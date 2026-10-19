# HW4 — submission

**AI assistance:** using only ChatGPT for understanding and debugging 

---

## Part A — Plan on paper (Easy)

> Commit this whole part before any `.py` file exists.

### A1 — The steps

| # | Step                    | What goes in (types)               | What comes out (types)                                                     | When it goes wrong                                                                                                                                                        | Tool, loop, or model?  |
|---|-------------------------|------------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|
| 1 | Understand the question | question: str                      | district_1: str, district_2: str, needed_fields: list[str], operation: str | The question is unclear, a district name is missing, or the operation isn't clear. The model should not guess                                                             | Model                  |
| 2 | Find facts              | district: str, field: str          | value: float, unit: str, source: str                                       | Nothing is found, the district name is misspelled or ambiguous, the profile is archived, or a correction must be used. The tool returns a clear error or corrected result | lookup tool            |
| 3 | Normalize units         | value: float, unit: str            | normalized_value: float, normalized_unit: str                              | The unit is unknown or cannot be converted. The system should return an error instead of guessing                                                                         | Model + calculate tool |
| 4 | Calculate density       | population: float, area: float     | density: float                                                             | A number cannot be read or the area is zero. The calculator returns an error                                                                                              | calculate tool         |
| 5 | Compare and answer      | density_1: float, density_2: float | answer: str                                                                | One of the earlier values is missing or invalid. The model shouldn't create an answer from incomplete data                                                                | Model                  |

**How the steps connect:**
 
Question -> Model understand the task -> lookup gets the required facts -> Values are converted to the same units if needed -> calculate performs the arithmetic -> Model compares the result -> Final answer 

**What I am assuming:**

- Using the current 2025 data.
- Archived profiles aren't used.
- If a later correction exists, I use the corrected value.
- Values must use compatible units before calculation.
- I don't guess unknown units.
- I keep full precision during calculations and round only the final answer.
- If a district name is ambiguous, the tool returns an error instead of choosing one automatically.


### A2 — The two tools

#### `lookup`

```json

{
  "type": "function",
  "function": {
    "name": "lookup",
    "description": "Find a current fact about a district. Use this tool to get values such as population, area, water use, or other district facts. Return the value, unit, and source document.",
    "parameters": {
      "type": "object",
      "properties": {
        "district": {
          "type": "string",
          "description": "The district name."
        },
        "field": {
          "type": "string",
          "description": "The fact to find, for example population, area, or water use."
        }
      },
      "required": ["district", "field"]
    }
  }
}
```

| Case                      | What the tool returns                                                                                              |
|---------------------------|--------------------------------------------------------------------------------------------------------------------|
| success                   | {"value": 48317, "unit": "people", "source": "NR-XX"}                                                              |
| district not found        | {"error": "district not found"}                                                                                    |
| similar or ambiguous name | {"error": "district name is ambiguous", "suggestions": ["...", "..."]}                                             |
| field not found           | {"error": "field not found for this district"}                                                                     |
| archived profile found    | The tool ignores the archived profile and uses the current one. If no current profile exists, it returns an error. |
| correction exists         | The tool returns the corrected value and the correction source.                                                    |
| unknown unit              | {"error": "unknown unit"}                                                                                          |

**Worst thing it could do with strange or dangerous input:**
The tool only reads local data. Strange input could cause no result or an error, but it shouldn't execute commands, modify files, or access the internet.

#### `calculate`

```json

{
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "Safely calculate a mathematical expression using numbers and basic arithmetic operators. Using for division, multiplication, addition, subtraction, and other allowed calculations. Don't use it to run Python code.",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "A mathematical expression, for example '48317 / 921.4'."
        }
      },
      "required": ["expression"]
    }
  }
}
```

| Case                  | What the tool returns               |
|-----------------------|-------------------------------------|
| success               | { "result": 52.44}                  |
| invalid expression    | {"error": "invalid expression"}     |
| division by zero      | {"error": "division by zero"}       |
| dangerous Python code | {"error": "unsupported expression"} |
| unsupported operator  | {"error": "operator not allowed"}   |
| number is too large   | {"error": "number is too large"}    |

**Worst thing it could do with strange or dangerous input:**
The calculator must not use eval or exec. It only accepts numbers and allowed arithmetic operators. Dangerous Python expressions must be rejected before they run.

### A3 — Q-09 by hand

```json

[
    {
    "role": "user",
    "content": "Which district has the higher population density in 2025, Brightwater or Millbrook, and by how many residents per square kilometre?"
  },
  {
    "tool_call": {
      "id": "call_1",
      "name": "lookup",
      "arguments": {
        "district": "Brightwater",
        "field": "population"
      }
    }
  },
  {
    "tool_call": {
      "id": "call_2",
      "name": "lookup",
      "arguments": {
        "district": "Brightwater",
        "field": "area"
      }
    }
  },
  {
    "tool_call": {
      "id": "call_3",
      "name": "lookup",
      "arguments": {
        "district": "Millbrook",
        "field": "population"
      }
    }
  },
  {
    "tool_call": {
      "id": "call_4",
      "name": "lookup",
      "arguments": {
        "district": "Millbrook",
        "field": "area"
      }
    }
  }
]
```

