"""Render evaluation results as a side-by-side terminal table."""

import shutil

from ..stats import ElevatorUtilization
from .runner import EvalResult

_SEP = "─"
_COL_SEP = " │ "


def _col_sep_width() -> int:
    return len(_COL_SEP)


def print_results(results: list[EvalResult], input_name: str, base_config_desc: str) -> None:
    """Print a side-by-side comparison table to stdout."""
    terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns

    labels = [r.label for r in results]

    # Build all rows as (metric_label, [value_per_result]) before sizing columns.
    rows = _build_rows(results)

    # Determine column widths.
    label_col_w = max(len(r[0]) for r in rows)
    label_col_w = max(label_col_w, len("Metric"))

    value_col_ws = [max(len(labels[i]), max(len(r[1][i]) for r in rows)) for i in range(len(results))]

    # Clamp total width to terminal.
    total_w = label_col_w + sum(_col_sep_width() + w for w in value_col_ws)
    if total_w > terminal_width:
        # Shrink value columns evenly; label column is protected.
        excess = total_w - terminal_width
        per_col = excess // len(value_col_ws) + 1
        value_col_ws = [max(8, w - per_col) for w in value_col_ws]

    def divider(char: str = _SEP) -> str:
        parts = [char * label_col_w]
        for w in value_col_ws:
            parts.append(char * (_col_sep_width()) + char * w)
        return "".join(parts)

    def header_row() -> str:
        parts = ["Metric".ljust(label_col_w)]
        for i, lbl in enumerate(labels):
            parts.append(_COL_SEP + lbl[:value_col_ws[i]].ljust(value_col_ws[i]))
        return "".join(parts)

    def data_row(metric: str, values: list[str]) -> str:
        parts = [metric.ljust(label_col_w)]
        for i, v in enumerate(values):
            parts.append(_COL_SEP + v[:value_col_ws[i]].ljust(value_col_ws[i]))
        return "".join(parts)

    print(f"\n=== Algorithm Evaluation: {input_name} ===")
    print(f"Config: {base_config_desc}")
    print()
    print(header_row())
    print(divider())

    section: str | None = None
    for metric, values, is_section_header in rows:
        if is_section_header:
            if section is not None:
                print(divider())
            section = metric
            print(data_row(metric, values))
        else:
            print(data_row(metric, values))

    print(divider())


def _build_rows(results: list[EvalResult]) -> list[tuple[str, list[str], bool]]:
    """Build all table rows as (label, [value, ...], is_section_header)."""
    rows: list[tuple[str, list[str], bool]] = []

    def row(label: str, values: list[str], section: bool = False) -> None:
        rows.append((label, values, section))

    def fmt_f(v: float) -> str:
        return f"{v:.1f}"

    def fmt_i(v: int) -> str:
        return str(v)

    def fmt_pct(v: float) -> str:
        return f"{v:.1f}%"

    # ── Overview ──────────────────────────────────────────────────────────────
    row("Overview", [""] * len(results), section=True)
    row("  Passengers served", [fmt_i(r.stats.count) for r in results])
    row("  Simulation duration (ticks)", [fmt_i(r.simulation_duration) for r in results])
    row("  Total floors traveled", [fmt_i(r.total_floors_traveled) for r in results])

    # ── Wait time ─────────────────────────────────────────────────────────────
    row("Wait time", [""] * len(results), section=True)
    row("  avg", [fmt_f(r.stats.avg_wait) for r in results])
    row("  std", [fmt_f(r.stats.std_wait) for r in results])
    row("  p95", [fmt_f(r.stats.p95_wait) for r in results])
    row("  min", [f"{r.stats.min_wait} ({r.stats.min_wait_id})" for r in results])
    row("  max", [f"{r.stats.max_wait} ({r.stats.max_wait_id})" for r in results])

    # ── Total time ────────────────────────────────────────────────────────────
    row("Total time", [""] * len(results), section=True)
    row("  avg", [fmt_f(r.stats.avg_total) for r in results])
    row("  std", [fmt_f(r.stats.std_total) for r in results])
    row("  p95", [fmt_f(r.stats.p95_total) for r in results])
    row("  min", [f"{r.stats.min_total} ({r.stats.min_total_id})" for r in results])
    row("  max", [f"{r.stats.max_total} ({r.stats.max_total_id})" for r in results])

    # ── Elevator utilization ──────────────────────────────────────────────────
    row("Elevator utilization", [""] * len(results), section=True)
    row("  avg", [fmt_pct(_avg_util(r.utilization)) for r in results])
    row("  min", [_min_util_str(r.utilization) for r in results])
    row("  max", [_max_util_str(r.utilization) for r in results])

    # Per-elevator rows — use the max elevator count across all results.
    max_elevators = max(len(r.utilization) for r in results)
    for i in range(max_elevators):
        row(
            f"  E{i + 1}",
            [_elevator_util_str(r.utilization, i) for r in results],
        )

    return rows


def _avg_util(utilization: list[ElevatorUtilization]) -> float:
    rates = [u.utilization for u in utilization]
    return sum(rates) / len(rates) if rates else 0.0


def _min_util_str(utilization: list[ElevatorUtilization]) -> str:
    if not utilization:
        return "—"
    u = min(utilization, key=lambda u: u.utilization)
    return f"{u.utilization:.1f}% (E{u.elevator_id})"


def _max_util_str(utilization: list[ElevatorUtilization]) -> str:
    if not utilization:
        return "—"
    u = max(utilization, key=lambda u: u.utilization)
    return f"{u.utilization:.1f}% (E{u.elevator_id})"


def _elevator_util_str(utilization: list[ElevatorUtilization], index: int) -> str:
    if index >= len(utilization):
        return "—"
    u = utilization[index]
    return f"{u.utilization:.1f}% ({u.active_ticks}/{u.total_ticks})"
