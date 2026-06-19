#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dense top-k sentence-level MMR compression baseline for Task46.

This is a diagnostic same-budget baseline. It starts from dense top-k retrieved
chunks, splits those chunks into sentence-like evidence units, selects units with
query-sentence MMR, and caps the selected sentence context at the per-query token
budget used by a target IntentWeight/Task38 context-budget artifact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")
dense_baseline = _load_script_module("dense_baseline", SCRIPT_DIR / "dense_baseline.py")
retrieval_metrics = context_token_cost.retrieval_metrics
paired = _load_script_module("task37_paired_significance", SCRIPT_DIR / "task37_paired_significance.py")
task38 = _load_script_module("task38_calibrated_context_budget", SCRIPT_DIR / "task38_calibrated_context_budget.py")


DEFAULT_MODEL = dense_baseline.DEFAULT_MODEL


class ContextVariant(NamedTuple):
    run_id: str
    method_label: str
    budget_target_run_id: str
    support_rankings: Dict[str, List[str]]
    context_tokens: Dict[str, int]
    budget_tokens: Dict[str, int]
    sentence_counts: Dict[str, int]
    supported_chunk_counts: Dict[str, int]


@dataclass(frozen=True)
class CandidateSentence:
    chunk_id: str
    dense_rank: int
    sentence_index: int
    text: str
    token_count: int
    embedding_index: int


@dataclass(frozen=True)
class SelectedSentence:
    chunk_id: str
    dense_rank: int
    sentence_index: int
    text: str
    token_count: int
    query_score: float
    mmr_score: float


def parse_ks(value: str) -> tuple[int, ...]:
    return context_token_cost.parse_ks(value)


def query_id(record: Mapping) -> str:
    return context_token_cost.query_id(record)


def chunk_id(record: Mapping) -> str:
    return context_token_cost.chunk_id(record)


def stable_slug(value: object, *, limit: int = 80) -> str:
    raw = str(value or "")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-._")
    if len(cleaned) <= limit:
        return cleaned or "unknown"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return f"{cleaned[:limit - 9]}-{digest}"


def percentile(values: Sequence[float], q: float) -> float:
    return context_token_cost.percentile(values, q)


def split_sentence_like_units(
    text: str,
    *,
    count_tokens,
    max_sentence_tokens: int,
) -> List[str]:
    """Split text into deterministic sentence-like evidence units."""
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return []

    rough_units: List[str] = []
    for paragraph in re.split(r"(?:\n\s*){1,}", str(text or "")):
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if not paragraph:
            continue
        parts = re.split(r"(?<=[.!?;:])\s+(?=[\"'(\[]?[A-Z0-9])", paragraph)
        rough_units.extend(part.strip() for part in parts if part.strip())
    if not rough_units:
        rough_units = [normalized]

    units: List[str] = []
    for unit in rough_units:
        if count_tokens(unit) <= max_sentence_tokens:
            units.append(unit)
            continue

        words = unit.split()
        current: List[str] = []
        for word in words:
            trial = " ".join([*current, word])
            if current and count_tokens(trial) > max_sentence_tokens:
                units.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            units.append(" ".join(current))
    return [unit for unit in units if unit]


def dedupe_chunk_ranking(selected: Sequence[SelectedSentence]) -> List[str]:
    ranking: List[str] = []
    seen: set[str] = set()
    for sentence in selected:
        if sentence.chunk_id in seen:
            continue
        ranking.append(sentence.chunk_id)
        seen.add(sentence.chunk_id)
    return ranking


def context_tokens_for_ranking(
    rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
) -> Dict[str, int]:
    return {
        str(qid): int(sum(chunk_tokens.get(str(item), 0) for item in ranking[:top_k]))
        for qid, ranking in rankings.items()
    }


def sentence_count_zeros(rankings: Mapping[str, Sequence[str]]) -> Dict[str, int]:
    return {str(qid): 0 for qid in rankings}


def supported_chunk_counts(rankings: Mapping[str, Sequence[str]], *, top_k: int) -> Dict[str, int]:
    return {str(qid): len({str(item) for item in ranking[:top_k]}) for qid, ranking in rankings.items()}


def load_single_ranking_variant(label: str, path: Path):
    variants = context_token_cost.load_ranking_variants(label, path)
    if len(variants) != 1:
        raise ValueError(f"Expected one ranking variant in {path}, got {len(variants)}")
    return variants[0]


