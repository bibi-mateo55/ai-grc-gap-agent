"""Turns the validated assessments into a Markdown report and an Excel workbook."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .store import AssessmentStore

LABEL = {
    "implemented": "✅ Implemented",
    "partially_implemented": "🟡 Partial",
    "not_implemented": "❌ Not implemented",
    "not_applicable": "➖ N/A",
}
FILL = {
    "implemented": "C6EFCE",
    "partially_implemented": "FFEB9C",
    "not_implemented": "FFC7CE",
    "not_applicable": "E7E6E6",
}
PRIO_ORDER = {"high": 0, "medium": 1, "low": 2}


def _cell(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _gaps(store: AssessmentStore) -> list[dict]:
    gaps = [a for a in store.ordered() if a["status"] in ("not_implemented", "partially_implemented")]
    return sorted(gaps, key=lambda a: (PRIO_ORDER.get(a.get("priority"), 3),
                                       0 if a["status"] == "not_implemented" else 1))


def write_markdown(store: AssessmentStore, path: Path, run: dict) -> None:
    cat = store.catalog
    c = store.counts()
    score = store.compliance_score()
    gaps = _gaps(store)
    review = [a for a in store.ordered() if a["needs_human_review"]]
    missing = store.remaining()

    L: list[str] = []
    L.append(f"# Gap analysis — {cat.organisation} vs {cat.framework}")
    L.append("")
    L.append(f"> ⚠️ **AI-assisted draft. Every finding must be validated by a qualified analyst before use.** "
             f"{run.get('provenance', '')}")
    L.append("")
    L.append(f"**Framework:** {cat.framework_name}  ")
    L.append(f"**Organisation:** {cat.organisation_description}  ")
    L.append(f"**Run:** {run.get('date', '')} · mode: `{run.get('mode', '')}`"
             + (f" · model: `{run['model']}`" if run.get("model") else "")
             + (f" · cost: ${run['cost_usd']:.2f}" if run.get("cost_usd") is not None else "")
             + (f" · turns: {run['turns']}" if run.get("turns") else ""))
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append("| Metric | Value |")
    L.append("|---|---|")
    L.append(f"| Controls assessed | {len(store.assessments)} / {len(cat.controls)} |")
    for s, n in c.items():
        L.append(f"| {LABEL[s]} | {n} |")
    L.append(f"| **Compliance score** (implemented = 1, partial = 0.5) | **{score}%** |"
             if score is not None else "| Compliance score | n/a |")
    L.append(f"| Findings flagged for human review | {len(review)} |")
    L.append(f"| Assessments rejected by guardrails during the run | {store.rejections} |")
    L.append("")
    if missing:
        L.append(f"> ❗ **Coverage check failed:** {len(missing)} control(s) were not assessed: "
                 f"{', '.join(missing)}. The report is incomplete.")
    else:
        L.append("> ✅ **Coverage check passed:** every control in scope was assessed.")
    L.append("")
    if run.get("summary"):
        L.append(f"## {run.get('summary_label', 'Executive summary')}")
        L.append("")
        L.append(run["summary"].strip())
        L.append("")
    L.append("## Prioritised gaps")
    L.append("")
    L.append("| Priority | Control | Status | Gap | Recommendation | Related risks |")
    L.append("|---|---|---|---|---|---|")
    for a in gaps:
        ctl = cat.control(a["control_id"])
        L.append(f"| {a.get('priority', '').upper()} | **{a['control_id']}** {_cell(ctl['title'])} | "
                 f"{LABEL[a['status']]} | {_cell(a.get('gap', ''))} | {_cell(a.get('recommendation', ''))} | "
                 f"{', '.join(a['related_risks']) or '—'} |")
    L.append("")
    L.append("## Full assessment")
    L.append("")
    L.append("| Control | Status | Evidence | Rationale | Confidence |")
    L.append("|---|---|---|---|---|")
    for a in store.ordered():
        ctl = cat.control(a["control_id"])
        flag = " 🔍" if a["needs_human_review"] else ""
        L.append(f"| **{a['control_id']}** {_cell(ctl['title'])} | {LABEL[a['status']]} | "
                 f"{', '.join(a['evidence_ids']) or '—'} | {_cell(a['rationale'])} | {a['confidence']}{flag} |")
    L.append("")
    L.append("🔍 = flagged for human review (confidence below *high*, or marked not applicable).")
    L.append("")
    L.append("## Evidence referenced")
    L.append("")
    used = sorted({e for a in store.assessments.values() for e in a["evidence_ids"]})
    for eid in used:
        e = cat.evidence_item(eid)
        L.append(f"- **{eid}** ({e['source']}): {e['statement']}")
    L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def write_excel(store: AssessmentStore, path: Path, run: dict) -> None:
    cat = store.catalog
    wb = Workbook()
    F = lambda **k: Font(name="Arial", **k)  # noqa: E731
    head = PatternFill("solid", fgColor="1F3864")
    thin = Side(style="thin", color="BFBFBF")
    B = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    ws = wb.active
    ws.title = "Gap analysis"
    ws["A1"] = f"Gap analysis — {cat.organisation} vs {cat.framework}"
    ws["A1"].font = F(bold=True, size=14)
    ws["A2"] = "AI-assisted draft — every finding must be validated by a qualified analyst. " + run.get("provenance", "")
    ws["A2"].font = F(italic=True, size=9, color="C00000")
    cols = ["Control", "Title", "Status", "Priority", "Confidence", "Human review", "Evidence",
            "Rationale", "Gap", "Recommendation", "Related risks"]
    for i, h in enumerate(cols, 1):
        x = ws.cell(4, i, h)
        x.font, x.fill, x.border, x.alignment = F(bold=True, color="FFFFFF"), head, B, wrap
    for r, a in enumerate(store.ordered(), 5):
        ctl = cat.control(a["control_id"])
        vals = [a["control_id"], ctl["title"], a["status"].replace("_", " "), a.get("priority", ""),
                a["confidence"], "Yes" if a["needs_human_review"] else "No", ", ".join(a["evidence_ids"]),
                a["rationale"], a.get("gap", ""), a.get("recommendation", ""), ", ".join(a["related_risks"])]
        for i, v in enumerate(vals, 1):
            x = ws.cell(r, i, v)
            x.font, x.border, x.alignment = F(), B, wrap
        ws.cell(r, 3).fill = PatternFill("solid", fgColor=FILL[a["status"]])
    for i, w in enumerate([10, 30, 16, 10, 11, 10, 14, 45, 40, 45, 14], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "C5"
    last = 4 + len(store.assessments)
    ws.auto_filter.ref = f"A4:K{last}"

    s = wb.create_sheet("Summary")
    s["A1"] = "Summary"
    s["A1"].font = F(bold=True, size=14)
    rows = [("Status", "Count")] + [(k.replace("_", " "), None) for k in ("implemented", "partially_implemented",
                                                                          "not_implemented", "not_applicable")]
    for i, (k, _) in enumerate(rows, 3):
        s.cell(i, 1, k).font = F(bold=(i == 3))
        if i == 3:
            s.cell(i, 2, "Count").font = F(bold=True)
        else:
            s.cell(i, 2, f'=COUNTIF(\'Gap analysis\'!C5:C{last},A{i})').font = F()
    s["A9"], s["B9"] = "Compliance score", "=IFERROR((B4+0.5*B5)/(B4+B5+B6),0)"
    s["A9"].font, s["B9"].font = F(bold=True), F(bold=True)
    s["B9"].number_format = "0.0%"
    s["A10"] = "Score = (implemented + 0.5 × partial) / assessed controls excluding N/A"
    s["A10"].font = F(italic=True, size=9)
    s["A12"], s["B12"] = "Run mode", run.get("mode", "")
    s["A13"], s["B13"] = "Model", run.get("model") or "—"
    s["A14"], s["B14"] = "Cost (USD)", run.get("cost_usd") if run.get("cost_usd") is not None else "—"
    s["A15"], s["B15"] = "Guardrail rejections", store.rejections
    for r in range(12, 16):
        s.cell(r, 1).font, s.cell(r, 2).font = F(bold=True), F()
    s.column_dimensions["A"].width = 30
    s.column_dimensions["B"].width = 22

    ev = wb.create_sheet("Evidence")
    for i, h in enumerate(["ID", "Area", "Source", "Statement"], 1):
        x = ev.cell(1, i, h)
        x.font, x.fill, x.border = F(bold=True, color="FFFFFF"), head, B
    for r, e in enumerate(cat.evidence, 2):
        for i, k in enumerate(["id", "area", "source", "statement"], 1):
            x = ev.cell(r, i, e[k])
            x.font, x.border, x.alignment = F(), B, wrap
    for i, w in enumerate([8, 14, 28, 90], 1):
        ev.column_dimensions[get_column_letter(i)].width = w

    wb.save(path)
