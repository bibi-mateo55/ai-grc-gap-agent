"""Assessment store with validation guardrails and an audit trail.

Every judgement the agent makes goes through `AssessmentStore.record()`.
Anything that cannot be traced back to real controls, evidence or risks is
rejected, and the agent is told why so it can correct itself."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .catalog import Catalog

STATUSES = ("implemented", "partially_implemented", "not_implemented", "not_applicable")
LEVELS = ("high", "medium", "low")
SCORE = {"implemented": 1.0, "partially_implemented": 0.5, "not_implemented": 0.0}


class AssessmentStore:
    def __init__(self, catalog: Catalog, audit_path: Path | None = None):
        self.catalog = catalog
        self.assessments: dict[str, dict] = {}
        self.rejections = 0
        self.audit_path = audit_path
        if audit_path:
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit_path.write_text("", encoding="utf-8")

    # ---- audit trail ---------------------------------------------------
    def audit(self, tool: str, args: dict, outcome: str, detail: str = "") -> None:
        if not self.audit_path:
            return
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tool": tool,
            "args": args,
            "outcome": outcome,
            "detail": detail,
        }
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---- validation ----------------------------------------------------
    def validate(self, a: dict) -> list[str]:
        problems: list[str] = []
        cid = a.get("control_id", "")
        status = a.get("status", "")
        evidence = a.get("evidence_ids") or []
        risks = a.get("related_risks") or []

        if cid not in self.catalog.control_ids:
            problems.append(f"control_id '{cid}' does not exist in {self.catalog.framework}. Use list_controls.")
        if status not in STATUSES:
            problems.append(f"status must be one of {STATUSES}.")
        if a.get("confidence") not in LEVELS:
            problems.append(f"confidence must be one of {LEVELS}.")
        unknown_ev = [e for e in evidence if e not in self.catalog.evidence_ids]
        if unknown_ev:
            problems.append(f"evidence_ids {unknown_ev} do not exist. Only cite IDs returned by search_evidence.")
        unknown_rk = [r for r in risks if r not in self.catalog.risk_ids]
        if unknown_rk:
            problems.append(f"related_risks {unknown_rk} do not exist. Use get_risks.")
        if status in ("implemented", "partially_implemented") and not evidence:
            problems.append("A control cannot be (partially) implemented without citing supporting evidence.")
        if not (a.get("rationale") or "").strip():
            problems.append("rationale is required: explain how the evidence supports the status.")
        if status in ("partially_implemented", "not_implemented"):
            if not (a.get("gap") or "").strip():
                problems.append("gap is required for partially/not implemented controls.")
            if not (a.get("recommendation") or "").strip():
                problems.append("recommendation is required for partially/not implemented controls.")
            if a.get("priority") not in LEVELS:
                problems.append(f"priority must be one of {LEVELS} for partially/not implemented controls.")
        return problems

    def record(self, a: dict) -> tuple[bool, str]:
        problems = self.validate(a)
        if problems:
            self.rejections += 1
            return False, "REJECTED:\n- " + "\n- ".join(problems)
        a = dict(a)
        a["evidence_ids"] = list(a.get("evidence_ids") or [])
        a["related_risks"] = list(a.get("related_risks") or [])
        a["needs_human_review"] = a["confidence"] != "high" or a["status"] == "not_applicable"
        replaced = a["control_id"] in self.assessments
        self.assessments[a["control_id"]] = a
        verb = "Updated" if replaced else "Recorded"
        return True, f"{verb} assessment for {a['control_id']} ({a['status']}). {len(self.remaining())} control(s) remaining."

    # ---- progress & scoring ---------------------------------------------
    def remaining(self) -> list[str]:
        return [c for c in self.catalog.control_ids if c not in self.assessments]

    def ordered(self) -> list[dict]:
        order = {cid: i for i, cid in enumerate(self.catalog.control_ids)}
        return sorted(self.assessments.values(), key=lambda a: order[a["control_id"]])

    def counts(self) -> dict[str, int]:
        c = {s: 0 for s in STATUSES}
        for a in self.assessments.values():
            c[a["status"]] += 1
        return c

    def compliance_score(self) -> float | None:
        scored = [SCORE[a["status"]] for a in self.assessments.values() if a["status"] in SCORE]
        return round(100 * sum(scored) / len(scored), 1) if scored else None