def load_target_variants(label: str, path: Path, include: str | None) -> List:
    variants = []
    for variant in context_token_cost.load_ranking_variants(label, path):
        if include and include not in variant.run_id:
            continue
        variants.append(variant)
    if not variants:
        raise ValueError(f"No target variants matched include={include!r} in {path}")
    return variants


def choose_eval_queries(
    queries: Sequence[Mapping],
    *,
    scale: str,
    eval_split: str,
    calibration_fraction: float,
    split_salt: str,
    max_queries: int | None,
) -> tuple[List[Mapping], Dict[str, object]]:
    if eval_split == "all":
        selected = list(queries)
        metadata = {"eval_split": "all"}
    else:
        calibration, test = task38.split_queries(
            queries,
            calibration_fraction=calibration_fraction,
            salt=f"{split_salt}:{scale}",
        )
        if eval_split == "calibration":
            selected = calibration
        elif eval_split == "test":
            selected = test
        else:
            raise ValueError(f"Unsupported eval_split={eval_split!r}")
        metadata = {
            "eval_split": eval_split,
            "calibration_fraction": calibration_fraction,
            "split_salt": split_salt,
            "calibration_query_count": len(calibration),
            "test_query_count": len(test),
        }
    if max_queries is not None:
        if max_queries <= 0:
            raise ValueError(f"max_queries must be positive, got {max_queries}")
        selected = selected[:max_queries]
        metadata["max_queries"] = max_queries
    return selected, metadata


def build_candidates(
    queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    corpus_by_id: Mapping[str, Mapping],
    sentence_text_to_index: Mapping[str, int],
    *,
    count_tokens,
    top_k: int,
    max_sentence_tokens: int,
) -> Dict[str, List[CandidateSentence]]:
    candidates_by_qid: Dict[str, List[CandidateSentence]] = {}
    for query in queries:
        qid = query_id(query)
        candidates: List[CandidateSentence] = []
        for dense_rank, cid in enumerate(dense_rankings.get(qid, [])[:top_k], start=1):
            chunk = corpus_by_id.get(str(cid))
            if chunk is None:
                continue
            sentence_units = split_sentence_like_units(
                str(chunk.get("text", "")),
                count_tokens=count_tokens,
                max_sentence_tokens=max_sentence_tokens,
            )
            for sentence_index, sentence_text in enumerate(sentence_units):
                token_count = int(count_tokens(sentence_text))
                if token_count <= 0:
                    continue
                candidates.append(CandidateSentence(
                    chunk_id=str(cid),
                    dense_rank=dense_rank,
                    sentence_index=sentence_index,
                    text=sentence_text,
                    token_count=token_count,
                    embedding_index=sentence_text_to_index[sentence_text],
                ))
        candidates_by_qid[qid] = candidates
    return candidates_by_qid


def collect_unique_sentence_texts(
    queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    corpus_by_id: Mapping[str, Mapping],
    *,
    count_tokens,
    top_k: int,
    max_sentence_tokens: int,
) -> List[str]:
    seen: Dict[str, None] = {}
    for query in queries:
        qid = query_id(query)
        for cid in dense_rankings.get(qid, [])[:top_k]:
            chunk = corpus_by_id.get(str(cid))
            if chunk is None:
                continue
            for sentence in split_sentence_like_units(
                str(chunk.get("text", "")),
                count_tokens=count_tokens,
                max_sentence_tokens=max_sentence_tokens,
            ):
                if count_tokens(sentence) > 0:
                    seen.setdefault(sentence, None)
    return list(seen.keys())


