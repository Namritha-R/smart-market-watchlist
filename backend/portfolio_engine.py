def calculate_portfolio_drift(position):
    actual = position["actual_weight"]
    target = position["target_weight"]

    drift = actual - target

    if abs(drift) >= 5:
        status = "WORTH_ATTENTION"
        reason = (
            f"{position['symbol']} is {abs(drift):.2f} percentage points "
            f"{'above' if drift > 0 else 'below'} its target allocation."
        )
    else:
        status = "NORMAL"
        reason = (
            f"{position['symbol']} is within 5 percentage points "
            f"of its target allocation."
        )

    return {
        "symbol": position["symbol"],
        "target_weight": target,
        "actual_weight": actual,
        "drift": round(drift, 2),
        "status": status,
        "reason": reason,
    }