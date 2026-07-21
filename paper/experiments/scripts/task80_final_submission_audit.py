#!/usr/bin/env python3
"""Validate the reconciled post-Task79 paper and submission state."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import fitz


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "paper"
EXPERIMENTS = PAPER / "experiments"
RESULTS = EXPERIMENTS / "results"
OUTPUT_JSON = RESULTS / "task80_final_submission_audit.json"
OUTPUT_MD = RESULTS / "task80_final_submission_audit.md"

CURRENT_STATUS_FILES = (
    EXPERIMENTS / "task80_authoritative_submission_state.md",
    EXPERIMENTS / "task80_remaining_work_checklist.md",
    EXPERIMENTS / "task80_status_reconciliation.md",
    EXPERIMENTS / "task_paper_use_status.md",
    PAPER / "journal_submission" / "README.md",
    PAPER / "journal_submission" / "submission_checklist.md",
    PAPER / "full_draft" / "README.md",
)

HISTORICAL_STATUS_FILES = (
    ROOT / "docs" / "pre_submission_comprehensive_audit_20260716.md",
    ROOT / "docs" / "publication-readiness-and-figure-plan.md",
    EXPERIMENTS / "phase5_submission_integration_audit.md",
    EXPERIMENTS / "post_task69_submission_readiness_plan.md",
    EXPERIMENTS / "task57_review_response_action_map.md",
    EXPERIMENTS / "task67_review_response_map.md",
    EXPERIMENTS / "task69_remaining_dataset_todo.md",
    PAPER / "journal_submission" / "task67_submission_readiness_report.md",
)

MAIN_CHAPTERS = tuple(
    PAPER / "full_draft" / name
    for name in (
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
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pdf_type3_count(path: Path) -> int:
    found: set[str] = set()
    with fitz.open(path) as document:
        for page in document:
            for font in page.get_fonts(full=True):
                if font[2] == "Type3":
                    found.add(font[3])
    return len(found)


def main() -> None:
    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })

    state = load_json(RESULTS / "task80_authoritative_submission_state.json")
    check(
        "authoritative_state_final",
        state.get("status") == "TASK80_COMPLETE_REPOSITORY_STATE_RECONCILED",
        str(state.get("status")),
    )

    answer = state["answer_evaluation"]
    check(
        "task79_judgment_coverage",
        answer["task79_valid_judgments"] == answer["task79_expected_judgments"]
        and answer["task79_missing_judgments"] == 0,
        f"{answer['task79_valid_judgments']}/{answer['task79_expected_judgments']}; missing={answer['task79_missing_judgments']}",
    )
    check(
        "task63_missingness_disclosed",
        answer["task63_valid_judgments"] == 6272
        and answer["task63_expected_judgments"] == 6300
        and answer["task63_remaining_minimax_missing"] == 28,
        f"{answer['task63_valid_judgments']}/{answer['task63_expected_judgments']}; missing={answer['task63_remaining_minimax_missing']}",
    )

    validation = state["validation"]
    check(
        "experiment_artifact_audit",
        validation["task51"].get("PASS") == 921
        and validation["task51"].get("WARN", 0) == 0
        and validation["task51"].get("ERROR", 0) == 0,
        json.dumps(validation["task51"], sort_keys=True),
    )
    check(
        "display_source_audit",
        validation["task43"]["checks"] == 128
        and validation["task43"]["passed"] == 128
        and validation["task43"]["failed"] == 0,
        json.dumps(validation["task43"], sort_keys=True),
    )
    check(
        "paper_evidence_audit",
        validation["task67"]["status"] == "PASS",
        json.dumps(validation["task67"], sort_keys=True),
    )
    check(
        "task79_local_gate",
        validation["task79_gate"]["status"] == "PASS_COMPLETE"
        and validation["task79_gate"]["passed"] == 14
        and validation["task79_gate"]["failed"] == 0,
        json.dumps(validation["task79_gate"], sort_keys=True),
    )

    evidence = state["evidence_surface"]
    expected_surface = {
        "dataset_domain_settings": 9,
        "domain_areas": 8,
        "cross_dataset_display_rows": 15,
        "main_tables": 5,
        "supplement_tables": 23,
        "main_figures": 3,
        "abstract_words_cas_validator_contract": 245,
    }
    check(
        "display_surface",
        all(evidence.get(key) == value for key, value in expected_surface.items()),
        json.dumps({key: evidence.get(key) for key in expected_surface}, sort_keys=True),
    )

    expected_pages = {
        "acl_complete_evidence": 34,
        "cas_anonymous_manuscript": 26,
        "cas_supplement": 13,
        "cas_title_page": 1,
    }
    for label, pages in expected_pages.items():
        row = state["compiled_packages"][label]
        path = ROOT / row["path"]
        actual_pages = 0
        if path.exists():
            with fitz.open(path) as document:
                actual_pages = document.page_count
        type3_count = pdf_type3_count(path) if path.exists() else -1
        check(
            f"pdf_{label}",
            actual_pages == pages and type3_count == 0,
            f"pages={actual_pages}; type3={type3_count}",
        )

    missing_current = [str(path.relative_to(ROOT)) for path in CURRENT_STATUS_FILES if not path.exists()]
    check("current_status_files_present", not missing_current, str(missing_current))
    if not missing_current:
        current_text = "\n".join(path.read_text(encoding="utf-8") for path in CURRENT_STATUS_FILES)
        stale_phrases = [
            phrase
            for phrase in (
                "Task80 reconciliation in progress",
                "Task80 evidence integration in progress",
                "15-page supplement",
                "6,265",
                "2,065",
                "35 MiniMax",
            )
            if phrase in current_text
        ]
        check("current_status_has_no_stale_facts", not stale_phrases, str(stale_phrases))

    missing_historical = [
        str(path.relative_to(ROOT)) for path in HISTORICAL_STATUS_FILES if not path.exists()
    ]
    check("historical_status_files_present", not missing_historical, str(missing_historical))
    if not missing_historical:
        unmarked = []
        for path in HISTORICAL_STATUS_FILES:
            head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:16]).lower()
            if "historical" not in head or "task80" not in head:
                unmarked.append(str(path.relative_to(ROOT)))
        check("historical_status_files_marked", not unmarked, str(unmarked))

    review_readme = (PAPER / "review_packet" / "README.md").read_text(encoding="utf-8")
    review_checklist = (PAPER / "review_packet" / "submission_checklist.md").read_text(
        encoding="utf-8"
    )
    check(
        "review_packet_status_scope",
        "generated review surface" in review_readme
        and "task80_authoritative_submission_state.md" in review_readme
        and "not a live completion tracker" in review_checklist,
        "generated review packet points to Task80 authority",
    )

    manuscript_text = "\n".join(path.read_text(encoding="utf-8") for path in MAIN_CHAPTERS)
    task_labels = sorted(set(re.findall(r"\bTask\d+(?:[._-]\d+)*\b", manuscript_text)))
    check("paper_has_no_task_labels", not task_labels, str(task_labels))

    anonymous_sources = [
        PAPER / "journal_submission" / "latex" / "anonymous_manuscript.tex",
        *sorted((PAPER / "journal_submission" / "latex" / "sections").glob("*.tex")),
    ]
    anonymous_text = "\n".join(path.read_text(encoding="utf-8") for path in anonymous_sources)
    identity_hits = sorted(
        set(
            match.group(0)
            for pattern in (
                re.compile(r"/home/[A-Za-z0-9._-]+"),
                re.compile(r"github\.com/[A-Za-z0-9_.-]+", re.IGNORECASE),
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            )
            for match in pattern.finditer(anonymous_text)
        )
    )
    check("anonymous_sources_have_no_identity_hits", not identity_hits, str(identity_hits))

    secret_hits: list[str] = []
    for path in (*CURRENT_STATUS_FILES, *MAIN_CHAPTERS):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"\b(?:sk|ark)-[A-Za-z0-9_-]{20,}\b", text):
            secret_hits.append(str(path.relative_to(ROOT)))
    check("paper_control_files_have_no_api_keys", not secret_hits, str(secret_hits))

    failed = [row for row in checks if row["status"] == "FAIL"]
    payload = {
        "status": "PASS" if not failed else "FAIL",
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Task80 Final Submission Audit",
        "",
        f"Status: {payload['status']}",
        "",
        "Date: 2026-07-21",
        "",
        f"Checks: {payload['summary']['passed']}/{payload['summary']['total']} passed.",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for row in checks:
        detail = row["detail"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{row['name']}` | {row['status']} | {detail} |")
    lines.extend(
        [
            "",
            "This audit checks repository-controlled state and compiled artifacts.",
            "It does not replace author metadata, license decisions, independent",
            "scientific review, native-level language review, or final visual approval.",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload["summary"] | {"status": payload["status"]}, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
