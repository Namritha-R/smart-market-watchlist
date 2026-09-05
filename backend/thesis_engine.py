def evaluate_thesis(thesis_type, current_value, threshold):
    if thesis_type == "growth":
        if current_value >= threshold:
            return {
                "status": "VALID",
                "reason": (
                    f"Growth of {current_value:.1f}% meets "
                    f"the {threshold:.1f}% thesis threshold."
                ),
            }

        return {
            "status": "INVALID",
            "reason": (
                f"Growth has fallen to {current_value:.1f}%, "
                f"below your {threshold:.1f}% thesis threshold."
            ),
        }

    return {
        "status": "UNKNOWN",
        "reason": "Unsupported thesis type.",
    }