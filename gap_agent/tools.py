"""Custom tools exposed to the agent through an in-process MCP server.

The agent has NO access to the shell, the file system or the internet:
these six tools are the only actions it can take (least privilege)."""

from __future__ import annotations

import json
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from .store import LEVELS, STATUSES, AssessmentStore

SERVER_NAME = "grc"


def _ok(payload: Any) -> dict:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": text}]}


def _err(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


RECORD_SCHEMA = {
    "type": "object",
    "properties": {
        "control_id": {"type": "string", "description": "ID exactly as returned by list_controls"},
        "status": {"type": "string", "enum": list(STATUSES)},
        "evidence_ids": {"type": "array", "items": {"type": "string"},
                         "description": "IDs (E-xx) of the evidence supporting this judgement"},
        "rationale": {"type": "string", "description": "How the cited evidence supports the status"},
        "gap": {"type": "string", "description": "What is missing versus the requirement"},
        "recommendation": {"type": "string", "description": "Concrete, actionable remediation step"},
        "priority": {"type": "string", "enum": list(LEVELS)},
        "confidence": {"type": "string", "enum": list(LEVELS),
                       "description": "high only if the evidence is direct and unambiguous"},
        "related_risks": {"type": "array", "items": {"type": "string"},
                          "description": "Risk IDs (R-xx) from get_risks that this gap relates to"},
    },
    "required": ["control_id", "status", "evidence_ids", "rationale", "confidence"],
}


def build_tools(store: AssessmentStore) -> list:
    cat = store.catalog

    @tool("list_controls", f"List every {cat.framework} control/requirement that must be assessed.",
          {"type": "object", "properties": {}})
    async def list_controls(args: dict) -> dict:
        store.audit("list_controls", args, "ok")
        return _ok({"framework": cat.framework_name, "controls": cat.controls})

    @tool("list_evidence_areas", "List the evidence areas available for the organisation, with item counts.",
          {"type": "object", "properties": {}})
    async def list_evidence_areas(args: dict) -> dict:
        store.audit("list_evidence_areas", args, "ok")
        return _ok({"organisation": cat.organisation, "description": cat.organisation_description,
                    "areas": cat.evidence_areas()})

    @tool("search_evidence",
          "Keyword search over the organisation's evidence (interviews, configs, documents). "
          "Optionally filter by area. Returns evidence items with their IDs.",
          {"type": "object",
           "properties": {"query": {"type": "string"},
                          "area": {"type": "string", "description": "Optional area filter"}},
           "required": ["query"]})
    async def search_evidence(args: dict) -> dict:
        hits = cat.search_evidence(args["query"], args.get("area"))
        store.audit("search_evidence", args, "ok", f"{len(hits)} hit(s): {[h['id'] for h in hits]}")
        if not hits:
            return _ok("No evidence found for this query. Try other keywords or an area filter. "
                       "If nothing exists, absence of evidence must be reflected in the assessment.")
        return _ok(hits)

    @tool("get_risks", "List the organisation's risk register (IDs and titles) to link gaps to risks.",
          {"type": "object", "properties": {}})
    async def get_risks(args: dict) -> dict:
        store.audit("get_risks", args, "ok")
        return _ok(cat.risks)

    @tool("record_assessment",
          "Record your assessment of ONE control. It is validated: unknown controls, evidence or "
          "risk IDs, or missing fields are rejected with an explanation. Fix and call again.",
          RECORD_SCHEMA)
    async def record_assessment(args: dict) -> dict:
        ok, msg = store.record(args)
        store.audit("record_assessment", args, "ok" if ok else "rejected", msg)
        return _ok(msg) if ok else _err(msg)

    @tool("get_progress", "Show how many controls are assessed and which ones are still missing.",
          {"type": "object", "properties": {}})
    async def get_progress(args: dict) -> dict:
        rem = store.remaining()
        store.audit("get_progress", args, "ok", f"{len(rem)} remaining")
        return _ok({"assessed": len(store.assessments), "total": len(cat.controls), "remaining": rem})

    return [list_controls, list_evidence_areas, search_evidence, get_risks, record_assessment, get_progress]


def build_server(store: AssessmentStore):
    tools = build_tools(store)
    server = create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=tools)
    names = [f"mcp__{SERVER_NAME}__{t.name}" for t in tools]
    return server, names, tools