def select_mmr_sentences(
    candidates: Sequence[CandidateSentence],
    query_embedding: np.ndarray,
    sentence_embeddings: np.ndarray,
    *,
    budget_tokens: int,
    mmr_lambda: float,
) -> List[SelectedSentence]:
    if budget_tokens <= 0 or not candidates:
        return []
    if mmr_lambda < 0.0 or mmr_lambda > 1.0:
        raise ValueError(f"mmr_lambda must be in [0,1], got {mmr_lambda}")

    candidate_embeddings = np.asarray(
        [sentence_embeddings[candidate.embedding_index] for candidate in candidates],
        dtype=np.float32,
    )
    query_scores = candidate_embeddings @ query_embedding.astype(np.float32)
    remaining = set(range(len(candidates)))
    selected_indices: List[int] = []
    selected: List[SelectedSentence] = []
    used_tokens = 0

    while remaining:
        fitting = [
            idx for idx in remaining
            if used_tokens + candidates[idx].token_count <= budget_tokens
        ]
        if not fitting:
            break

        best_idx = None
        best_key = None
        for idx in fitting:
            if selected_indices:
                diversity_penalty = float(np.max(candidate_embeddings[idx] @ candidate_embeddings[selected_indices].T))
                mmr_score = mmr_lambda * float(query_scores[idx]) - (1.0 - mmr_lambda) * diversity_penalty
            else:
                mmr_score = float(query_scores[idx])
            candidate = candidates[idx]
            key = (
                mmr_score,
                float(query_scores[idx]),
                -candidate.dense_rank,
                -candidate.sentence_index,
            )
            if best_key is None or key > best_key:
                best_key = key
                best_idx = idx

        if best_idx is None:
            break
        candidate = candidates[best_idx]
        selected_indices.append(best_idx)
        remaining.remove(best_idx)
        used_tokens += candidate.token_count
        selected.append(SelectedSentence(
            chunk_id=candidate.chunk_id,
            dense_rank=candidate.dense_rank,
            sentence_index=candidate.sentence_index,
            text=candidate.text,
            token_count=candidate.token_count,
            query_score=float(query_scores[best_idx]),
            mmr_score=float(best_key[0]),
        ))
    return selected


def build_sent_mmr_variant(
    *,
    target_variant,
    queries: Sequence[Mapping],
    candidates_by_qid: Mapping[str, Sequence[CandidateSentence]],
    query_embeddings_by_qid: Mapping[str, np.ndarray],
    sentence_embeddings: np.ndarray,
    target_context_tokens: Mapping[str, int],
    mmr_lambda: float,
) -> tuple[ContextVariant, Dict[str, List[Mapping[str, object]]]]:
    support_rankings: Dict[str, List[str]] = {}
    context_tokens: Dict[str, int] = {}
    sentence_counts: Dict[str, int] = {}
    supported_counts: Dict[str, int] = {}
    contexts: Dict[str, List[Mapping[str, object]]] = {}

    for query in queries:
        qid = query_id(query)
        selected = select_mmr_sentences(
            candidates_by_qid.get(qid, []),
            query_embeddings_by_qid[qid],
            sentence_embeddings,
            budget_tokens=int(target_context_tokens.get(qid, 0)),
            mmr_lambda=mmr_lambda,
        )
        support_rankings[qid] = dedupe_chunk_ranking(selected)
        context_tokens[qid] = int(sum(sentence.token_count for sentence in selected))
        sentence_counts[qid] = len(selected)
        supported_counts[qid] = len(set(support_rankings[qid]))
        contexts[qid] = [
            {
                "chunk_id": sentence.chunk_id,
                "dense_rank": sentence.dense_rank,
                "sentence_index": sentence.sentence_index,
                "token_count": sentence.token_count,
                "query_score": sentence.query_score,
                "mmr_score": sentence.mmr_score,
                "text": sentence.text,
            }
            for sentence in selected
        ]

    short_target = stable_slug(target_variant.run_id, limit=64)
    variant = ContextVariant(
        run_id=f"dense_sent_mmr:{short_target}:lambda{mmr_lambda:.2f}",
        method_label="dense_sent_mmr",
        budget_target_run_id=str(target_variant.run_id),
        support_rankings=support_rankings,
        context_tokens=context_tokens,
        budget_tokens={str(qid): int(value) for qid, value in target_context_tokens.items()},
        sentence_counts=sentence_counts,
        supported_chunk_counts=supported_counts,
    )
    return variant, contexts


