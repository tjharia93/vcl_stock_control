"""
Item Discovery — pre-pilot prerequisite.

Scans ERPNext Item master against a list of canonical VCL keys (from
the sheet templates) and produces item_discovery_report.csv showing
match status of every variant.

Run with bench:
    bench --site <site> execute vcl_stock_control.scripts.item_discovery.run

Output: ./item_discovery_report.csv with columns:
    sheet_code, vcl_key, canonical_label, exact_match, fuzzy_matches,
    suggested_status, current_uom, candidate_item_codes
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import frappe


@dataclass
class CanonicalRow:
    sheet_code: str
    vcl_key: str
    canonical_label: str
    expected_uom: str | None = None


@dataclass
class DiscoveryResult:
    row: CanonicalRow
    exact_match: str | None
    fuzzy_matches: list[tuple[str, float]]
    suggested_status: str
    current_uom: str | None
    candidate_item_codes: list[str]


FUZZY_THRESHOLD = 0.78


def _normalise(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _all_items() -> list[dict]:
    return frappe.get_all(
        "Item",
        fields=["item_code", "item_name", "stock_uom", "disabled"],
        filters={"disabled": 0},
        limit_page_length=0,
    )


def _score(label_norm: str, item: dict) -> float:
    code_norm = _normalise(item["item_code"])
    name_norm = _normalise(item["item_name"] or "")
    return max(
        SequenceMatcher(None, label_norm, code_norm).ratio(),
        SequenceMatcher(None, label_norm, name_norm).ratio(),
    )


def discover(canonical_rows: list[CanonicalRow]) -> list[DiscoveryResult]:
    items = _all_items()
    results: list[DiscoveryResult] = []
    for row in canonical_rows:
        label_norm = _normalise(row.canonical_label)
        exact = next(
            (i["item_code"] for i in items
             if _normalise(i["item_code"]) == label_norm or _normalise(i["item_name"] or "") == label_norm),
            None,
        )
        fuzzy = sorted(
            ((i["item_code"], _score(label_norm, i)) for i in items),
            key=lambda x: x[1],
            reverse=True,
        )
        fuzzy = [(c, round(s, 3)) for c, s in fuzzy if s >= FUZZY_THRESHOLD][:5]

        if exact:
            status = "REUSE"
        elif fuzzy:
            status = "RECONCILE"
        else:
            status = "CREATE"

        candidate_codes = ([exact] if exact else []) + [c for c, _ in fuzzy if c != exact]
        current_uom = next(
            (i["stock_uom"] for i in items if i["item_code"] in candidate_codes),
            None,
        )

        results.append(DiscoveryResult(
            row=row,
            exact_match=exact,
            fuzzy_matches=fuzzy,
            suggested_status=status,
            current_uom=current_uom,
            candidate_item_codes=candidate_codes,
        ))
    return results


def write_csv(results: list[DiscoveryResult], path: str = "item_discovery_report.csv") -> str:
    out = Path(path).resolve()
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "sheet_code", "vcl_key", "canonical_label", "expected_uom",
            "exact_match", "fuzzy_matches", "suggested_status",
            "current_uom", "candidate_item_codes",
        ])
        for r in results:
            w.writerow([
                r.row.sheet_code,
                r.row.vcl_key,
                r.row.canonical_label,
                r.row.expected_uom or "",
                r.exact_match or "",
                "; ".join(f"{c}({s})" for c, s in r.fuzzy_matches),
                r.suggested_status,
                r.current_uom or "",
                "; ".join(r.candidate_item_codes),
            ])
    return str(out)


def _load_canonical_seeds() -> list[CanonicalRow]:
    """Load canonical rows from setup/canonical_seeds.csv if present, else use a stub."""
    seeds_path = Path(frappe.get_app_path("vcl_stock_control")).parent / "setup" / "canonical_seeds.csv"
    if seeds_path.exists():
        rows = []
        with open(seeds_path) as f:
            for r in csv.DictReader(f):
                rows.append(CanonicalRow(
                    sheet_code=r["sheet_code"],
                    vcl_key=r["vcl_key"],
                    canonical_label=r["canonical_label"],
                    expected_uom=r.get("expected_uom") or None,
                ))
        return rows
    return _BROWN_PAPER_STUB


_BROWN_PAPER_STUB: list[CanonicalRow] = [
    CanonicalRow("BROWN_PAPER_REELS", f"BPR-{gsm}GSM-{w}MM",
                 f"Brown Paper Reel {gsm}gsm {w}mm", "Kg")
    for gsm in (35, 40, 44, 50, 60, 70, 80)
    for w in (760, 1010, 1270)
][:21]


def run(output: str = "item_discovery_report.csv") -> str:
    """Bench entry point. Returns path to the generated CSV."""
    rows = _load_canonical_seeds()
    results = discover(rows)
    path = write_csv(results, output)
    print(f"[item_discovery] {len(results)} canonical rows scanned -> {path}")
    print(f"[item_discovery] REUSE={sum(1 for r in results if r.suggested_status=='REUSE')} "
          f"RECONCILE={sum(1 for r in results if r.suggested_status=='RECONCILE')} "
          f"CREATE={sum(1 for r in results if r.suggested_status=='CREATE')}")
    return path
