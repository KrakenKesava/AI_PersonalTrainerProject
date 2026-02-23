def analyse_pullup(elbow_angle, direction):
    """
    direction:
    0 → pulling up
    1 → going down
    """

    # =========================
    # TOP PHASE (pull)
    # =========================
    if direction == 0:
        if elbow_angle <= 45:
            return {
                "formCorrect": True,
                "feedback": ["Good pull-up"]
            }
        else:
            return {
                "formCorrect": False,
                "feedback": ["Pull higher"]
            }

    # =========================
    # BOTTOM PHASE (extend)
    # =========================
    if direction == 1:
        if elbow_angle >= 150:
            return {
                "formCorrect": True,
                "feedback": ["Full extension correct"]
            }
        else:
            return {
                "formCorrect": False,
                "feedback": ["Extend fully"]
            }

    # =========================
    # FALLBACK (never empty)
    # =========================
    return {
        "formCorrect": True,
        "feedback": ["Keep going..."]
    }