def evaluate_context_variant(
    variant: ContextVariant,
    queries: Sequence[Mapping],
    *,
    ks: Sequence[int],
    k: int,
    skip_empty_gt: bool = True,
) -> Dict[str, object]:
    ranking_metrics = retrieval_metrics.evaluate_rankings(
        queries,
        variant.support_rankings,
        ks=ks,
        skip_empty_gt=skip_empty_gt,
    )

    token_values: List[float] = []
    budget_values: List[float] = []
    sentence_values: List[float] = []
    supported_values: List[float] = []
    for query in queries:
        gt = retrieval_metrics._ground_truth(query)
        if not gt and skip_empty_gt:
            continue
        qid = query_id(query)
        token_values.append(float(variant.context_tokens.get(qid, 0)))
        budget_values.append(float(variant.budget_tokens.get(qid, 0)))
        sentence_values.append(float(variant.sentence_counts.get(qid, 0)))
        supported_values.append(float(variant.supported_chunk_counts.get(qid, 0)))

    token_mean = float(mean(token_values)) if token_values else 0.0
    budget_mean = float(mean(budget_values)) if budget_values else 0.0

    return {
        "run_id": variant.run_id,
        "method_label": variant.method_label,
        "budget_target_run_id": variant.budget_target_run_id,
        **ranking_metrics,
        f"avg_context_tokens@{k}": token_mean,
        f"avg_budget_tokens@{k}": budget_mean,
        f"budget_fill_ratio@{k}": token_mean / budget_mean if budget_mean > 0 else 0.0,
        f"median_context_tokens@{k}": float(median(token_values)) if token_values else 0.0,
        f"p95_context_tokens@{k}": percentile(token_values, 0.95),
        f"max_context_tokens@{k}": float(max(token_values)) if token_values else 0.0,
        f"avg_selected_sentences@{k}": float(mean(sentence_values)) if sentence_values else 0.0,
        f"avg_supported_chunks@{k}": float(mean(supported_values)) if supported_values else 0.0,
    }


def add_dense_ratios(rows: List[Dict[str, object]], *, baseline_row: Mapping[str, object], k: int) -> None:
    baseline_hit = float(baseline_row.get(f"hit@{k}", 0.0))
    baseline_tokens = float(baseline_row.get(f"avg_context_tokens@{k}", 0.0))
    for row in rows:
        row[f"hit_delta_vs_dense@{k}"] = float(row.get(f"hit@{k}", 0.0)) - baseline_hit
        tokens = float(row.get(f"avg_context_tokens@{k}", 0.0))
        row[f"context_token_ratio_vs_dense@{k}"] = tokens / baseline_tokens if baseline_tokens > 0 else 0.0
        row[f"context_token_saving_percent_vs_dense@{k}"] = (
            (1.0 - row[f"context_token_ratio_vs_dense@{k}"]) * 100.0
        )