**My arithmetic:**

Brightwater:
44,675 / 921.4 = 48.49 residents/km²

Millbrook:
37,203 / 758.6 = 49.04 residents/km²

Difference:
49.04 - 48.49 ≈ 0.56 residents/km²

Millbrook has the higher population density by about 0.56 residents per square kilometre.

### A4 — Why I split it this way


Another option would be to create one large tool called answer_question that reads the documents, finds the facts, performs the calculation, and returns the final answer.
I didn't choose this design because it would be harder to test and understand. With two small tools, lookup is responsible only for finding correct facts and calculate is responsible only for safe arithmetic. 
The model connects these steps and creates the final answer. This makes errors easier to find and the tools easier to reuse. 


---

## Part B — Build it and run it (Medium)

### What I changed from Part A while coding
 
I made a small change to lookup. Instead of returning only one number, it returns a small set of relevant sentences with their source document ids. This makes corrections easier to handle because the model can see both the original fact and the later correction notice

### B2 — Tests

```text

collected 12 items                                                                                                                                 

tests/test_tools.py::test_calculate_multiplication PASSED                                                                                    [  8%]
tests/test_tools.py::test_calculate_division PASSED                                                                                          [ 16%]
tests/test_tools.py::test_calculate_import_attack PASSED                                                                                     [ 25%]
tests/test_tools.py::test_calculate_class_attack PASSED                                                                                      [ 33%]
tests/test_tools.py::test_calculate_huge_power PASSED                                                                                        [ 41%]
tests/test_tools.py::test_calculate_division_by_zero PASSED                                                                                  [ 50%]
tests/test_tools.py::test_lookup_current_population PASSED                                                                                   [ 58%]
tests/test_tools.py::test_lookup_ignores_archived_profile PASSED                                                                             [ 66%]
tests/test_tools.py::test_lookup_uses_brightwater_correction PASSED                                                                          [ 75%]
tests/test_tools.py::test_lookup_similar_names_are_separate PASSED                                                                           [ 83%]
tests/test_tools.py::test_lookup_misspelled_name PASSED                                                                                      [ 91%]
tests/test_tools.py::test_lookup_lindenmoor_water_unit PASSED                                                                                [100%]

=============================================================== 12 passed in 0.07s ================================================================

```

### B3 — The loop

- Round limit, and why: 8 rounds. This is enough for several lookup and calculation steps, but it also prevents an infinite tool-calling loop if something goes wrong.
  - Where the logs are:  The tool logs are saved as JSON files in outputs/run1/tools/ and outputs/run2/tools/. Each log contains tool calls, arguments, results, execution time, token usage and number of rounds.
  - Real Q-09 conversation compared with my A3 version, what is different: 
In my start version, I expected separate lookup and calculation steps. In the real run, the model requested several facts in the same round and then used the calculator in later rounds. It needed 4 rounds in total.

### B4 — Three strategies

**What I kept the same:**

I used gpt-5.6-luna for all three strategies and the same 20 questions.
S1 and S2 received the same complete corpus and the same answer instructions. S2 used k = 5. S3 did not receive the corpus directly and could only access facts through the lookup and calculate tools.
All strategies were expected to finish with the same answer format:

ANSWER: <name or yes/no> | <number>

I used the same correctness checker for all three strategies.

**My rule for a correct answer** (written before the first full run):

The name or yes/no part must match the reference answer. The numeric value must match the reference value rounded to the number of decimal places specified in questions.json. I allow a difference of one unit in the last required decimal place

| Run | Strategy                  | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) |
|-----|---------------------------|------------:|-----------:|-------------:|--------------:|----------------------------:|--------------:|---------:|
| 1   | S1 direct                 |        2/20 |          0 |       44 660 |           410 |                        1.28 |         29.74 |   0.0094 |
| 1   | S2 think and vote (k = 5) |       11/20 |          0 |      224 200 |         8 023 |                        8.62 |        179.64 |   0.0545 |
| 1   | S3 tools                  |       13/20 |          2 |       74 019 |         4 524 |                        5.99 |        128.84 |   0.0202 |
| 2   | S1 direct                 |        4/20 |          0 |       44 660 |           468 |                        1.52 |         37.62 |   0.0095 |
| 2   | S2 think and vote (k = 5) |       11/20 |          0 |      224 200 |         7 602 |                       11.89 |       1431.71 |   0.0540 |
| 2   | S3 tools                  |       17/20 |          2 |       77 398 |         4 651 |                        6.62 |        157.25 |   0.0211 |

