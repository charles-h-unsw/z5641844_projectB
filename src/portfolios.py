"""Walk-forward out-of-sample fund construction for Project B.

The functions in this module estimate monthly target weights from expanding
windows that end strictly before the rebalance date, then run a buy-and-hold
daily accounting path until the next rebalance.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
import pandas as pd
from scipy.optimize import minimize

METHOD_EQUAL_WEIGHT = "Equal Weight"
METHOD_MIN_VARIANCE = "Minimum Variance"
METHOD_RISK_PARITY = "Risk Parity"
METHODS = (METHOD_EQUAL_WEIGHT, METHOD_MIN_VARIANCE, METHOD_RISK_PARITY)
MAX_TARGET_WEIGHT = 0.20
TRANSACTION_COST_RATE = 0.001
RISK_FREE_RATE = 0.0
INITIAL_ESTIMATION_YEAR = 2020


@dataclass(frozen=True)
class FundSpec:
    """Stable identity and assumptions for one fund."""

    fund_id: str
    fund_name: str
    asset_family: str
    method: str
    annualisation_factor: int
    calendar: str


@dataclass(frozen=True)
class OptimisationResult:
    """Target weights and diagnostics for one rebalance."""

    weights: np.ndarray
    success: bool
    message: str
    objective_value: float
    covariance_regularisation: float
    max_risk_contribution_deviation: float


def clean_return_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Return a sorted numeric return matrix with unique dates and columns."""

    if returns.empty:
        raise ValueError("returns must not be empty")
    frame = returns.copy()
    frame.index = pd.DatetimeIndex(pd.to_datetime(frame.index)).normalize()
    frame = frame.sort_index()
    if not frame.index.is_unique:
        raise ValueError("return index must be unique")
    if frame.columns.duplicated().any():
        raise ValueError("return columns must be unique")
    frame = frame.apply(pd.to_numeric, errors="coerce")
    if frame.isna().any().any():
        missing = int(frame.isna().sum().sum())
        raise ValueError(f"return matrix contains {missing} missing values")
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("return matrix contains non-finite values")
    return frame


def monthly_rebalance_dates(
    returns: pd.DataFrame,
    *,
    initial_estimation_year: int = INITIAL_ESTIMATION_YEAR,
) -> pd.DatetimeIndex:
    """First available return observation of each month after the estimation year."""

    frame = clean_return_matrix(returns)
    live = frame.loc[frame.index.year > initial_estimation_year]
    if live.empty:
        raise ValueError("no out-of-sample dates after the initial estimation year")
    dates = live.index.to_series()
    return pd.DatetimeIndex(dates.groupby(dates.dt.to_period("M")).first())


def assert_no_lookahead(
    diagnostics: pd.DataFrame,
    returns: pd.DataFrame,
    *,
    initial_estimation_year: int = INITIAL_ESTIMATION_YEAR,
) -> None:
    """Raise if any rebalance was estimated using same-day or future returns."""

    if diagnostics.empty:
        raise ValueError("diagnostics are empty")
    training_end = pd.to_datetime(diagnostics["training_end"])
    rebalance_date = pd.to_datetime(diagnostics["rebalance_date"])
    if training_end.ge(rebalance_date).any():
        raise ValueError("look-ahead detected: training_end must precede rebalance_date")
    first_live = pd.to_datetime(diagnostics["rebalance_date"]).min()
    if first_live.year <= initial_estimation_year:
        raise ValueError("first live date is inside the initial estimation period")
    live_start = monthly_rebalance_dates(
        returns,
        initial_estimation_year=initial_estimation_year,
    ).min()
    if first_live != live_start:
        raise ValueError("diagnostic first live date does not match the return calendar")


def covariance_matrix(training_returns: pd.DataFrame) -> tuple[np.ndarray, float]:
    """Estimate covariance and add minimal diagonal regularisation if needed."""

    train = clean_return_matrix(training_returns)
    if len(train) < 2:
        raise ValueError("at least two training observations are required")
    cov = train.cov().to_numpy(dtype=float)
    if not np.isfinite(cov).all():
        raise ValueError("covariance matrix contains non-finite values")
    cov = (cov + cov.T) / 2.0
    eigen_min = float(np.linalg.eigvalsh(cov).min())
    regularisation = 0.0
    if eigen_min < 1e-10:
        scale = float(np.trace(cov) / max(len(cov), 1))
        regularisation = max(1e-8, 1e-8 * scale, -eigen_min + 1e-10)
        cov = cov + np.eye(len(cov)) * regularisation
    return cov, regularisation