def compare_context_variant(
    *,
    scale: str,
    queries: Sequence[Mapping],
    baseline: ContextVariant,
    variant: ContextVariant,
    k: int,
    noninferiority_margin: float,
    n_bootstrap: int,
    confidence: float,
    rng: np.random.Generator,
) -> Dict[str, object]:
    baseline_hits: List[int] = []
    method_hits: List[int] = []
    baseline_tokens: List[float] = []
    method_tokens: List[float] = []
    recall_deltas: List[float] = []
    mrr_deltas: List[float] = []
    ndcg_deltas: List[float] = []
    wins = losses = ties = 0
    token_down_hit_same = 0
    token_down_hit_worse = 0
    token_down_hit_better = 0
    evaluated = 0

    for query in queries:
        gt = retrieval_metrics._ground_truth(query)
        if not gt:
            continue
        qid = query_id(query)
        baseline_ranking = [str(item) for item in baseline.support_rankings.get(qid, [])]
        method_ranking = [str(item) for item in variant.support_rankings.get(qid, [])]
        base_hit = paired.has_hit(baseline_ranking, gt, k)
        method_hit = paired.has_hit(method_ranking, gt, k)
        base_tokens = float(baseline.context_tokens.get(qid, 0))
        method_tok = float(variant.context_tokens.get(qid, 0))

        baseline_hits.append(base_hit)
        method_hits.append(method_hit)
        baseline_tokens.append(base_tokens)
        method_tokens.append(method_tok)
        recall_deltas.append(paired.evidence_recall(method_ranking, gt, k) - paired.evidence_recall(baseline_ranking, gt, k))
        mrr_deltas.append(retrieval_metrics.mrr_at_k(method_ranking, gt, k) - retrieval_metrics.mrr_at_k(baseline_ranking, gt, k))
        ndcg_deltas.append(retrieval_metrics.ndcg_at_k(method_ranking, gt, k) - retrieval_metrics.ndcg_at_k(baseline_ranking, gt, k))

        if method_hit > base_hit:
            wins += 1
        elif method_hit < base_hit:
            losses += 1
        else:
            ties += 1
        if method_tok < base_tokens:
            if method_hit == base_hit:
                token_down_hit_same += 1
            elif method_hit > base_hit:
                token_down_hit_better += 1
            else:
                token_down_hit_worse += 1
        evaluated += 1

    baseline_hits_arr = np.asarray(baseline_hits, dtype=np.float64)
    method_hits_arr = np.asarray(method_hits, dtype=np.float64)
    baseline_tokens_arr = np.asarray(baseline_tokens, dtype=np.float64)
    method_tokens_arr = np.asarray(method_tokens, dtype=np.float64)
    hit_delta = method_hits_arr - baseline_hits_arr
    token_delta = method_tokens_arr - baseline_tokens_arr
    token_saving = baseline_tokens_arr - method_tokens_arr

    hit_mean, hit_lo, hit_hi = paired.bootstrap_ci(
        hit_delta,
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    token_delta_mean, token_delta_lo, token_delta_hi = paired.bootstrap_ci(
        token_delta,
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    saving_mean, saving_lo, saving_hi = paired.bootstrap_ci(
        token_saving,
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    recall_delta_mean, recall_delta_lo, recall_delta_hi = paired.bootstrap_ci(
        np.asarray(recall_deltas, dtype=np.float64),
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    method_only, baseline_only, mcnemar_p = paired.mcnemar_exact_p(method_hits, baseline_hits)
    token_wilcoxon_p = paired.safe_wilcoxon_p(token_saving, alternative="greater")

    baseline_token_mean = float(np.mean(baseline_tokens_arr)) if baseline_tokens_arr.size else 0.0
    method_token_mean = float(np.mean(method_tokens_arr)) if method_tokens_arr.size else 0.0
    token_ratio = method_token_mean / baseline_token_mean if baseline_token_mean > 0 else 0.0

    return {
        "scale": scale,
        "baseline_run_id": baseline.run_id,
        "method_label": variant.method_label,
        "method_run_id": variant.run_id,
        "budget_target_run_id": variant.budget_target_run_id,
        "num_queries": evaluated,
        f"baseline_hit@{k}": float(np.mean(baseline_hits_arr)) if evaluated else 0.0,
        f"method_hit@{k}": float(np.mean(method_hits_arr)) if evaluated else 0.0,
        "hit_delta_mean": hit_mean,
        "hit_delta_ci_low": hit_lo,
        "hit_delta_ci_high": hit_hi,
        "noninferior_margin": noninferiority_margin,
        "noninferior_by_ci": bool(hit_lo >= -noninferiority_margin),
        "method_only_hits": method_only,
        "baseline_only_hits": baseline_only,
        "hit_ties": ties,
        "hit_wins": wins,
        "hit_losses": losses,
        "mcnemar_p_two_sided": mcnemar_p,
        "baseline_tokens_mean": baseline_token_mean,
        "method_tokens_mean": method_token_mean,
        "token_ratio": token_ratio,
        "token_saving_percent": (1.0 - token_ratio) * 100.0,
        "token_delta_mean": token_delta_mean,
        "token_delta_ci_low": token_delta_lo,
        "token_delta_ci_high": token_delta_hi,
        "token_saving_mean": saving_mean,
        "token_saving_ci_low": saving_lo,
        "token_saving_ci_high": saving_hi,
        "token_saving_wilcoxon_p_greater": token_wilcoxon_p,
        "token_down_hit_same": token_down_hit_same,
        "token_down_hit_better": token_down_hit_better,
        "token_down_hit_worse": token_down_hit_worse,
        "token_down_nonworse_rate": (token_down_hit_same + token_down_hit_better) / evaluated if evaluated else 0.0,
        "evidence_recall_delta_mean": recall_delta_mean,
        "evidence_recall_delta_ci_low": recall_delta_lo,
        "evidence_recall_delta_ci_high": recall_delta_hi,
        "mrr_delta_mean": float(mean(mrr_deltas)) if mrr_deltas else 0.0,
        "ndcg_delta_mean": float(mean(ndcg_deltas)) if ndcg_deltas else 0.0,
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    preferred = [
        "scale",
        "split",
        "method_label",
        "run_id",
        "budget_target_run_id",
        "num_queries",
        "hit@10",
        "hit_delta_vs_dense@10",
        "evidence_recall@10",
        "mrr@10",
        "ndcg@10",
        "avg_context_tokens@10",
        "avg_budget_tokens@10",
        "budget_fill_ratio@10",
        "context_token_ratio_vs_dense@10",
        "context_token_saving_percent_vs_dense@10",
        "avg_selected_sentences@10",
        "avg_supported_chunks@10",
    ]
    fieldnames = [key for key in preferred if any(key in row for row in rows)]
    fieldnames.extend(sorted({key for row in rows for key in row if key not in set(fieldnames)}))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    path: Path,
    *,
    scale: str,
    split: str,
    rows: Sequence[Mapping[str, object]],
    paired_rows: Sequence[Mapping[str, object]],
    k: int,
    config: Mapping[str, object],
) -> None:
    summary_columns = [
        "method_label",
        "budget_target_run_id",
        f"hit@{k}",
        f"hit_delta_vs_dense@{k}",
        f"evidence_recall@{k}",
        f"avg_context_tokens@{k}",
        f"avg_budget_tokens@{k}",
        f"budget_fill_ratio@{k}",
        f"context_token_ratio_vs_dense@{k}",
        f"context_token_saving_percent_vs_dense@{k}",
        f"avg_selected_sentences@{k}",
        f"avg_supported_chunks@{k}",
    ]
    paired_columns = [
        "method_label",
        "budget_target_run_id",
        f"method_hit@{k}",
        "hit_delta_mean",
        "hit_delta_ci_low",
        "hit_delta_ci_high",
        "noninferior_by_ci",
        "token_ratio",
        "token_saving_percent",
        "token_down_nonworse_rate",
        "mcnemar_p_two_sided",
    ]

    lines = [
        "# Task46 Dense+Sentence-MMR Same-Budget Baseline",
        "",
        f"- Scale: `{scale}`",
        f"- Evaluation split: `{split}`",
        f"- Dense candidate depth: `{config.get('top_k')}`",
        f"- MMR lambda: `{float(config.get('mmr_lambda', 0.0)):.2f}`",
        f"- Sentence unit cap: `{config.get('max_sentence_tokens')}` tokens",
        f"- Budget source: `{config.get('target_ranking')}`",
        "",
        "## Summary",
        "",
        "| " + " | ".join(summary_columns) + " |",
        "| " + " | ".join("---" for _ in summary_columns) + " |",
    ]
    for row in rows:
        values = []
        for column in summary_columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:.4g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")

    lines.extend([
        "",
        "## Paired Dense Comparison",
        "",
        "| " + " | ".join(paired_columns) + " |",
        "| " + " | ".join("---" for _ in paired_columns) + " |",
    ])
    for row in paired_rows:
        values = []
        for column in paired_columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:.4g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")

    lines.extend([
        "",
        "## Notes",
        "",
        "- Dense+SentMMR starts from dense top-k chunks and only compresses the final evidence context.",
        "- Same-budget means the per-query sentence budget is capped by the selected target policy's final chunk-token budget.",
        "- Hit and evidence-recall metrics use unique source chunks represented by selected sentences.",
        "- Token metrics for SentMMR count selected sentence text, while dense and target rows count selected chunk text.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_contexts_jsonl(
    path: Path,
    contexts_by_variant: Mapping[str, Mapping[str, Sequence[Mapping[str, object]]]],
    queries: Sequence[Mapping],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    query_order = [query_id(query) for query in queries]
    with path.open("w", encoding="utf-8") as f:
        for variant_id, contexts in contexts_by_variant.items():
            for qid in query_order:
                record = {
                    "run_id": variant_id,
                    "query_id": qid,
                    "sentences": list(contexts.get(qid, [])),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task46 Dense+Sentence-MMR same-budget baseline")
    parser.add_argument("--scale", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--dense-ranking", required=True, help="label=path")
    parser.add_argument("--target-ranking", required=True, help="label=path")
    parser.add_argument("--target-include", default=None, help="Substring filter for target budget variants")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--mmr-lambda", type=float, default=0.70)
    parser.add_argument("--max-sentence-tokens", type=int, default=128)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--eval-split", default="test", choices=("all", "calibration", "test"))
    parser.add_argument("--calibration-fraction", type=float, default=0.30)
    parser.add_argument("--split-salt", default="task38_lotte_calibration_v1")
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--noninferiority-margin", type=float, default=0.01)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--write-contexts", action="store_true")
    args = parser.parse_args(argv)

    ks = parse_ks(args.ks)
    if args.k not in ks:
        ks = tuple(sorted({*ks, args.k}))
    if args.max_sentence_tokens <= 0:
        raise ValueError(f"max_sentence_tokens must be positive, got {args.max_sentence_tokens}")

    corpus = context_token_cost.load_json_list(args.corpus)
    all_queries = context_token_cost.load_json_list(args.queries)
    eval_queries, split_metadata = choose_eval_queries(
        all_queries,
        scale=args.scale,
        eval_split=args.eval_split,
        calibration_fraction=args.calibration_fraction,
        split_salt=args.split_salt,
        max_queries=args.max_queries,
    )

    dense_label, dense_path = context_token_cost.parse_ranking_arg(args.dense_ranking)
    dense_variant_raw = load_single_ranking_variant(dense_label, dense_path)
    target_label, target_path = context_token_cost.parse_ranking_arg(args.target_ranking)
    target_variants = load_target_variants(target_label, target_path, args.target_include)

    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    corpus_by_id = {chunk_id(chunk): chunk for chunk in corpus}
    chunk_tokens = {chunk_id(chunk): int(count_tokens(str(chunk.get("text", "")))) for chunk in corpus}

    dense_context_tokens = context_tokens_for_ranking(dense_variant_raw.rankings, chunk_tokens, top_k=args.top_k)
    dense_variant = ContextVariant(
        run_id=str(dense_variant_raw.run_id),
        method_label="dense_top10",
        budget_target_run_id="",
        support_rankings={str(qid): [str(item) for item in ranking[:args.top_k]] for qid, ranking in dense_variant_raw.rankings.items()},
        context_tokens=dense_context_tokens,
        budget_tokens=dense_context_tokens,
        sentence_counts=sentence_count_zeros(dense_variant_raw.rankings),
        supported_chunk_counts=supported_chunk_counts(dense_variant_raw.rankings, top_k=args.top_k),
    )

    print(f"Collecting sentence units from dense top-{args.top_k} candidates...")
    sentence_texts = collect_unique_sentence_texts(
        eval_queries,
        dense_variant_raw.rankings,
        corpus_by_id,
        count_tokens=count_tokens,
        top_k=args.top_k,
        max_sentence_tokens=args.max_sentence_tokens,
    )
    sentence_text_to_index = {text: idx for idx, text in enumerate(sentence_texts)}
    candidates_by_qid = build_candidates(
        eval_queries,
        dense_variant_raw.rankings,
        corpus_by_id,
        sentence_text_to_index,
        count_tokens=count_tokens,
        top_k=args.top_k,
        max_sentence_tokens=args.max_sentence_tokens,
    )
    print(f"Encoding {len(sentence_texts)} unique sentence units and {len(eval_queries)} queries...")
    encoder = dense_baseline.load_sentence_transformer(
        args.model,
        device=args.device,
        local_files_only=args.local_files_only,
    )
    sentence_embeddings = dense_baseline.encode_texts(
        encoder,
        sentence_texts,
        batch_size=args.batch_size,
    ) if sentence_texts else np.zeros((0, 1), dtype=np.float32)
    query_embeddings = dense_baseline.encode_texts(
        encoder,
        [str(query.get("text", "")) for query in eval_queries],
        batch_size=args.batch_size,
    )
    query_embeddings_by_qid = {
        query_id(query): query_embeddings[idx]
        for idx, query in enumerate(eval_queries)
    }

    rows: List[Dict[str, object]] = []
    paired_rows: List[Dict[str, object]] = []
    output_rankings: Dict[str, Dict[str, List[str]]] = {}
    contexts_by_variant: Dict[str, Dict[str, List[Mapping[str, object]]]] = {}

    dense_row = evaluate_context_variant(dense_variant, eval_queries, ks=ks, k=args.k)
    dense_row.update({
        "scale": args.scale,
        "split": args.eval_split,
    })
    rows.append(dense_row)
    output_rankings[dense_variant.run_id] = {
        qid: ranking[:args.top_k]
        for qid, ranking in dense_variant.support_rankings.items()
        if qid in {query_id(query) for query in eval_queries}
    }

    rng = np.random.default_rng(args.seed)
    eval_qids = {query_id(query) for query in eval_queries}
    for target_variant_raw in target_variants:
        target_context_tokens = context_tokens_for_ranking(target_variant_raw.rankings, chunk_tokens, top_k=args.top_k)
        target_variant = ContextVariant(
            run_id=str(target_variant_raw.run_id),
            method_label="budget_target",
            budget_target_run_id=str(target_variant_raw.run_id),
            support_rankings={
                str(qid): [str(item) for item in ranking[:args.top_k]]
                for qid, ranking in target_variant_raw.rankings.items()
            },
            context_tokens=target_context_tokens,
            budget_tokens=target_context_tokens,
            sentence_counts=sentence_count_zeros(target_variant_raw.rankings),
            supported_chunk_counts=supported_chunk_counts(target_variant_raw.rankings, top_k=args.top_k),
        )
        sent_variant, sent_contexts = build_sent_mmr_variant(
            target_variant=target_variant_raw,
            queries=eval_queries,
            candidates_by_qid=candidates_by_qid,
            query_embeddings_by_qid=query_embeddings_by_qid,
            sentence_embeddings=sentence_embeddings,
            target_context_tokens=target_context_tokens,
            mmr_lambda=args.mmr_lambda,
        )

        for variant in (target_variant, sent_variant):
            row = evaluate_context_variant(variant, eval_queries, ks=ks, k=args.k)
            row.update({
                "scale": args.scale,
                "split": args.eval_split,
            })
            rows.append(row)
            if variant.method_label != "budget_target":
                paired_rows.append(compare_context_variant(
                    scale=args.scale,
                    queries=eval_queries,
                    baseline=dense_variant,
                    variant=variant,
                    k=args.k,
                    noninferiority_margin=args.noninferiority_margin,
                    n_bootstrap=args.bootstrap,
                    confidence=args.confidence,
                    rng=rng,
                ))
        output_rankings[sent_variant.run_id] = {
            qid: ranking
            for qid, ranking in sent_variant.support_rankings.items()
            if qid in eval_qids
        }
        contexts_by_variant[sent_variant.run_id] = sent_contexts

    add_dense_ratios(rows, baseline_row=dense_row, k=args.k)
    rows.sort(key=lambda row: (
        str(row.get("method_label", "")),
        str(row.get("budget_target_run_id", "")),
    ))

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_prefix.with_suffix(".csv"), rows)
    paired.write_csv(output_prefix.with_suffix(".paired.csv"), paired_rows)
    output_prefix.with_suffix(".json").write_text(json.dumps({
        "config": {
            "scale": args.scale,
            "corpus": str(args.corpus),
            "queries": str(args.queries),
            "dense_ranking": args.dense_ranking,
            "target_ranking": args.target_ranking,
            "target_include": args.target_include,
            "model": args.model,
            "device": args.device,
            "local_files_only": args.local_files_only,
            "batch_size": args.batch_size,
            "top_k": args.top_k,
            "ks": list(ks),
            "k": args.k,
            "mmr_lambda": args.mmr_lambda,
            "max_sentence_tokens": args.max_sentence_tokens,
            "tokenizer": args.tokenizer,
            "encoding": args.encoding,
            "noninferiority_margin": args.noninferiority_margin,
            "bootstrap": args.bootstrap,
            "confidence": args.confidence,
            "seed": args.seed,
            **split_metadata,
        },
        "rows": rows,
        "paired_rows": paired_rows,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_prefix.with_suffix(".rankings.json").write_text(
        json.dumps(output_rankings, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(
        output_prefix.with_suffix(".md"),
        scale=args.scale,
        split=args.eval_split,
        rows=rows,
        paired_rows=paired_rows,
        k=args.k,
        config={
            "top_k": args.top_k,
            "mmr_lambda": args.mmr_lambda,
            "max_sentence_tokens": args.max_sentence_tokens,
            "target_ranking": args.target_ranking,
        },
    )
    if args.write_contexts:
        write_contexts_jsonl(output_prefix.with_suffix(".contexts.jsonl"), contexts_by_variant, eval_queries)

    print(f"Summary: {output_prefix.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