Cost calculation: 
input tokens prices - $0.20 per 1 million
output tokens prices - $1.20 per 1 million

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|----------|:--:|:--:|:--:|
| Q-01     | ✗  | ✗  | ✓  |
| Q-02     | ✗  | ✗  | ✗  |
| Q-03     | ✗  | ✓  | ✓  |
| Q-04     | ✗  | ✓  | ✓  |
| Q-05     | ✗  | ✗  | ✓  |
| Q-06     | ✗  | ✓  | ✗  |
| Q-07     | ✗  | ✓  | ✗  |
| Q-08     | ✗  | ✓  | ✗  |
| Q-09     | ✗  | ✓  | ✓  |
| Q-10     | ✓  | ✓  | ✓  |
| Q-11     | ✗  | ✓  | ✓  |
| Q-12     | ✗  | ✗  | ✓  |
| Q-13     | ✗  | ✗  | ✓  |
| Q-14     | ✗  | ✗  | ✗  |
| Q-15     | ✗  | ✗  | ✓  |
| Q-16     | ✓  | ✓  | ✓  |
| Q-17     | ✗  | ✗  | ✗  |
| Q-18     | ✗  | ✓  | ✓  |
| Q-19     | ✗  | ✓  | ✓  |
| Q-20     | ✗  | ✗  | ✗  |

---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

| Question | Calls (your description) | Calls (vague) | Answer (yours) | Answer (vague)              |
|----------|-------------------------:|--------------:|----------------|-----------------------------|
| Q-03     |                        7 |             9 | correct        | correct                     |
| Q-08     |                       26 |            19 | unanswered     | wrong                       |
| Q-09     |                        7 |             9 | correct        | correct                     |
| Q-12     |                        6 |             9 | correct        | correct value, wrong format |
| Q-15     |                        7 |             9 | correct        | correct                     |

A clear tool description usually helped the model use fewer calls and follow the task better.
This shows that the tool description matters because it helps the model understand when and how to use the tool.

### C2 — Three mistakes explained

S1 — Q-15
S1 answered Q-15 incorrectly. It had the documents, but it made an arithmetic mistake when calculating pupils per school. 
This shows that giving the model all documents doesn't guarantee correct arithmetic.

S2 — Q-09, Run 2
S2 answered: Brightwater | 1.37
the correct answer was: Millbrook | 0.6
Voting didn't fix the mistake because several model attempts can make similar reasoning mistakes. Voting helps with random mistakes, but not when the same mistake appears many times.

S3 — Q-08
S3 didn't answer Q-08 and reached the round limit. The question needs several steps: water use, unit conversion, tariff and comparison
The loop stopped after 8 rounds, so the question was marked unanswered. This shows that tool use can be accurate, but complex questions may require many calls
The calculator helps because Python performs the arithmetic instead of the language model. Each S3 round also becomes more expensive because previous messages, tool calls and tool results remain in the conversation.

### C3 — Which strategy I would use, and what would change it

I would use S3 — tools.

It had the best accuracy in my experiments.
S3 used more time than S1, but much fewer tokens than S2. It was also better for calculations because it used the calculate tool
I wouldn't choose S1 because its accuracy was low. I wouldn't choose S2 because it used about five times more input tokens and was still less accurate than S3
If I had a very small budget or strict time limit, I would choose S1 because it's the fastest and cheapest
If there were 1,000 times more documents, I would still use a tool-based strategy, but I would replace the simple lookup with a search or retrieval system.
If the questions were very simple and had no arithmetic, S1 could be enough.

### C4 — How sure I can be

The two runs were quite different.
S1 changed from 2/20 to 4/20. S2 stayed at 11/20. S3 changed from 13/20 to 17/20.
This means the results have some randomness, especially for S1 and S3.
S3 was still the best strategy in both runs, so I have some confidence that it's the best choice. However, 20 questions is a small test set

### Final questions

1. When the model sends a tool_calls message, what has actually run so far?
Nothing from my Python tool has run yet. The model has only requested a tool call. My loop reads the request and then runs the real function

2. Why does arguments arrive as a string, and what goes wrong if you pass it straight into your function?
The API sends tool arguments as JSON text. I first use json.loads() to convert the string into a Python dictionary. If I pass the string directly, the function cannot correctly access fields such as district or field

3. How many tokens do your two tool definitions add to every S3 request? Measure it.
Tool definition tokens: 262
These tokens are added to every S3 API request because the model needs the tool definitions to know which tools are available

4. How much more did S2 cost than S1?
In Run 1, S2 cost about $0.045 more than S1. In Run 2, it was also about $0.045 more
This is because S2 calls the model five times for each question and sends the complete corpus every time

5. Which question needed the most rounds in S3, and why?
Q-08 and Q-17 reached the 8-round limit and were unanswered.
Both questions require several steps, including looking up water use, populations or tariffs, converting units and doing several calculations

6. What would you change in lookup if there were 100,000 documents?
I wouldn't scan every document one by one. I would use an indexed search system or a vector database to find only the most relevant documents

7. What stops your calculate from running dangerous code? Could the model still make it misbehave?
Function calculate uses Python ast and only allows numbers and selected arithmetic operators. It doesn't use eval or exec
The model can still send invalid or very large expressions, so the tool also checks unsupported operations and large values.

8. For which kind of question did tools help most, and for which did they not help at all?
Tools helped most with questions that needed several calculations, unit conversions or corrected values. For example, S3 correctly solved Q-15 using the calculator.
Tools helped less on very simple questions such as Q-10, where all three strategies could answer correctly without complicated calculations.
