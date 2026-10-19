import json
from pathlib import Path

import strategies


TEST_IDS = [
    "Q-03",
    "Q-08",
    "Q-09",
    "Q-12",
    "Q-15"
]


with open(
    "data/questions.json",
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)

questions = data["questions"] if isinstance(data, dict) else data


def count_calls(log_path):
    with open(log_path, "r", encoding="utf-8") as file:
        log = json.load(file)

    return sum(
        len(round_data["tool_calls"])
        for round_data in log["rounds"]
    )


original_description = (
    strategies.TOOLS[0]["function"]["description"]
)

strategies.TOOLS[0]["function"]["description"] = "Looks things up."


for qid in TEST_IDS:

    question = next(
        q for q in questions
        if q["id"] == qid
    )

    normal_log = Path(
        f"outputs/run2/tools/{qid}_tools.json"
    )

    normal_calls = count_calls(normal_log)

    with open(
        normal_log,
        "r",
        encoding="utf-8"
    ) as file:
        normal_data = json.load(file)

    normal_answer = normal_data["answer"]

    vague_result = strategies.tool_strategy(
        question["question"],
        qid,
        output_dir="outputs/vague"
    )

    vague_log = Path(
        f"outputs/vague/{qid}_tools.json"
    )

    vague_calls = count_calls(vague_log)

    print("=" * 70)
    print(qid)
    print("Normal calls:", normal_calls)
    print("Vague calls:", vague_calls)
    print("Normal answer:", normal_answer)
    print("Vague answer:", vague_result["answer"])


strategies.TOOLS[0]["function"]["description"] = (
    original_description
)