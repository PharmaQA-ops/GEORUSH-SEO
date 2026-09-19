"""GEORUSH AI Agent powered by Google Gemini Interactions API.

The agent receives GEORUSH evidence through local function tools and returns
structured SEO recommendations. The Gemini API key is read only from the
server environment.
"""

import json
import os
from typing import Any

try:
    from google import genai
except Exception:  # pragma: no cover - handled at runtime
    genai = None

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    }


def tool_definitions() -> list[dict]:
    return [
        _tool(
            "get_crawl_summary",
            "Get the current GEORUSH technical crawl summary, SEO score, page count, issue counts and representative affected URLs.",
            {"include_pages": {"type": "boolean", "description": "Whether to include page-level evidence."}},
        ),
        _tool(
            "get_keyword_opportunities",
            "Get the currently loaded GEORUSH keyword opportunity data, including query, impressions, CTR, position and opportunity score.",
            {"limit": {"type": "integer", "description": "Maximum number of keyword rows to return."}},
        ),
        _tool(
            "get_competitor_analysis",
            "Get automatically discovered GEORUSH competitor analysis and target-vs-competitor signal gaps.",
            {"limit": {"type": "integer", "description": "Maximum number of competitors to return."}},
        ),
        _tool(
            "get_radar_summary",
            "Get Cloudflare Radar / URL Scanner signals already collected for the target website.",
            {},
        ),
    ]


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "overall_priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                    "area": {"type": "string"},
                    "finding": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "why": {"type": "string"},
                    "evidence": {"type": "string"},
                    "affected_urls": {"type": "array", "items": {"type": "string"}},
                    "implementation": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "priority", "area", "finding", "recommendation", "why",
                    "evidence", "affected_urls", "implementation",
                ],
            },
        },
        "action_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timeframe": {"type": "string"},
                    "actions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["timeframe", "actions"],
            },
        },
        "data_gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["executive_summary", "overall_priority", "recommendations", "action_plan", "data_gaps"],
}


class GeminiAgentError(RuntimeError):
    pass


def _execute_tool(name: str, arguments: dict, context: dict) -> dict:
    if name == "get_crawl_summary":
        crawl = context.get("crawl") or {}
        results = crawl.get("results") or []
        issue_counts: dict[str, int] = {}
        for page in results:
            for issue in page.get("issues") or []:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        payload = {
            "url": crawl.get("url") or context.get("target"),
            "seo_score": (crawl.get("seo_score") or {}).get("total"),
            "pages": len(results),
            "issues": sum(issue_counts.values()),
            "issue_counts": dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)),
        }
        if arguments.get("include_pages", True):
            payload["pages_detail"] = [
                {
                    "url": p.get("url"),
                    "status": p.get("status_code"),
                    "title": p.get("title"),
                    "words": p.get("word_count", 0),
                    "h1_count": p.get("h1_count", 0),
                    "issues": p.get("issues") or [],
                }
                for p in results[:100]
            ]
        return payload

    if name == "get_keyword_opportunities":
        rows = context.get("keywords") or []
        limit = max(1, min(int(arguments.get("limit", 25)), 100))
        return {"count": len(rows), "keywords": rows[:limit]}

    if name == "get_competitor_analysis":
        competitors = context.get("competitors") or []
        limit = max(1, min(int(arguments.get("limit", 5)), 10))
        return {
            "target": (context.get("competitor_analysis") or {}).get("target"),
            "top_competitor": (context.get("competitor_analysis") or {}).get("top_competitor"),
            "competitors": competitors[:limit],
        }

    if name == "get_radar_summary":
        return context.get("radar") or {"available": False}

    return {"error": f"Unknown tool: {name}"}


def _initial_prompt(context: dict) -> str:
    target = context.get("target") or "unknown website"
    return f"""You are GEORUSH AI, an evidence-driven SEO analyst for {target}.

Analyze the website using GEORUSH's tools. You MUST base findings on returned evidence. Do not invent rankings, traffic, backlinks, conversions, search volume, Google penalties, or business impact that the supplied data does not establish.

Your job is to produce practical recommendations for an SEO/marketing team. Prioritize issues by severity, breadth, and dependency: crawlability/indexation first, then metadata/on-page structure, content, internal linking, keyword opportunities, competitor gaps, and supplementary security/performance signals.

For every important recommendation, explain the observed finding, why it matters, the evidence, affected URLs when available, and concrete implementation steps. Clearly mark missing data as a data gap.

Use the tool data first. Do not treat the GEORUSH signal score as a Google ranking score. Competitor signal scores are comparative GEORUSH diagnostic scores, not search-engine rankings.

Return the final result strictly in the requested JSON schema.

Target: {target}
"""


def _extract_output(interaction: Any) -> str:
    text = getattr(interaction, "output_text", None)
    if text:
        return text
    for step in reversed(getattr(interaction, "steps", []) or []):
        content = getattr(step, "content", None)
        if content:
            for part in reversed(content):
                value = getattr(part, "text", None)
                if value:
                    return value
    raise GeminiAgentError("Gemini returned no final output.")


def run_agent(context: dict) -> dict:
    if genai is None:
        raise GeminiAgentError("google-genai is not installed. Run: pip install -r requirements.txt")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiAgentError("GEMINI_API_KEY is not configured on the GEORUSH API server.")

    client = genai.Client(api_key=api_key)
    tools = tool_definitions()
    response_format = {
        "type": "text",
        "mime_type": "application/json",
        "schema": OUTPUT_SCHEMA,
    }

    interaction = client.interactions.create(
        model=MODEL,
        input=_initial_prompt(context),
        tools=tools,
        response_format=response_format,
    )

    # Allow the agent to call multiple GEORUSH tools. A hard cap prevents loops.
    for _ in range(8):
        calls = [s for s in (getattr(interaction, "steps", []) or []) if getattr(s, "type", "") == "function_call"]
        if not calls:
            break

        results = []
        for call in calls:
            result = _execute_tool(call.name, call.arguments or {}, context)
            results.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [{"type": "text", "text": _json(result)}],
            })

        interaction = client.interactions.create(
            model=MODEL,
            previous_interaction_id=interaction.id,
            input=results,
            tools=tools,
            response_format=response_format,
        )

    raw = _extract_output(interaction)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        # A structured-output failure should be visible rather than silently
        # turning model prose into fake structured data.
        raise GeminiAgentError(f"Gemini returned invalid JSON: {exc}") from exc

    result["mode"] = "Google Gemini GEORUSH AI Agent"
    result["model"] = MODEL
    result["agent"] = "GEORUSH AI SEO Analyst"
    return result