def equal_weight(n_assets: int) -> np.ndarray:
    """Fully invested equal-weight target."""

    if n_assets < 1:
        raise ValueError("n_assets must be positive")
    return np.repeat(1.0 / n_assets, n_assets)


def optimise_minimum_variance(
    training_returns: pd.DataFrame,
    *,
    max_weight: float = MAX_TARGET_WEIGHT,
) -> OptimisationResult:
    """Long-only capped minimum-variance optimiser."""

    n_assets = training_returns.shape[1]
    _check_cap_feasible(n_assets, max_weight)
    cov, regularisation = covariance_matrix(training_returns)
    x0 = equal_weight(n_assets)
    bounds = [(0.0, max_weight)] * n_assets
    constraints = [{"type": "eq", "fun": lambda weights: float(weights.sum() - 1.0)}]
    result = minimize(
        lambda weights: float(weights @ cov @ weights),
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000, "disp": False},
    )
    weights = _normalise_weights(result.x)
    success = bool(result.success and _weights_valid(weights, max_weight))
    return OptimisationResult(
        weights=weights,
        success=success,
        message=str(result.message),
        objective_value=float(weights @ cov @ weights),
        covariance_regularisation=regularisation,
        max_risk_contribution_deviation=np.nan,
    )


def optimise_risk_parity(
    training_returns: pd.DataFrame,
    *,
    max_weight: float = MAX_TARGET_WEIGHT,
) -> OptimisationResult:
    """Long-only capped equal-risk-contribution optimiser."""

    n_assets = training_returns.shape[1]
    _check_cap_feasible(n_assets, max_weight)
    cov, regularisation = covariance_matrix(training_returns)
    target = np.repeat(1.0 / n_assets, n_assets)
    x0 = _normalise_weights(1.0 / np.sqrt(np.clip(np.diag(cov), 1e-16, None)))
    x0 = np.minimum(x0, max_weight)
    x0 = _normalise_weights(x0)
    if (x0 > max_weight + 1e-12).any():
        x0 = equal_weight(n_assets)

    bounds = [(0.0, max_weight)] * n_assets
    constraints = [{"type": "eq", "fun": lambda weights: float(weights.sum() - 1.0)}]

    def objective(weights: np.ndarray) -> float:
        rc = risk_contribution_shares(weights, cov)
        return float(np.square(rc - target).sum())

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 2000, "disp": False},
    )
    weights = _normalise_weights(result.x)
    rc_deviation = float(np.abs(risk_contribution_shares(weights, cov) - target).max())
    success = bool(result.success and _weights_valid(weights, max_weight))
    return OptimisationResult(
        weights=weights,
        success=success,
        message=str(result.message),
        objective_value=float(objective(weights)),
        covariance_regularisation=regularisation,
        max_risk_contribution_deviation=rc_deviation,
    )


