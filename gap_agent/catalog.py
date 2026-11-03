"""Loads the reference data the agent works with: control catalogues,
the organisation's evidence and its risk register."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FRAMEWORK_FILES = {
    "nis2": "controls_nis2.json",
    "iso27001": "controls_iso27001.json",
}


@dataclass
class Catalog:
    framework: str
    framework_name: str
    controls: list[dict]
    organisation: str
    organisation_description: str
    evidence: list[dict]
    risks: list[dict]

    # ---- lookups -------------------------------------------------------
    @property
    def control_ids(self) -> list[str]:
        return [c["id"] for c in self.controls]

    @property
    def evidence_ids(self) -> set[str]:
        return {e["id"] for e in self.evidence}

    @property
    def risk_ids(self) -> set[str]:
        return {r["id"] for r in self.risks}

    def control(self, control_id: str) -> dict | None:
        return next((c for c in self.controls if c["id"] == control_id), None)

    def evidence_item(self, evidence_id: str) -> dict | None:
        return next((e for e in self.evidence if e["id"] == evidence_id), None)

    def evidence_areas(self) -> dict[str, int]:
        areas: dict[str, int] = {}
        for e in self.evidence:
            areas[e["area"]] = areas.get(e["area"], 0) + 1
        return dict(sorted(areas.items()))

    def search_evidence(self, query: str, area: str | None = None, limit: int = 8) -> list[dict]:
        """Simple keyword search. Deliberately transparent (no embeddings) so
        every result can be explained to an auditor."""
        terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2]
        scored = []
        for e in self.evidence:
            if area and e["area"] != area.lower():
                continue
            text = f'{e["area"]} {e["statement"]} {e["source"]}'.lower()
            score = sum(text.count(t) for t in terms)
            if area and not terms:
                score = 1
            if score:
                scored.append((score, e))
        scored.sort(key=lambda x: (-x[0], x[1]["id"]))
        return [e for _, e in scored[:limit]]


def load_catalog(framework: str) -> Catalog:
    framework = framework.lower()
    if framework not in FRAMEWORK_FILES:
        raise ValueError(f"Unknown framework '{framework}'. Choose from: {', '.join(FRAMEWORK_FILES)}")
    fw = json.loads((DATA_DIR / FRAMEWORK_FILES[framework]).read_text(encoding="utf-8"))
    ev = json.loads((DATA_DIR / "cloudnova_evidence.json").read_text(encoding="utf-8"))
    rk = json.loads((DATA_DIR / "cloudnova_risks.json").read_text(encoding="utf-8"))
    return Catalog(
        framework=fw["framework"],
        framework_name=fw["full_name"],
        controls=fw["controls"],
        organisation=ev["organisation"],
        organisation_description=ev["description"],
        evidence=ev["evidence"],
        risks=rk["risks"],
    )
