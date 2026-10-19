import json
import re
import statistics
from pathlib import Path

from strategies import (
    direct_strategy,
    vote_strategy,
    tool_strategy
)


QUESTIONS_PATH = Path("data/questions.json")
OUTPUTS_DIR = Path("outputs")


def load_questions():
    with open(
        QUESTIONS_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    if isinstance(data, dict):
        return data["questions"]

    return data


def parse_answer(text):

    if not text:
        return None

    match = re.search(
        r"ANSWER:\s*(.*?)\s*\|\s*([-+]?[0-9][0-9,]*(?:\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    name = match.group(1).strip()

    number_text = (
        match.group(2)
        .replace(",", "")
    )

    try:
        number = float(number_text)
    except ValueError:
        return None

    return {
        "name": name,
        "number": number
    }


def is_correct(model_answer, question):
    parsed = parse_answer(model_answer)

    if parsed is None:
        return False

    expected_name = str(
        question["answer"]
    ).strip()

    expected_value = float(
        question["value"]
    )

    decimals = int(
        question["decimals"]
    )

    name_correct = (
        parsed["name"].lower()
        == expected_name.lower()
    )

    expected_rounded = round(
        expected_value,
        decimals
    )

    actual_rounded = round(
        parsed["number"],
        decimals
    )

    tolerance = 10 ** (-decimals)

    number_correct = (
        abs(
            actual_rounded
            - expected_rounded
        )
        <= tolerance
    )

    return (
        name_correct
        and number_correct
    )


def make_result(
    run_number,
    question,
    strategy_name,
    strategy_result
):
    answer = strategy_result["answer"]

    return {
        "run": run_number,
        "question_id": question["id"],
        "question": question["question"],

        "strategy": strategy_name,

        "answer": answer,

        "expected_name": question["answer"],
        "expected_value": question["value"],

        "parsed_answer": parse_answer(answer),

        "correct": is_correct(
            answer,
            question
        ),

        "unanswered": strategy_result.get(
            "unanswered",
            False
        ),

        "input_tokens": strategy_result.get(
            "input_tokens",
            0
        ),

        "output_tokens": strategy_result.get(
            "output_tokens",
            0
        ),

        "seconds": strategy_result.get(
            "seconds",
            0
        )
    }


def save_results(results, run_number):
    OUTPUTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        OUTPUTS_DIR
        / f"run{run_number}_results.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\nSaved results to: {file_path}"
    )


def run_one_question(
    question,
    run_number
):
    qid = question["id"]
    question_text = question["question"]

    print("\n" + "=" * 80)
    print(
        f"RUN {run_number} | {qid}"
    )
    print(question_text)

    question_results = []


    print("\nS1 direct...")

    try:
        s1 = direct_strategy(
            question_text
        )

    except Exception as error:
        print(
            "S1 ERROR:",
            error
        )

        s1 = {
            "answer": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "seconds": 0,
            "unanswered": True
        }

    result_s1 = make_result(
        run_number,
        question,
        "S1",
        s1
    )

    question_results.append(
        result_s1
    )

    print(
        "S1:",
        "✓"
        if result_s1["correct"]
        else "✗"
    )

    print(
        "Answer:",
        result_s1["answer"]
    )


    print("\nS2 think and vote...")

    try:
        s2 = vote_strategy(
            question_text,
            k=5
        )

    except Exception as error:
        print(
            "S2 ERROR:",
            error
        )

        s2 = {
            "answer": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "seconds": 0,
            "unanswered": True
        }

    result_s2 = make_result(
        run_number,
        question,
        "S2",
        s2
    )

    question_results.append(
        result_s2
    )

    print(
        "S2:",
        "✓"
        if result_s2["correct"]
        else "✗"
    )

    print(
        "Answer:",
        result_s2["answer"]
    )


    print("\nS3 tools...")

    try:
        s3 = tool_strategy(
            question_text,
            qid,
            output_dir=(
                f"outputs/run{run_number}/tools"
            )
        )

    except Exception as error:
        print(
            "S3 ERROR:",
            error
        )

        s3 = {
            "answer": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "seconds": 0,
            "unanswered": True
        }

    result_s3 = make_result(
        run_number,
        question,
        "S3",
        s3
    )

    question_results.append(
        result_s3
    )

    print(
        "S3:",
        "✓"
        if result_s3["correct"]
        else "✗"
    )

    print(
        "Answer:",
        result_s3["answer"]
    )

    return question_results


def run_all(run_number):
    questions = load_questions()

    all_results = []

    print("\n" + "#" * 80)
    print(
        f"STARTING FULL RUN {run_number}"
    )
    print("#" * 80)

    for question in questions:

        question_results = run_one_question(
            question,
            run_number
        )

        all_results.extend(
            question_results
        )

        # Save after every question
        # so results are not lost
        save_results(
            all_results,
            run_number
        )

    return all_results


def get_strategy_results(
    results,
    strategy
):
    return [
        result
        for result in results
        if result["strategy"] == strategy
    ]


def print_summary(
    results,
    run_number
):
    print("\n")
    print("=" * 90)
    print(
        f"RUN {run_number} SUMMARY"
    )
    print("=" * 90)

    for strategy in [
        "S1",
        "S2",
        "S3"
    ]:

        items = get_strategy_results(
            results,
            strategy
        )

        correct = sum(
            1
            for item in items
            if item["correct"]
        )

        unanswered = sum(
            1
            for item in items
            if item["unanswered"]
        )

        input_tokens = sum(
            item["input_tokens"]
            for item in items
        )

        output_tokens = sum(
            item["output_tokens"]
            for item in items
        )

        times = [
            item["seconds"]
            for item in items
        ]

        if times:
            median_seconds = (
                statistics.median(
                    times
                )
            )

            total_seconds = sum(
                times
            )

        else:
            median_seconds = 0
            total_seconds = 0

        print(
            f"\nStrategy: {strategy}"
        )

        print(
            f"Correct: {correct}/20"
        )

        print(
            f"Unanswered: {unanswered}"
        )

        print(
            f"Input tokens: {input_tokens}"
        )

        print(
            f"Output tokens: {output_tokens}"
        )

        print(
            "Median seconds per question:",
            round(
                median_seconds,
                2
            )
        )

        print(
            "Total seconds:",
            round(
                total_seconds,
                2
            )
        )


def print_per_question(results):
    print("\n")
    print(
        "PER QUESTION TABLE"
    )

    print(
        "| Question | S1 | S2 | S3 |"
    )

    print(
        "|---|:---:|:---:|:---:|"
    )

    for number in range(
        1,
        21
    ):

        qid = f"Q-{number:02d}"

        cells = []

        for strategy in [
            "S1",
            "S2",
            "S3"
        ]:

            item = next(
                (
                    result
                    for result in results
                    if result["question_id"] == qid
                    and result["strategy"] == strategy
                ),
                None
            )

            if item is None:
                cells.append("?")

            elif item["correct"]:
                cells.append("✓")

            else:
                cells.append("✗")

        print(
            f"| {qid} | "
            f"{cells[0]} | "
            f"{cells[1]} | "
            f"{cells[2]} |"
        )


if __name__ == "__main__":


    # results1 = run_all(
    #     run_number=1
    # )
    #
    # print_summary(
    #     results1,
    #     run_number=1
    # )
    #
    # print_per_question(
    #     results1
    # )


    results2 = run_all(
        run_number=2
    )

    print_summary(
        results2,
        run_number=2
    )