def risk_contribution_shares(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Return each asset's share of total portfolio variance."""

    weights = np.asarray(weights, dtype=float)
    marginal = cov @ weights
    variance = float(weights @ marginal)
    if variance <= 0 or not np.isfinite(variance):
        return np.repeat(np.nan, len(weights))
    return weights * marginal / variance


def optimise_weights(
    training_returns: pd.DataFrame,
    method: str,
    *,
    max_weight: float = MAX_TARGET_WEIGHT,
) -> OptimisationResult:
    """Dispatch to the requested target-weight method."""

    n_assets = training_returns.shape[1]
    if method == METHOD_EQUAL_WEIGHT:
        weights = equal_weight(n_assets)
        return OptimisationResult(
            weights=weights,
            success=True,
            message="deterministic equal weight",
            objective_value=np.nan,
            covariance_regularisation=0.0,
            max_risk_contribution_deviation=np.nan,
        )
    if method == METHOD_MIN_VARIANCE:
        return optimise_minimum_variance(training_returns, max_weight=max_weight)
    if method == METHOD_RISK_PARITY:
        return optimise_risk_parity(training_returns, max_weight=max_weight)
    raise ValueError(f"unknown portfolio method: {method}")


def oos_backtest(
    returns: pd.DataFrame,
    method: str = METHOD_MIN_VARIANCE,
    *,
    fund_spec: FundSpec | None = None,
    asset_metadata: pd.DataFrame | None = None,
    max_weight: float = MAX_TARGET_WEIGHT,
    transaction_cost_rate: float = TRANSACTION_COST_RATE,
    initial_estimation_year: int = INITIAL_ESTIMATION_YEAR,
) -> dict[str, pd.DataFrame]:
    """Run a monthly expanding-window out-of-sample buy-and-hold backtest."""

    frame = clean_return_matrix(returns)
    assets = frame.columns.astype(str).tolist()
    n_assets = len(assets)
    _check_cap_feasible(n_assets, max_weight)

    if fund_spec is None:
        fund_spec = FundSpec(
            fund_id=method.lower().replace(" ", "_"),
            fund_name=method,
            asset_family="Unspecified",
            method=method,
            annualisation_factor=252,
            calendar="unspecified",
        )
    metadata = _prepare_asset_metadata(assets, fund_spec.asset_family, asset_metadata)
    rebalance_dates = monthly_rebalance_dates(
        frame,
        initial_estimation_year=initial_estimation_year,
    )
    live_returns = frame.loc[frame.index >= rebalance_dates.min()].copy()
    rebalance_set = set(rebalance_dates)
    current_weights: np.ndarray | None = None
    gross_wealth = 1.0
    net_wealth = 1.0
    returns_rows: list[dict[str, object]] = []
    weights_rows: list[dict[str, object]] = []
    diagnostics_rows: list[dict[str, object]] = []

    for date, row in live_returns.iterrows():
        rebalance_flag = date in rebalance_set
        turnover = 0.0
        transaction_cost = 0.0
        if rebalance_flag:
            training = frame.loc[frame.index < date]
            training_start = training.index.min()
            training_end = training.index.max()
            opt = optimise_weights(training, method, max_weight=max_weight)
            if not opt.success:
                raise RuntimeError(
                    f"optimiser failed for {fund_spec.fund_id} on {date.date()}: {opt.message}"
                )
            target_weights = opt.weights
            pretrade = np.zeros(n_assets) if current_weights is None else current_weights.copy()
            if current_weights is not None:
                turnover = float(0.5 * np.abs(target_weights - pretrade).sum())
                transaction_cost = float(transaction_cost_rate * turnover)
            current_weights = target_weights.copy()
            next_idx = np.where(rebalance_dates == date)[0][0] + 1
            next_rebalance_date = (
                rebalance_dates[next_idx] if next_idx < len(rebalance_dates) else pd.NaT
            )
            diagnostics_rows.append(
                {
                    "fund_id": fund_spec.fund_id,
                    "fund_name": fund_spec.fund_name,
                    "asset_family": fund_spec.asset_family,
                    "method": fund_spec.method,
                    "rebalance_date": date,
                    "next_rebalance_date": next_rebalance_date,
                    "training_start": training_start,
                    "training_end": training_end,
                    "training_observations": len(training),
                    "solver_success": opt.success,
                    "solver_message": opt.message,
                    "objective_value": opt.objective_value,
                    "covariance_regularisation": opt.covariance_regularisation,
                    "max_risk_contribution_deviation": opt.max_risk_contribution_deviation,
                    "weight_sum": float(target_weights.sum()),
                    "minimum_weight": float(target_weights.min()),
                    "maximum_weight": float(target_weights.max()),
                }
            )
            for asset, pre_w, target_w in zip(assets, pretrade, target_weights, strict=True):
                meta = metadata.loc[asset]
                weights_rows.append(
                    {
                        "rebalance_date": date,
                        "fund_id": fund_spec.fund_id,
                        "fund_name": fund_spec.fund_name,
                        "asset_family": fund_spec.asset_family,
                        "method": fund_spec.method,
                        "asset": asset,
                        "asset_class": meta["asset_class"],
                        "sector": meta["sector"],
                        "pretrade_weight": float(pre_w),
                        "target_weight": float(target_w),
                        "is_latest_rebalance": False,
                    }
                )

        if current_weights is None:
            raise RuntimeError("no target weights were available for the live period")
        asset_returns = row.to_numpy(dtype=float)
        gross_return = float(current_weights @ asset_returns)
        net_return = float((1.0 - transaction_cost) * (1.0 + gross_return) - 1.0)
        gross_wealth *= 1.0 + gross_return
        net_wealth *= 1.0 + net_return
        denominator = 1.0 + gross_return
        if denominator <= 0:
            raise RuntimeError(f"portfolio wealth became non-positive on {date.date()}")
        current_weights = current_weights * (1.0 + asset_returns) / denominator
        current_weights = _normalise_weights(current_weights)
        net_drawdown = net_wealth / max(1.0, max([1.0, net_wealth])) - 1.0
        returns_rows.append(
            {
                "date": date,
                "fund_id": fund_spec.fund_id,
                "fund_name": fund_spec.fund_name,
                "asset_family": fund_spec.asset_family,
                "method": fund_spec.method,
                "gross_return": gross_return,
                "net_return": net_return,
                "gross_wealth": gross_wealth,
                "net_wealth": net_wealth,
                "net_drawdown": net_drawdown,
                "rebalance_flag": rebalance_flag,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
            }
        )

    fund_returns = pd.DataFrame(returns_rows)
    fund_returns["net_drawdown"] = (
        fund_returns["net_wealth"] / fund_returns["net_wealth"].cummax() - 1.0
    )
    fund_weights = pd.DataFrame(weights_rows)
    if not fund_weights.empty:
        latest = fund_weights["rebalance_date"].max()
        fund_weights["is_latest_rebalance"] = fund_weights["rebalance_date"].eq(latest)
    diagnostics = pd.DataFrame(diagnostics_rows)
    assert_no_lookahead(diagnostics, frame, initial_estimation_year=initial_estimation_year)
    return {
        "returns": fund_returns,
        "weights": fund_weights,
        "diagnostics": diagnostics,
    }


def build_fund_suite(
    universes: dict[str, pd.DataFrame],
    metadata: dict[str, pd.DataFrame],
    *,
    transaction_cost_rate: float = TRANSACTION_COST_RATE,
    max_weight: float = MAX_TARGET_WEIGHT,
) -> dict[str, pd.DataFrame]:
    """Build all nine base funds across equity, crypto, and combined universes."""

    specs = fund_specs()
    return_parts: list[pd.DataFrame] = []
    weight_parts: list[pd.DataFrame] = []
    diagnostic_parts: list[pd.DataFrame] = []
    design_rows: list[dict[str, object]] = []

    for spec in specs:
        result = oos_backtest(
            universes[spec.asset_family],
            method=spec.method,
            fund_spec=spec,
            asset_metadata=metadata[spec.asset_family],
            transaction_cost_rate=transaction_cost_rate,
            max_weight=max_weight,
        )
        returns = result["returns"]
        diagnostics = result["diagnostics"]
        design_rows.append(
            {
                "fund_id": spec.fund_id,
                "fund_name": spec.fund_name,
                "asset_family": spec.asset_family,
                "method": spec.method,
                "calendar": spec.calendar,
                "annualisation_factor": spec.annualisation_factor,
                "initial_estimation_start": universes[spec.asset_family].index.min(),
                "initial_estimation_end": pd.Timestamp(f"{INITIAL_ESTIMATION_YEAR}-12-31"),
                "first_live_date": returns["date"].min(),
                "end_date": returns["date"].max(),
                "window_type": "expanding",
                "rebalance_rule": "first available observation of each calendar month",
                "training_rule": "returns strictly before rebalance_date",
                "holding_rule": "monthly target weights drift with buy-and-hold daily returns",
                "max_target_weight": max_weight if spec.method != METHOD_EQUAL_WEIGHT else np.nan,
                "risk_free_rate": RISK_FREE_RATE,
                "transaction_cost_rate": transaction_cost_rate,
                "initial_establishment_cost_charged": False,
            }
        )
        return_parts.append(returns)
        weight_parts.append(result["weights"])
        diagnostic_parts.append(diagnostics)

    fund_returns = pd.concat(return_parts, ignore_index=True)
    fund_weights = pd.concat(weight_parts, ignore_index=True)
    diagnostics = pd.concat(diagnostic_parts, ignore_index=True)
    metrics = calculate_metrics(
        fund_returns,
        fund_weights,
        specs,
    )
    design = pd.DataFrame(design_rows)
    fact_sheet = make_fact_sheet_summary(metrics)
    latest = latest_holdings(fund_weights)
    return {
        "fund_returns": fund_returns,
        "fund_weights": fund_weights,
        "performance_metrics": metrics,
        "fund_backtest_design": design,
        "fund_optimizer_diagnostics": diagnostics,
        "fund_latest_holdings": latest,
        "fund_fact_sheet_summary": fact_sheet,
    }


def fund_specs() -> list[FundSpec]:
    """Return the stable nine-fund universe."""

    families = [
        ("equity", "Equity", 252, "equity trading calendar"),
        ("crypto", "Crypto", 365, "native seven-day calendar"),
        ("combined", "Combined", 252, "equity trading calendar with same-date native crypto returns"),
    ]
    method_ids = {
        METHOD_EQUAL_WEIGHT: "equal_weight",
        METHOD_MIN_VARIANCE: "minimum_variance",
        METHOD_RISK_PARITY: "risk_parity",
    }
    specs: list[FundSpec] = []
    for family_id, family_name, annualisation, calendar in families:
        for method in METHODS:
            specs.append(
                FundSpec(
                    fund_id=f"{family_id}_{method_ids[method]}",
                    fund_name=f"{family_name} {method}",
                    asset_family=family_name,
                    method=method,
                    annualisation_factor=annualisation,
                    calendar=calendar,
                )
            )
    return specs


def calculate_metrics(
    fund_returns: pd.DataFrame,
    fund_weights: pd.DataFrame,
    specs: list[FundSpec],
) -> pd.DataFrame:
    """Calculate required gross and net performance metrics for each fund."""

    rows: list[dict[str, object]] = []
    for spec in specs:
        group = fund_returns.loc[fund_returns["fund_id"].eq(spec.fund_id)].sort_values("date")
        weights = fund_weights.loc[fund_weights["fund_id"].eq(spec.fund_id)]
        net = group["net_return"].astype(float)
        gross = group["gross_return"].astype(float)
        latest = weights.loc[weights["is_latest_rebalance"]]
        rows.append(
            {
                "fund_id": spec.fund_id,
                "fund_name": spec.fund_name,
                "asset_family": spec.asset_family,
                "method": spec.method,
                "first_live_date": group["date"].min(),
                "end_date": group["date"].max(),
                "number_of_observations": len(group),
                "annualisation_factor": spec.annualisation_factor,
                "risk_free_rate": RISK_FREE_RATE,
                "transaction_cost_rate": TRANSACTION_COST_RATE,
                "cumulative_return_gross": float(group["gross_wealth"].iloc[-1] - 1.0),
                "cumulative_return_net": float(group["net_wealth"].iloc[-1] - 1.0),
                "annualised_return_gross": _geometric_annualised_return(gross, spec.annualisation_factor),
                "annualised_return_net": _geometric_annualised_return(net, spec.annualisation_factor),
                "annualised_volatility_gross": _annualised_volatility(gross, spec.annualisation_factor),
                "annualised_volatility_net": _annualised_volatility(net, spec.annualisation_factor),
                "Sharpe_gross": _sharpe(gross, spec.annualisation_factor),
                "Sharpe_net": _sharpe(net, spec.annualisation_factor),
                "maximum_drawdown_net": float(group["net_drawdown"].min()),
                "average_rebalance_turnover": float(group.loc[group["rebalance_flag"], "turnover"].mean()),
                "total_rebalance_turnover": float(group["turnover"].sum()),
                "total_transaction_cost": float(group["transaction_cost"].sum()),
                "number_of_rebalances": int(group["rebalance_flag"].sum()),
                "current_number_of_holdings": int(latest["target_weight"].gt(1e-10).sum()),
                "largest_current_weight": float(latest["target_weight"].max()),
            }
        )
    return pd.DataFrame(rows)


def performance_metrics(daily_returns: pd.Series, periods_per_year: int = 252) -> dict:
    """Backward-compatible single-return-series metrics helper."""

    returns = pd.Series(daily_returns, dtype=float).dropna()
    wealth = (1.0 + returns).cumprod()
    drawdown = wealth / wealth.cummax() - 1.0
    return {
        "annualised_return": _geometric_annualised_return(returns, periods_per_year),
        "annualised_volatility": _annualised_volatility(returns, periods_per_year),
        "Sharpe": _sharpe(returns, periods_per_year),
        "maximum_drawdown": float(drawdown.min()),
    }


def latest_holdings(fund_weights: pd.DataFrame) -> pd.DataFrame:
    """Return latest target holdings for each fund."""

    return (
        fund_weights.loc[fund_weights["is_latest_rebalance"]]
        .sort_values(["fund_id", "target_weight", "asset"], ascending=[True, False, True])
        .reset_index(drop=True)
    )


def make_fact_sheet_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    """Compact app/report-readable fund fact sheet table."""

    columns = [
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "first_live_date",
        "end_date",
        "annualised_return_net",
        "annualised_volatility_net",
        "Sharpe_net",
        "maximum_drawdown_net",
        "average_rebalance_turnover",
        "total_transaction_cost",
        "current_number_of_holdings",
        "largest_current_weight",
    ]
    return metrics[columns].copy()


def _prepare_asset_metadata(
    assets: list[str],
    asset_family: str,
    metadata: pd.DataFrame | None,
) -> pd.DataFrame:
    if metadata is None:
        asset_class = "Crypto" if asset_family == "Crypto" else "Equity"
        return pd.DataFrame(
            {"asset": assets, "asset_class": asset_class, "sector": pd.NA}
        ).set_index("asset")
    required = {"asset", "asset_class", "sector"}
    missing = required.difference(metadata.columns)
    if missing:
        raise ValueError(f"asset metadata missing columns: {sorted(missing)}")
    result = metadata.copy()
    result["asset"] = result["asset"].astype(str)
    result = result.drop_duplicates("asset").set_index("asset")
    missing_assets = sorted(set(assets).difference(result.index))
    if missing_assets:
        raise ValueError(f"asset metadata missing assets: {missing_assets[:5]}")
    return result.loc[assets]


def _normalise_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    weights = np.where(np.abs(weights) < 1e-14, 0.0, weights)
    total = float(weights.sum())
    if not np.isfinite(total) or abs(total) < 1e-14:
        raise ValueError("weights cannot be normalised")
    return weights / total


def _weights_valid(weights: np.ndarray, max_weight: float) -> bool:
    return bool(
        np.isfinite(weights).all()
        and abs(float(weights.sum()) - 1.0) <= 1e-8
        and float(weights.min()) >= -1e-8
        and float(weights.max()) <= max_weight + 1e-8
    )


def _check_cap_feasible(n_assets: int, max_weight: float) -> None:
    if n_assets * max_weight < 1.0 - 1e-12:
        raise ValueError(
            f"max weight cap {max_weight:.2%} is infeasible for {n_assets} assets"
        )


def _geometric_annualised_return(returns: pd.Series, annualisation_factor: int) -> float:
    values = pd.Series(returns, dtype=float).dropna()
    if values.empty:
        return np.nan
    cumulative = float(np.prod(1.0 + values))
    return cumulative ** (annualisation_factor / len(values)) - 1.0


def _annualised_volatility(returns: pd.Series, annualisation_factor: int) -> float:
    values = pd.Series(returns, dtype=float).dropna()
    if len(values) < 2:
        return np.nan
    return float(values.std(ddof=1) * sqrt(annualisation_factor))


def _sharpe(returns: pd.Series, annualisation_factor: int) -> float:
    values = pd.Series(returns, dtype=float).dropna()
    if len(values) < 2:
        return np.nan
    volatility = float(values.std(ddof=1))
    if volatility == 0:
        return np.nan
    return float(values.mean() / volatility * sqrt(annualisation_factor))
