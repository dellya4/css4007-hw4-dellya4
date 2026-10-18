# HW4 — submission

**AI assistance:** <!-- what you used, and for what. "None" is an answer too. -->

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

<!-- Question -> Model understand the task -> lookup gets the required facts -> Values are converted to the same units if needed -> calculate performs the arithmetic -> Model compares the result -> Final answer  -->



**What I am assuming:**

<!-- 

- Using the current 2025 data.
- Archived profiles aren't used.
- If a later correction exists, I use the corrected value.
- Values must use compatible units before calculation.
- I don't guess unknown units.
- I keep full precision during calculations and round only the final answer.
- If a district name is ambiguous, the tool returns an error instead of choosing one automatically.

-->

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

Brightwater population in 2025 = 44,675
The original profile gives the area as 912.4 km², but NR-16 says this is a mistake, the correct area is 921.4 km².

Brightwater population density:
44,675 / 921.4 = 48.486

Rounded result:
48.49 residents per square kilometre

### A4 — Why I split it this way

<!-- 

Another option would be to create one large tool called answer_question that reads the documents, finds the facts, performs the calculation, and returns the final answer.
I didn't choose this design because it would be harder to test and understand. With two small tools, lookup is responsible only for finding correct facts and calculate is responsible only for safe arithmetic. 
The model connects these steps and creates the final answer. This makes errors easier to find and the tools easier to reuse. 

-->

---

## Part B — Build it and run it (Medium)

### What I changed from Part A while coding

<!-- what changed in your plan, and why. "None" is an answer too. -->

### B2 — Tests

```text
<!-- pytest output -->
```

### B3 — The loop

- Round limit, and why:
- Where the logs are:
- Real Q-09 conversation compared with my A3 version, what is different:

### B4 — Three strategies

**What I kept the same:**

<!-- model, temperature, k, prompts, answer format, anything else -->

**My rule for a correct answer** (written before the first full run):

| Run | Strategy | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | S1 direct | | | | | | | |
| 1 | S2 think and vote (k = ) | | | | | | | |
| 1 | S3 tools | | | | | | | |
| 2 | S1 direct | | | | | | | |
| 2 | S2 think and vote (k = ) | | | | | | | |
| 2 | S3 tools | | | | | | | |

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | | | |
| Q-02 | | | |
| Q-03 | | | |
| Q-04 | | | |
| Q-05 | | | |
| Q-06 | | | |
| Q-07 | | | |
| Q-08 | | | |
| Q-09 | | | |
| Q-10 | | | |
| Q-11 | | | |
| Q-12 | | | |
| Q-13 | | | |
| Q-14 | | | |
| Q-15 | | | |
| Q-16 | | | |
| Q-17 | | | |
| Q-18 | | | |
| Q-19 | | | |
| Q-20 | | | |

---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

| Question | Calls (your description) | Calls (vague) | Answer (yours) | Answer (vague) |
|---|---:|---:|---|---|
| | | | | |

### C2 — Three mistakes explained

### C3 — Which strategy I would use, and what would change it

### C4 — How sure I can be

### Final questions

1.
2.
3.
4.
5.
6.
7.
8.
