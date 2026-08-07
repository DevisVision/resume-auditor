from __future__ import annotations
import json
import os
from typing import Optional
from openai import OpenAI


def _client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key or key.startswith("sk-your"):
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to your .env file.")
    return OpenAI(api_key=key)


def _model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


ORG_RUBRIC = """
ORG-SPECIFIC RESUME STANDARDS (for Azure Data Engineer candidates):
- Professional summary must highlight: Azure Data Engineer role, years of experience,
  and core skills (ADF, SQL, Python, PySpark, Databricks).
- Skillset section must align with Azure Data Engineering skillset.
- Work experience: each role must have Company-Role-Period; current role should mention
  "Azure Data Engineer"; Roles & Responsibilities should have AT LEAST 10 bullet points
  with keywords (ADF, SQL, Python, PySpark, Databricks, Synapse, ADLS, etc.) highlighted.
- Education: only highest qualification kept.
- Mandatory Certifications:
  • DP-900
  • DP-700
  • Databricks Associate

- Additional certifications like Databricks Fundamentals or
  Databricks GenAI Fundamentals are optional.

- If any mandatory certification is missing,
  mention it explicitly in recommendations and section compliance.
"""

SINGLE_AUDIT_SYSTEM = f"""You are a senior technical recruiter and resume auditor for an
Azure Data Engineering practice. Evaluate resumes against optional job descriptions and
the org's specific resume standards. Produce strictly structured JSON. Be objective and
evidence-based. Never invent facts. {ORG_RUBRIC}"""


SINGLE_AUDIT_SCHEMA_HINT = """
Return a JSON object with EXACTLY this shape:
{
  "candidate_name": string,
  "headline": string,
  "overall_score": int,
  "ats_score": int,
  "quality_score": int,
  "jd_match_score": int,
  "experience_score": int,
  "org_standard_score": int,
  "total_experience_years": number,
  "seniority_fit": string,
  "skills": {
    "matched":    [string],
    "missing":    [string],
    "additional": [string]
  },
  "section_compliance": [
    { "section": "Professional Summary",
      "passed": bool,
      "note": "...keyword highlight check, mentions years + Azure DE..." },
    { "section": "Skillset",                  "passed": bool, "note": "..." },
    { "section": "Work Experience Structure", "passed": bool, "note": "Company-Role-Period present" },
    { "section": "Current Role = Azure DE",   "passed": bool, "note": "..." },
    { "section": "Min 10 R&R bullets",        "passed": bool, "note": "..." },
    { "section": "Education (highest only)",  "passed": bool, "note": "..." },
    {"section": "Mandatory Certifications", "passed": bool,"note": "Mention whether DP-900, DP-700 and Databricks Associate are all present. List missing certifications if any."}
  ],
  "red_flags":   [string],
  "strengths":   [string],
  "weaknesses":  [string],
  "recommendations": [string],
  "verdict": string
}
All score keys must be integers 0..100. No prose outside the JSON.
"""


def audit_resume(resume_text: str, jd_text: Optional[str] = None) -> dict:
    client = _client()
    jd_block = f"\n\nJOB DESCRIPTION:\n{jd_text.strip()}" if jd_text else "\n\n(No job description provided — evaluate generally.)"
    user_prompt = f"RESUME:\n{resume_text.strip()[:18000]}{jd_block}\n\n{SINGLE_AUDIT_SCHEMA_HINT}"
    resp = client.chat.completions.create(
        model=_model(),
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=[
            {"role": "system", "content": SINGLE_AUDIT_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )
    return _safe_load(resp.choices[0].message.content or "{}")


COMPARE_SYSTEM = """
You are a senior Azure Data Engineering recruiter.

Compare candidates using:

- Professional Summary
- Azure Data Engineering Skills
- Experience
- ATS Quality
- Resume Quality
- DP-900
- DP-700
- Databricks Associate
- ADE Project minimum 10 responsibilities
- Highest qualification should include CGPA

Candidates missing mandatory certifications should receive lower scores.

Return ONLY the JSON requested.
"""

COMPARE_SCHEMA_HINT = """
Return a JSON object with EXACTLY this structure.

{
  "ranking":[
    {
      "rank":1,
      "candidate_name":"",
      "overall_score":0,
      "jd_match_score":0,
      "experience_score":0,
      "quality_score":0,
      "key_strengths":[],
      "key_gaps":[],
      "verdict":""
    }
  ],

  "winner":"",

  "why_winner":"",

  "comparison_summary":""
}

Rules:

overall_score = integer (0-100)

jd_match_score = integer (0-100)

experience_score = integer (0-100)

quality_score = integer (0-100)

rank starts from 1.

Return ONLY JSON.
"""


def compare_resumes(resumes: list, jd_text: Optional[str] = None) -> dict:
    client = _client()
    blocks = []
    for i, r in enumerate(resumes, 1):
        blocks.append(f"=== CANDIDATE {i}: {r['name']} ===\n{r['text'].strip()[:9000]}")
    joined = "\n\n".join(blocks)
    jd_block = f"\n\nJOB DESCRIPTION:\n{jd_text.strip()}" if jd_text else "\n\n(No job description — compare generally.)"
    user_prompt = f"{joined}{jd_block}\n\n{COMPARE_SCHEMA_HINT}"
    resp = client.chat.completions.create(
        model=_model(),
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=[
            {"role": "system", "content": COMPARE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )
    return _safe_load(resp.choices[0].message.content or "{}")


def _safe_load(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
        raise