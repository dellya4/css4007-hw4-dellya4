import ast
import json
import operator
from pathlib import Path
import re

DATA_PATH = Path("data/corpus.jsonl")


def load_corpus():
    documents = []

    with open(DATA_PATH, "r", encoding="utf-8") as file:
        for line in file:
            documents.append(json.loads(line))

    return documents


CORPUS = load_corpus()


DISTRICTS = [
    "Ossbridge",
    "Ossford",
    "Tarnvale",
    "Kelmarsh",
    "Brightwater",
    "Stonecairn",
    "Harrowfield",
    "Lindenmoor",
    "Redfen",
    "Ashgrove",
    "Millbrook",
    "Coldharbour",
]


FIELD_KEYWORDS = {
    "population": [
        "population",
        "census recorded",
        "census counted",
        "census population"
    ],

    "area": [
        "square kilometre",
        "square kilometres",
        "area"
    ],

    "water use": [
        "water",
        "megalitre",
        "megalitres",
        "cubic metre",
        "cubic metres"
    ],

    "budget": [
        "budget"
    ],

    "schools": [
        "school",
        "schools"
    ],

    "pupils": [
        "pupil",
        "pupils"
    ],

    "roads": [
        "road",
        "roads",
        "paved road"
    ]
}


def lookup(district, field):
    try:
        district = district.strip()
        field = field.strip().lower()

        if not district:
            return {"error": "district name is empty"}

        if not field:
            return {"error": "field is empty"}

        exact_matches = [
            name
            for name in DISTRICTS
            if name.lower() == district.lower()
        ]

        if not exact_matches:
            suggestions = [
                name
                for name in DISTRICTS
                if district.lower() in name.lower()
                or name.lower() in district.lower()
            ]

            if suggestions:
                return {
                    "error": f"district '{district}' not found exactly",
                    "suggestions": suggestions
                }

            return {
                "error": f"district '{district}' not found"
            }

        district_name = exact_matches[0]

        keywords = FIELD_KEYWORDS.get(
            field,
            [field]
        )

        current_docs = []
        archived_docs = []

        for doc in CORPUS:
            title_lower = doc["title"].lower()

            if district_name.lower() in title_lower:

                if "archived" in title_lower:
                    archived_docs.append(doc)

                elif "district profile" in title_lower:
                    current_docs.append(doc)

        if not current_docs:
            if archived_docs:
                return {
                    "error": f"only archived profile found for '{district_name}'"
                }

            return {
                "error": f"no current profile found for '{district_name}'"
            }

        relevant_sentences = []

        for doc in current_docs:
            sentences = re.split(r'(?<!\d)\.(?!\d)', doc["text"])

            for sentence in sentences:
                sentence_lower = sentence.lower()

                if any(
                    keyword in sentence_lower
                    for keyword in keywords
                ):
                    relevant_sentences.append({
                        "text": sentence.strip(),
                        "source": doc["id"]
                    })

        corrections = []

        for doc in CORPUS:
            if "correction" in doc["title"].lower():
                text_lower = doc["text"].lower()

                if (
                    district_name.lower() in text_lower
                    and any(
                        keyword in text_lower
                        for keyword in keywords
                    )
                ):
                    corrections.append({
                        "text": doc["text"],
                        "source": doc["id"]
                    })

        if not relevant_sentences and not corrections:
            return {
                "error": f"field '{field}' not found for '{district_name}'"
            }

        return {
            "district": district_name,
            "field": field,
            "matches": relevant_sentences,
            "corrections": corrections
        }

    except Exception as error:
        return {
            "error": str(error)
        }


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow
}


def evaluate_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("only numbers are allowed")

    if isinstance(node, ast.BinOp):
        operator_type = type(node.op)

        if operator_type not in ALLOWED_OPERATORS:
            raise ValueError("operator not allowed")

        left = evaluate_node(node.left)
        right = evaluate_node(node.right)

        if isinstance(node.op, ast.Pow):
            if abs(right) > 10:
                raise ValueError(
                    "exponent is too large"
                )

        return ALLOWED_OPERATORS[
            operator_type
        ](left, right)

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -evaluate_node(
                node.operand
            )

        if isinstance(node.op, ast.UAdd):
            return evaluate_node(
                node.operand
            )

    raise ValueError(
        "unsupported expression"
    )


def calculate(expression):
    try:
        tree = ast.parse(
            expression,
            mode="eval"
        )

        result = evaluate_node(tree.body)

        if abs(result) > 1e12:
            return {
                "error": "result is too large"
            }

        return {
            "result": result
        }

    except ZeroDivisionError:
        return {
            "error": "division by zero"
        }

    except Exception:
        return {
            "error": "unsupported expression"
        }