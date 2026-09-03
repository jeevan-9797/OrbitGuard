import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


# ==========================================
# LOAD API KEY
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found.")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class Hypothesis(BaseModel):
    cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]


class Diagnosis(BaseModel):
    primary_hypothesis: Hypothesis
    hypotheses: list[Hypothesis]
    needs_evidence: bool


# ==========================================
# DIAGNOSIS PROMPT
# ==========================================

SYSTEM_INSTRUCTIONS = """
You are the OrbitGuard satellite anomaly diagnosis agent.

Your job is to diagnose the likely cause of a detected satellite anomaly.

STRICT RULES:

1. Use ONLY the telemetry, trends, deviations, power balance,
   and events supplied in the incident context.

2. NEVER invent telemetry values.

3. Every diagnosis must be supported by evidence from the
   supplied incident context.

4. Confidence must be between 0 and 1.

5. If the evidence is insufficient or ambiguous, set
   needs_evidence to true and use a lower confidence.

6. Return structured data matching the requested schema.

7. Do not recommend recovery actions.
   Your job is ONLY diagnosis.
"""


# ==========================================
# LOAD CONTEXT
# ==========================================

def load_context(file_name):

    with open(file_name, "r") as file:
        return json.load(file)


# ==========================================
# RUN DIAGNOSIS
# ==========================================

def diagnose(context):

    prompt = f"""
{SYSTEM_INSTRUCTIONS}

Here is the incident context:

{json.dumps(context, indent=2)}

Analyze the incident and determine the most likely cause.

Return:
- primary_hypothesis
- hypotheses
- needs_evidence

Evidence must directly correspond to information present
in the incident context.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": Diagnosis,
        },
    )

    return Diagnosis.model_validate_json(response.text)


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage:")
        print(
            "python -m ai_ml.diagnosis.diagnosis_agent "
            "<context_file>"
        )

        sys.exit(1)

    context_file = sys.argv[1]

    try:
        context = load_context(context_file)

        diagnosis = diagnose(context)

        print("\n================================")
        print("       ORBITGUARD DIAGNOSIS")
        print("================================\n")

        print(
            json.dumps(
                diagnosis.model_dump(),
                indent=2
            )
        )

    except Exception as error:

        print(f"\nERROR: Diagnosis failed.")
        print(f"Details: {error}")
        sys.exit(1)