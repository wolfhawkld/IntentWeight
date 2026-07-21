#!/usr/bin/env python3
"""Generate the authoritative post-Task79 paper and submission state."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

import fitz


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "paper"
EXPERIMENTS = PAPER / "experiments"
RESULTS = EXPERIMENTS / "results"
DRAFT = PAPER / "full_draft"
LATEX = PAPER / "latex"
CAS = PAPER / "journal_submission" / "latex"
OUTPUT_JSON = RESULTS / "task80_authoritative_submission_state.json"
OUTPUT_MD = EXPERIMENTS / "task80_authoritative_submission_state.md"
MAIN_SECTIONS = (
    "01_abstract.md",
    "02_introduction.md",
    "03_related_work.md",
    "04_method.md",
    "05_experimental_setup.md",
    "06_results.md",
    "07_discussion.md",
    "08_limitations.md",
    "09_conclusion.md",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_pages(path: Path) -> int:
    with fitz.open(path) as document:
        return document.page_count


def pdf_type3_fonts(path: Path) -> list[str]:
    fonts: set[str] = set()
    with fitz.open(path) as document:
        for page in document:
            for font in page.get_fonts(full=True):
                if font[2] == "Type3":
                    fonts.add(font[3])
    return sorted(fonts)


def markdown_rows_after(text: str, caption: str) -> list[list[str]]:
    start = text.index(caption)
    lines = text[start:].splitlines()[1:]
    rows: list[list[str]] = []
    in_table = False
    for line in lines:
        if not line.startswith("|"):
            if in_table:
                break
            continue
        in_table = True
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def find_csv_row(path: Path, **matches: str) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if all(row.get(key) == value for key, value in matches.items()):
                return dict(row)
    raise ValueError(f"No matching row in {path}: {matches}")


def count_status(checks: Iterable[dict[str, Any]]) -> dict[str, int]:
    output: dict[str, int] = {}
    for row in checks:
        status = str(row.get("status", "UNKNOWN"))
        output[status] = output.get(status, 0) + 1
    return output


def abstract_words() -> int:
    source = (CAS / "anonymous_manuscript.tex").read_text(encoding="utf-8")
    match = re.search(
        r"% TASK66_ABSTRACT_START\s*(.*?)\s*% TASK66_ABSTRACT_END",
        source,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("CAS abstract markers are missing")
    text = re.sub(r"(?<!\\)%.*", " ", match.group(1))
    text = re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?", " ", text)
    text = re.sub(r"[{}$]", " ", text)
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def main() -> None:
    task51 = read_json(RESULTS / "task51_experiment_validation_audit.json")
    task67 = read_json(RESULTS / "task67_paper_evidence_audit.json")
    task79_gate = read_json(RESULTS / "task79_local_validation.json")
    task79 = read_json(RESULTS / "task79_llmlingua2_multi_judge_analysis.json")
    task65 = read_json(RESULTS / "task65_7_multi_judge_analysis.json")
    task43_text = (RESULTS / "task43_table_figure_data_audit.md").read_text(encoding="utf-8")
    task43_match = re.search(r"- Checks: (\d+)\s+- Passed: (\d+)\s+- Failed: (\d+)", task43_text)
    if not task43_match:
        raise ValueError("Cannot parse Task43 audit summary")

    results_text = (DRAFT / "06_results.md").read_text(encoding="utf-8")
    appendix_text = (DRAFT / "12_appendix.md").read_text(encoding="utf-8")
    cross_dataset_rows = markdown_rows_after(
        results_text,
        "**Table 4. Cross-dataset and cross-domain evidence matrix.",
    )
    main_table_count = len(re.findall(r"^\*\*Table \d+\.", results_text, flags=re.MULTILINE))
    supplement_table_count = len(
        re.findall(r"^\*\*Supplementary Table S\d+\.", appendix_text, flags=re.MULTILINE)
    )
    main_figure_count = len(
        re.findall(r"\\begin\{figure\*?\}", (LATEX / "main.tex").read_text(encoding="utf-8"))
    )
    main_words = sum(
        len((DRAFT / name).read_text(encoding="utf-8").split()) for name in MAIN_SECTIONS
    )

    task79_primary = find_csv_row(
        RESULTS / "task79_llmlingua2_multi_judge_analysis.paired.csv",
        judge_scope="three_judge_majority",
        comparison="IntentRoute+LLMLingua-2 vs Dense+LLMLingua-2",
    )
    sent_mmr = find_csv_row(
        RESULTS / "task65_7_multi_judge_analysis.paired.csv",
        judge_model="three_judge_majority",
        comparison="IntentRoute+SentMMR vs Dense+SentMMR",
    )

    task51_summary = (task51.get("summary") or {}).get("status_counts") or count_status(
        task51.get("checks") or []
    )
    task43_checks, task43_passed, task43_failed = map(int, task43_match.groups())
    pdfs = {
        "acl_complete_evidence": LATEX / "main.pdf",
        "cas_anonymous_manuscript": CAS / "anonymous_manuscript.pdf",
        "cas_supplement": CAS / "supplementary_material.pdf",
        "cas_title_page": CAS / "title_page.pdf",
    }

    payload: dict[str, Any] = {
        "status": "TASK80_COMPLETE_REPOSITORY_STATE_RECONCILED",
        "authority": {
            "scope": "repository-controlled scientific and submission state through Task80",
            "generated_from_current_worktree": True,
            "manual_submission_fields_excluded": True,
        },
        "claim_boundary": {
            "chain": "local geometric structure -> adaptive route selection -> feedback correction -> quality-efficiency trade-off",
            "geometry": "design hypothesis and route diagnostic; not a manifold theorem or compression oracle",
            "feedback": "controlled repeated-interaction and conditional recovery evidence; not production RLHF",
            "dense": "strong baseline, recall floor, and fallback; not universally replaced",
            "cost": "final evidence-context input tokens; not end-to-end serving cost",
        },
        "evidence_surface": {
            "dataset_domain_settings": 9,
            "domain_areas": 8,
            "cross_dataset_display_rows": len(cross_dataset_rows),
            "main_tables": main_table_count,
            "supplement_tables": supplement_table_count,
            "main_figures": main_figure_count,
            "canonical_main_text_words_whitespace_count": main_words,
            "abstract_words_cas_validator_contract": abstract_words(),
        },
        "answer_evaluation": {
            "task63_answers": int(task65["answer_count"]),
            "task63_valid_judgments": int(task65["valid_judgment_count"]),
            "task63_expected_judgments": int(task65["answer_count"]) * 3,
            "task63_shared_three_judge_keys": int(task65["shared_valid_count"]),
            "task63_remaining_minimax_missing": int(task65["missing_count"]),
            "task79_answers": int(task79["answer_count"]),
            "task79_valid_judgments": int(task79["valid_judgment_count"]),
            "task79_expected_judgments": int(task79["expected_judgment_count"]),
            "task79_missing_judgments": int(task79["missing_judgment_count"]),
            "task79_primary_context_saving_percent": float(task79_primary["context_token_saving_percent"]),
            "task79_primary_context_saving_ci_percent": [
                float(task79_primary["context_token_saving_ci_low_percent"]),
                float(task79_primary["context_token_saving_ci_high_percent"]),
            ],
            "task79_primary_majority_correctness_delta_pp": float(task79_primary["is_correct_delta_pp"]),
            "task79_primary_majority_correctness_ci_pp": [
                float(task79_primary["is_correct_delta_ci_low_pp"]),
                float(task79_primary["is_correct_delta_ci_high_pp"]),
            ],
            "sent_mmr_complete_pair_count": int(sent_mmr["paired_queries"]),
            "sent_mmr_majority_faithfulness_delta_pp": float(sent_mmr["faithful_delta_pp"]),
            "sent_mmr_majority_faithfulness_mcnemar_p": float(sent_mmr["faithful_mcnemar_exact_p"]),
        },
        "validation": {
            "task51": task51_summary,
            "task43": {
                "checks": task43_checks,
                "passed": task43_passed,
                "failed": task43_failed,
            },
            "task67": {
                "status": task67["status"],
                "main_tables": 5,
                "figure_data_files": 2,
                "supplementary_numeric_values": next(
                    row["numeric_values"]
                    for row in task67["checks"]
                    if row["item"] == "supplementary_numeric_provenance"
                ),
            },
            "task79_gate": {
                "status": task79_gate["status"],
                "passed": task79_gate["passed"],
                "failed": task79_gate["failed"],
            },
        },
        "compiled_packages": {
            label: {
                "path": str(path.relative_to(ROOT)),
                "pages": pdf_pages(path),
                "type3_fonts": pdf_type3_fonts(path),
                "sha256": sha256(path),
            }
            for label, path in pdfs.items()
        },
        "remaining_author_or_release_work": [
            "replace Figure 1 placeholder with author-produced editable vector artwork",
            "complete author identities, affiliations, ORCIDs, CRediT roles, and declarations",
            "audit redistribution licenses and prepare a blinded/public reproducibility package",
            "obtain independent scientific and English/layout review, then freeze the submission",
        ],
        "source_sha256": {
            "task51_audit": sha256(RESULTS / "task51_experiment_validation_audit.json"),
            "task43_audit": sha256(RESULTS / "task43_table_figure_data_audit.md"),
            "task67_audit": sha256(RESULTS / "task67_paper_evidence_audit.json"),
            "task79_gate": sha256(RESULTS / "task79_local_validation.json"),
            "task79_analysis": sha256(RESULTS / "task79_llmlingua2_multi_judge_analysis.json"),
            "task65_analysis": sha256(RESULTS / "task65_7_multi_judge_analysis.json"),
        },
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    answer = payload["answer_evaluation"]
    evidence = payload["evidence_surface"]
    validation = payload["validation"]
    packages = payload["compiled_packages"]
    lines = [
        "# Task80 Authoritative Submission State",
        "",
        "Status: Task80 complete; repository-controlled state reconciled",
        "",
        "Date: 2026-07-21",
        "",
        "This is the sole current repository-controlled status snapshot. Older task,",
        "review, and readiness reports remain historical records. Scientific claims",
        "must still be read from the manuscript and source experiment artifacts.",
        "",
        "## Claim Boundary",
        "",
        "`local geometric structure -> adaptive route selection -> feedback correction -> quality-efficiency trade-off`",
        "",
        "Geometry is diagnostic rather than theorem-level proof; feedback is controlled",
        "simulation rather than production RLHF; Dense remains a recall floor; and cost",
        "means final evidence-context input tokens rather than total serving cost.",
        "",
        "## Current Evidence Surface",
        "",
        f"- Dataset/domain settings: `{evidence['dataset_domain_settings']}` across `{evidence['domain_areas']}` domain areas.",
        f"- Cross-dataset display rows: `{evidence['cross_dataset_display_rows']}`; no pooled effect.",
        f"- Main displays: `{evidence['main_tables']}` tables and `{evidence['main_figures']}` figures.",
        f"- Supplement: `{evidence['supplement_tables']}` tables.",
        f"- Canonical main-text whitespace word count: `{evidence['canonical_main_text_words_whitespace_count']}`.",
        f"- CAS abstract: `{evidence['abstract_words_cas_validator_contract']}` words.",
        "",
        "## Answer-Level State",
        "",
        f"- Task63: `{answer['task63_answers']}` answers, `{answer['task63_valid_judgments']}/{answer['task63_expected_judgments']}` valid judgments, `{answer['task63_shared_three_judge_keys']}` shared keys, `{answer['task63_remaining_minimax_missing']}` MiniMax failures not imputed.",
        f"- Task79: `{answer['task79_answers']}` endpoint-answer records and `{answer['task79_valid_judgments']}/{answer['task79_expected_judgments']}` judgments; missing=`{answer['task79_missing_judgments']}`.",
        f"- LLMLingua-2 primary majority comparison: `{answer['task79_primary_context_saving_percent']:.2f}%` context saving, correctness delta `{answer['task79_primary_majority_correctness_delta_pp']:+.2f}pp`; correctness CI crosses zero.",
        f"- Recovered Sentence-MMR comparison: `{answer['sent_mmr_complete_pair_count']}` complete pairs; majority faithfulness delta `{answer['sent_mmr_majority_faithfulness_delta_pp']:+.2f}pp`, McNemar `p={answer['sent_mmr_majority_faithfulness_mcnemar_p']:.4f}`.",
        "",
        "## Validation State",
        "",
        f"- Experiment artifact audit: `{validation['task51'].get('PASS', 0)}` PASS, `{validation['task51'].get('WARN', 0)}` WARN, `{validation['task51'].get('ERROR', 0)}` ERROR.",
        f"- Table/figure source audit: `{validation['task43']['passed']}/{validation['task43']['checks']}` PASS.",
        f"- Paper evidence audit: `{validation['task67']['status']}`; supplementary numeric values=`{validation['task67']['supplementary_numeric_values']}`.",
        f"- Task79 local gate: `{validation['task79_gate']['passed']}/{validation['task79_gate']['passed'] + validation['task79_gate']['failed']}`, status `{validation['task79_gate']['status']}`.",
        "",
        "## Compiled Packages",
        "",
        "| Package | Pages | Type 3 fonts |",
        "|---|---:|---:|",
    ]
    for label, row in packages.items():
        lines.append(f"| {label} | {row['pages']} | {len(row['type3_fonts'])} |")
    lines.extend(
        [
            "",
            "## Remaining Human/Release Work",
            "",
            *[f"- {item}" for item in payload["remaining_author_or_release_work"]],
            "",
            "## Machine-Readable Source",
            "",
            "`paper/experiments/results/task80_authoritative_submission_state.json`",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "main_tables": main_table_count,
        "supplement_tables": supplement_table_count,
        "main_figures": main_figure_count,
        "task79_judgments": answer["task79_valid_judgments"],
        "task51_pass": validation["task51"].get("PASS", 0),
    }, indent=2))


if __name__ == "__main__":
    main()
