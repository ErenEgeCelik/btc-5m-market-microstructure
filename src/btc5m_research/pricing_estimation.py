"""Offline regression tools for the archived pricing study.

The target is a fitted market-implied scale, not realized volatility or P&L.
See docs/pricing-estimation.md for the input contract and evaluation limits.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import fmean, pstdev
from typing import Iterable, Mapping, Sequence

from .quote_model import transformed_quote_target


@dataclass(frozen=True)
class LinearFit:
    intercept: float
    coefficients: tuple[float, ...]

    def predict(self, features: Sequence[float]) -> float:
        if len(features) != len(self.coefficients):
            raise ValueError("feature count differs from fitted model")
        if not all(math.isfinite(value) for value in features):
            raise ValueError("features must be finite")
        return self.intercept + math.fsum(b * x for b, x in zip(self.coefficients, features))


def _solve(matrix: list[list[float]], target: list[float]) -> list[float]:
    """Partial-pivot Gaussian elimination for a small standardized Gram matrix."""
    n = len(target)
    rows = [list(row) + [value] for row, value in zip(matrix, target)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda i: abs(rows[i][column]))
        if abs(rows[pivot][column]) < 1e-12:
            raise ValueError("features are constant or linearly dependent")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for i in range(n):
            if i == column:
                continue
            multiplier = rows[i][column]
            rows[i] = [a - multiplier * b for a, b in zip(rows[i], rows[column])]
    return [rows[i][-1] for i in range(n)]


def fit_ols(features: Sequence[Sequence[float]], targets: Sequence[float]) -> LinearFit:
    """Fit OLS with an intercept, centering/scaling columns for numeric stability.

    Intended for the one-to-three-feature archived models, not large or ill-conditioned
    general linear algebra. Rank deficiency is an error rather than an implicit penalty.
    """
    if len(features) != len(targets) or not features:
        raise ValueError("features and targets must have equal nonzero length")
    p = len(features[0])
    if p < 1 or len(features) <= p:
        raise ValueError("need more observations than features")
    if any(len(row) != p for row in features):
        raise ValueError("feature rows must have equal length")
    if not all(math.isfinite(x) for row in features for x in row) or not all(
        math.isfinite(y) for y in targets
    ):
        raise ValueError("regression inputs must be finite")
    centers = [fmean(row[j] for row in features) for j in range(p)]
    scales = [pstdev(row[j] for row in features) for j in range(p)]
    if any(scale == 0 for scale in scales):
        raise ValueError("features are constant or linearly dependent")
    standardized = [
        [(row[j] - centers[j]) / scales[j] for j in range(p)] for row in features
    ]
    y_mean = fmean(targets)
    gram = [
        [fmean(row[a] * row[b] for row in standardized) for b in range(p)]
        for a in range(p)
    ]
    cov = [
        fmean(row[j] * (y - y_mean) for row, y in zip(standardized, targets))
        for j in range(p)
    ]
    scaled_coefs = _solve(gram, cov)
    coefs = tuple(coef / scale for coef, scale in zip(scaled_coefs, scales))
    intercept = y_mean - math.fsum(coef * center for coef, center in zip(coefs, centers))
    return LinearFit(intercept, coefs)


def r_squared(targets: Sequence[float], predictions: Sequence[float]) -> float:
    """Score against the evaluated target mean; negative held-out scores are retained."""
    if not targets or len(targets) != len(predictions):
        raise ValueError("targets and predictions must have equal nonzero length")
    if not all(math.isfinite(x) for x in [*targets, *predictions]):
        raise ValueError("scores require finite values")
    center = fmean(targets)
    total = math.fsum((value - center) ** 2 for value in targets)
    if total == 0:
        raise ValueError("R-squared is undefined for a constant target")
    return 1 - math.fsum((a - b) ** 2 for a, b in zip(targets, predictions)) / total


def fit_transformed_schedule(
    displacement: Sequence[float], mids: Sequence[float], tau_s: Sequence[float]
) -> dict[str, float | int]:
    """Fit Phi^-1(mid)*sqrt(tau) = alpha + beta*displacement.

    Observations must already pass the caller's clock, quote-health and sample masks.
    This helper does not turn arbitrary observations into a verified dataset.
    """
    if len(displacement) != len(mids) or len(mids) != len(tau_s):
        raise ValueError("schedule inputs must have equal length")
    target = [transformed_quote_target(mid, tau) for mid, tau in zip(mids, tau_s)]
    fit = fit_ols([[x] for x in displacement], target)
    beta = fit.coefficients[0]
    if beta <= 0:
        raise ValueError("a positive fitted slope is required for a positive scale")
    return {
        "n": len(target),
        "alpha": fit.intercept,
        "beta": beta,
        "sigma_usd_per_sqrt_s": 1 / beta,
        "anchor_offset_usd": fit.intercept / beta,
        "transformed_r_squared": r_squared(target, [fit.predict([x]) for x in displacement]),
    }


def leave_one_group_out(
    rows: Sequence[Mapping[str, object]], feature_names: Sequence[str],
    target: str = "sigma_hat", group: str = "source_group",
) -> dict[str, object]:
    """Re-estimate on every training fold and freeze before scoring its omitted log.

    All requested fields must be present and finite. Missing rows are not silently dropped.
    This groups by acquisition log, not time; it does not enforce chronological evaluation.
    """
    if not feature_names or len(set(feature_names)) != len(feature_names):
        raise ValueError("feature names must be nonempty and unique")
    groups = sorted({str(row[group]) for row in rows})
    if len(groups) < 2:
        raise ValueError("leave-one-group-out requires at least two groups")
    def x(row: Mapping[str, object]) -> list[float]:
        return [float(row[name]) for name in feature_names]
    actual: list[float] = []
    predicted: list[float] = []
    folds = []
    for holdout in groups:
        train = [row for row in rows if str(row[group]) != holdout]
        test = [row for row in rows if str(row[group]) == holdout]
        fit = fit_ols([x(row) for row in train], [float(row[target]) for row in train])
        actual.extend(float(row[target]) for row in test)
        predicted.extend(fit.predict(x(row)) for row in test)
        folds.append({
            "held_out_group": holdout, "n_train": len(train), "n_test": len(test),
            "intercept": fit.intercept, "coefficients": list(fit.coefficients),
        })
    full = fit_ols([x(row) for row in rows], [float(row[target]) for row in rows])
    cvs = []
    for j in range(len(feature_names)):
        values = [fold["coefficients"][j] for fold in folds]
        average = fmean(values)
        cvs.append(pstdev(values) / abs(average) if average != 0 else None)
    return {
        "features": list(feature_names), "n": len(rows), "n_groups": len(groups),
        "full_fit": {"intercept": full.intercept, "coefficients": list(full.coefficients)},
        "in_sample_r_squared": r_squared(
            [float(row[target]) for row in rows], [full.predict(x(row)) for row in rows]
        ),
        "logo_r_squared": r_squared(actual, predicted),
        "coefficient_cv": cvs, "folds": folds,
    }


def variance_inflation_factors(
    rows: Sequence[Mapping[str, object]], feature_names: Sequence[str],
) -> dict[str, float]:
    if len(feature_names) == 1:
        return {feature_names[0]: 1.0}
    result = {}
    for name in feature_names:
        others = [other for other in feature_names if other != name]
        target = [float(row[name]) for row in rows]
        design = [[float(row[other]) for other in others] for row in rows]
        fit = fit_ols(design, target)
        r2 = r_squared(target, [fit.predict(row) for row in design])
        result[name] = 1 / (1 - r2) if r2 < 1 else math.inf
    return result


ARCHIVED_MODELS = (
    ("range2",), ("range2_pre",), ("range2", "dvol_per_sqrt_s"),
    ("range2", "abs_ofi_30s"), ("range2", "dvol_per_sqrt_s", "abs_ofi_30s"),
    ("range2_pre", "dvol_per_sqrt_s", "abs_ofi_30s"),
    ("range2", "dvol_per_sqrt_s", "abs_cvd_2m"),
)


def audit_feature_table(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Recompute the seven frozen historical candidate comparisons without a new search."""
    prepared = [dict(row) for row in rows]
    for row in prepared:
        row["abs_ofi_30s"] = abs(float(row["ofi_30s"]))
        row["abs_cvd_2m"] = abs(float(row["cvd_2m"]))
    results = []
    for features in ARCHIVED_MODELS:
        result = leave_one_group_out(prepared, features)
        result["vif"] = variance_inflation_factors(prepared, features)
        cv = result["coefficient_cv"][0]
        result["passes_archived_selection_rule"] = (
            result["logo_r_squared"] > 0.300 and cv is not None and cv < 0.20
            and max(result["vif"].values()) < 5
        )
        results.append(result)
    eligible = [r for r in results if r["passes_archived_selection_rule"]]
    selected = max(eligible, key=lambda r: r["logo_r_squared"]) if eligible else None
    return {
        "evaluation": "archived-feature recheck; log-wise validation, not chronological OOS",
        "n": len(prepared), "models": results,
        "selected_features": selected["features"] if selected else None,
    }
