import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from collections import Counter

from tools import lookup, calculate

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = "gpt-5.6-luna"


def load_documents_text():
    documents = []

    with open(
        "data/corpus.jsonl",
        "r",
        encoding="utf-8"
    ) as file:
        for line in file:
            doc = json.loads(line)

            documents.append(
                f"[{doc['id']}] {doc['title']}\n"
                f"{doc['text']}"
            )

    return "\n\n".join(documents)


ALL_DOCUMENTS = load_documents_text()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": (
                "Find current facts about one district in the Nine Rivers Region. "
                "Use it for population, area, water use, budget, schools, pupils, "
                "or roads. Current 2025 profiles must be preferred over archived "
                "profiles. Correction notices take priority over the original value. "
                "The result includes source document IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {
                        "type": "string",
                        "description": "Exact district name, for example Brightwater."
                    },
                    "field": {
                        "type": "string",
                        "description": (
                            "Fact to find, for example population, area, "
                            "water use, budget, schools, pupils, or roads."
                        )
                    }
                },
                "required": ["district", "field"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Safely calculate an arithmetic expression using numbers and basic "
                "operators. Use this tool for arithmetic instead of calculating "
                "numbers yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "Arithmetic expression, for example '44675 / 921.4'."
                        )
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        }
    }
]

def run_tool(name, arguments):
    if name == "lookup":
        return lookup(
            arguments["district"],
            arguments["field"]
        )

    if name == "calculate":
        return calculate(
            arguments["expression"]
        )

    return {
        "error": f"unknown tool: {name}"
    }


S3_SYSTEM_PROMPT = """
You answer questions about the Nine Rivers Region.

You don't have the district documents directly.
Use the provided tools to find every fact you need.

Rules:
- Use current 2025 values.
- Ignore archived profiles.
- A correction notice takes priority over the original profile.
- Check units carefully.
- Use the calculate tool for arithmetic.
- Don't guess missing facts.
- Keep full precision during calculations and round only the final answer.
- On the final ANSWER line, write only the name and the number.
- Don't write units or extra words after the number.
- Your final response must end with exactly:

ANSWER: <name or yes/no> | <number>
""".strip()


DIRECT_SYSTEM_PROMPT = """
Use the provided Nine Rivers Region documents to answer the question.

Rules:
- Use the current 2025 information.
- Do not use archived profiles when a current profile exists.
- Use correction notices when they update a value.
- Check units before doing calculations.
- Keep full precision and round only the final value.
- The final line must contain only the answer name and numeric value.
- Do not write units or extra words after the number.
- End with exactly:

ANSWER: <name or yes/no> | <number>
""".strip()


def save_log(log, question_id, output_dir):
    path = Path(output_dir)

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = path / f"{question_id}_tools.json"

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            log,
            file,
            ensure_ascii=False,
            indent=2
        )


def tool_strategy(question, question_id, output_dir="outputs", round_limit=8):
    messages = [
        {
            "role": "system",
            "content": S3_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ]

    log = {
        "question_id": question_id,
        "question": question,
        "round_limit": round_limit,
        "rounds": [],
        "input_tokens": 0,
        "output_tokens": 0,
        "unanswered": False
    }

    start_total = time.perf_counter()

    for round_number in range(1, round_limit + 1):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            reasoning_effort="none"
        )

        if response.usage:
            log["input_tokens"] += response.usage.prompt_tokens
            log["output_tokens"] += response.usage.completion_tokens

        message = response.choices[0].message

        round_log = {
            "round": round_number,
            "tool_calls": []
        }

        messages.append(message)

        if not message.tool_calls:
            final_answer = message.content or ""

            round_log["final_answer"] = final_answer
            log["rounds"].append(round_log)

            log["answer"] = final_answer
            log["rounds_used"] = round_number
            log["total_seconds"] = time.perf_counter() - start_total

            save_log(
                log,
                question_id,
                output_dir
            )

            return {
                "answer": final_answer,
                "input_tokens": log["input_tokens"],
                "output_tokens": log["output_tokens"],
                "seconds": log["total_seconds"],
                "rounds": round_number,
                "unanswered": False
            }

        for tool_call in message.tool_calls:

            tool_start = time.perf_counter()

            name = tool_call.function.name
            raw_arguments = tool_call.function.arguments

            try:
                arguments = json.loads(raw_arguments)

                if not isinstance(arguments, dict):
                    raise ValueError(
                        "arguments must be a JSON object"
                    )

                result = run_tool(
                    name,
                    arguments
                )

            except json.JSONDecodeError:
                arguments = raw_arguments

                result = {
                    "error": "invalid JSON arguments"
                }

            except Exception as error:
                result = {
                    "error": str(error)
                }

            tool_seconds = (
                time.perf_counter()
                - tool_start
            )

            round_log["tool_calls"].append({
                "tool_call_id": tool_call.id,
                "name": name,
                "arguments": arguments,
                "result": result,
                "seconds": tool_seconds
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            })

        log["rounds"].append(round_log)

    log["unanswered"] = True
    log["answer"] = ""
    log["rounds_used"] = round_limit
    log["total_seconds"] = (
        time.perf_counter()
        - start_total
    )

    save_log(
        log,
        question_id,
        output_dir
    )

    return {
        "answer": "",
        "input_tokens": log["input_tokens"],
        "output_tokens": log["output_tokens"],
        "seconds": log["total_seconds"],
        "rounds": round_limit,
        "unanswered": True
    }


def direct_strategy(question):
    prompt = f"""
Here are the documents:

{ALL_DOCUMENTS}

Question:
{question}
""".strip()

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": DIRECT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        reasoning_effort="none"
    )

    seconds = time.perf_counter() - start

    return {
        "answer": response.choices[0].message.content or "",
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "seconds": seconds,
        "unanswered": False
    }


def extract_answer_line(text):
    for line in reversed(text.splitlines()):
        line = line.strip()

        if line.startswith("ANSWER:"):
            return line

    return None


def vote_strategy(question, k=5):
    prompt = f"""
DOCUMENTS

{ALL_DOCUMENTS}

QUESTION

{question}

Work through the problem carefully before giving the final answer.
""".strip()

    samples = []

    total_input_tokens = 0
    total_output_tokens = 0

    start = time.perf_counter()

    for _ in range(k):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": DIRECT_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            reasoning_effort="none",
            temperature=0.7
        )

        answer = (
            response.choices[0].message.content
            or ""
        )

        total_input_tokens += (
            response.usage.prompt_tokens
        )

        total_output_tokens += (
            response.usage.completion_tokens
        )

        answer_line = extract_answer_line(
            answer
        )

        samples.append({
            "full_answer": answer,
            "answer_line": answer_line
        })

    valid_lines = [
        sample["answer_line"]
        for sample in samples
        if sample["answer_line"] is not None
    ]

    if valid_lines:
        winner = Counter(
            valid_lines
        ).most_common(1)[0][0]

        unanswered = False
    else:
        winner = ""
        unanswered = True

    seconds = time.perf_counter() - start

    return {
        "answer": winner,
        "samples": samples,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "seconds": seconds,
        "unanswered": unanswered
    }


