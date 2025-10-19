# search_agent.py

"""Search Agent for evaluating RWA startups.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Keyword groups used for scoring
DOMAIN_SEGMENT_KEYWORDS = {
    "custody": 0.3,
    "issuance": 0.3,
    "tokenization": 0.3,
    "oracle": 0.3,
    "regulation": 0.3,
    "compliance": 0.3,
}
REGULATORY_KEYWORDS = {
    "sec": 0.3,
    "mas": 0.3,
    "bafin": 0.3,
    "finma": 0.3,
    "fca": 0.3,
    "regulator": 0.3,
    "licensed": 0.3,
}
INSTITUTIONAL_TERMS = {
    "qualified investor": 0.2,
    "broker-dealer": 0.2,
    "institutional": 0.2,
    "custodian": 0.2,
}
TECHNICAL_TERMS = {
    "mpc": 0.2,
    "multi-party": 0.2,
    "zero-knowledge": 0.2,
    "zk": 0.2,
    "compliance infra": 0.2,
    "infrastructure": 0.2,
}

INVESTOR_KEYWORDS = {
    "blackrock": 0.4,
    "a16z": 0.4,
    "andreessen horowitz": 0.4,
    "pantera": 0.4,
    "coinbase ventures": 0.4,
    "polychain": 0.4,
}
PARTNER_KEYWORDS = {
    "bank": 0.3,
    "custodian": 0.3,
    "asset manager": 0.3,
    "partner": 0.3,
}
FUNDING_STAGE_SCORES = {
    "seed": 0.1,
    "series a": 0.2,
    "series b": 0.2,
    "series c": 0.2,
    "series d": 0.2,
    "series e": 0.2,
}
REPORT_KEYWORDS = {
    "report": 0.1,
    "portfolio": 0.1,
    "coverage": 0.1,
    "featured": 0.1,
}

EXCLUSION_KEYWORDS = {"airdrop", "apy", "meme", "retail"}


def ensure_output_folder() -> str:
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.join(output_dir, "selected_candidates.json")


def _combine_text(row: pd.Series, columns: List[str]) -> str:
    return " ".join(str(row[col]) for col in columns if col in row and pd.notna(row[col])).lower()


def _aggregate_row_text(row: pd.Series) -> str:
    return " ".join(str(value).lower() for value in row.values if pd.notna(value))


def score_domain_fit(row: pd.Series) -> float:
    text = _aggregate_row_text(row)
    segment_text = _combine_text(row, ["segment"])
    score = 0.0
    for group in [DOMAIN_SEGMENT_KEYWORDS, REGULATORY_KEYWORDS, INSTITUTIONAL_TERMS, TECHNICAL_TERMS]:
        for keyword, value in group.items():
            if keyword in text or keyword in segment_text:
                score += value
                if score >= 1.0:
                    return 1.0
    return min(score, 1.0)


def score_credibility(row: pd.Series) -> float:
    text = _aggregate_row_text(row)
    score = 0.0
    for keyword, value in INVESTOR_KEYWORDS.items():
        if keyword in text:
            score += value
            break
    for keyword, value in PARTNER_KEYWORDS.items():
        if keyword in text:
            score += value
            break
    funding_stage = str(row.get("funding_stage", "")).lower()
    for stage, value in FUNDING_STAGE_SCORES.items():
        if stage in funding_stage:
            score += value
            break
    for keyword, value in REPORT_KEYWORDS.items():
        if keyword in text:
            score += value
            break
    return min(score, 1.0)


def has_exclusion_flag(row: pd.Series) -> bool:
    text = _aggregate_row_text(row)
    return any(keyword in text for keyword in EXCLUSION_KEYWORDS)


def evaluate_startup(row: pd.Series) -> Dict[str, object]:
    domain_fit = score_domain_fit(row)
    credibility = score_credibility(row)
    final_score = round(0.6 * domain_fit + 0.4 * credibility, 3)
    reason = str(row.get("evidence", "") or row.get("notes", "") or row.get("description", ""))
    return {
        "name": row.get("name"),
        "website": row.get("website"),
        "segment": row.get("segment"),
        "region": row.get("region"),
        "funding_stage": row.get("funding_stage"),
        "domain_fit": round(domain_fit, 3),
        "credibility_score": round(credibility, 3),
        "final_score": final_score,
        "reason": reason,
    }


def select_candidates(df: pd.DataFrame, top_n: int) -> List[Dict[str, object]]:
    evaluations = []
    for _, row in df.iterrows():
        if has_exclusion_flag(row):
            continue
        evaluation = evaluate_startup(row)
        evaluations.append(evaluation)
    evaluations.sort(key=lambda item: item["final_score"], reverse=True)
    return evaluations[:top_n]


def save_results(candidates: List[Dict[str, object]], output_path: str | Path) -> None:
    Path(output_path).write_text(json.dumps(candidates, indent=2))


def run_pipeline(csv_path: Path, output_path: str | Path, top_n: int) -> None:
    df = pd.read_csv(csv_path)
    selected = select_candidates(df, top_n=top_n)
    save_results(selected, output_path)


def main() -> None:
    input_csv = Path("rwa_top15_crossverified.csv")
    output_json = ensure_output_folder()
    top_n = 3
    run_pipeline(input_csv, output_json, top_n)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RWA startups and select top candidates.")
    parser.add_argument("--csv", type=Path, default=None, help="Path to the CSV file containing startup data.")
    parser.add_argument("--output", type=Path, default=None, help="Path to save the selected candidates JSON.")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top startups to select (2 or 3 recommended).")
    args = parser.parse_args()

    if args.csv is not None or args.output is not None or args.top_n != 3:
        csv_path = args.csv if args.csv is not None else Path("rwa_top15_crossverified.csv")
        if args.output is not None:
            output_path = args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(ensure_output_folder())
        run_pipeline(csv_path, output_path, args.top_n)
    else:
        main()
