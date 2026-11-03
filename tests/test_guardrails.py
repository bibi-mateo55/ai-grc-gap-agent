"""Offline tests (no API key needed). Run with: python -m pytest -q"""

import json

import anyio
import pytest

from gap_agent.agent import run_offline_demo
from gap_agent.catalog import load_catalog
from gap_agent.store import AssessmentStore
from gap_agent.tools import build_server

VALID = {
    "control_id": "NIS2-21b", "status": "not_implemented", "evidence_ids": ["E-16"],
    "rationale": "No incident plan.", "gap": "No plan.", "recommendation": "Write one.",
    "priority": "high", "confidence": "high", "related_risks": ["R-04"],
}


@pytest.fixture
def store():
    return AssessmentStore(load_catalog("nis2"))


def test_valid_assessment_is_recorded(store):
    ok, _ = store.record(VALID)
    assert ok and "NIS2-21b" in store.assessments


@pytest.mark.parametrize("change, expected", [
    ({"control_id": "NIS2-99"}, "does not exist"),                  # hallucinated control
    ({"evidence_ids": ["E-99"]}, "do not exist"),                   # hallucinated evidence
    ({"related_risks": ["R-42"]}, "do not exist"),                  # hallucinated risk
    ({"status": "implemented", "evidence_ids": []}, "without citing"),  # claim without evidence
    ({"recommendation": ""}, "recommendation is required"),
    ({"confidence": "certain"}, "confidence must be"),
])
def test_guardrails_reject_bad_input(store, change, expected):
    ok, msg = store.record({**VALID, **change})
    assert not ok and expected in msg
    assert store.rejections == 1 and not store.assessments


def test_low_confidence_is_flagged_for_review(store):
    store.record({**VALID, "confidence": "medium"})
    assert store.assessments["NIS2-21b"]["needs_human_review"] is True


def test_tool_returns_is_error_on_rejection(store):
    _, _, tools = build_server(store)
    record = next(t for t in tools if t.name == "record_assessment")
    res = anyio.run(record.handler, {**VALID, "evidence_ids": ["E-99"]})
    assert res["is_error"] is True


def test_search_evidence_finds_mfa(store):
    ids = [e["id"] for e in store.catalog.search_evidence("MFA root account")]
    assert "E-05" in ids


def test_sample_covers_every_control_and_passes_guardrails(tmp_path):
    assert anyio.run(run_offline_demo, "nis2", tmp_path) == 0
    log = [json.loads(l) for l in (tmp_path / "audit_log_nis2.jsonl").read_text().splitlines()]
    assert all(e["outcome"] == "ok" for e in log)
    report = (tmp_path / "gap_analysis_nis2.md").read_text()
    assert "Coverage check passed" in report
    assert (tmp_path / "gap_analysis_nis2.xlsx").exists()
