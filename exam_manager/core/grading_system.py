from exam_manager.ui.exam_config import ExamConfig   

def validate_detection_results(results: list) -> dict:
    validation = {
        "total_questions": len(results),
        "answered_questions": len([r for r in results if r.get("grade") not in (None, "missing")]),
        "warnings": []
    }
    if not results:
        validation["warnings"].append("No questions detected.")
        return validation

    counts = {}
    for r in results:
        g = r.get("grade", "missing")
        counts[g] = counts.get(g, 0) + 1

    if len(counts) == 1 and len(results) > 5:
        validation["warnings"].append("All questions have same answer — possible detection issue.")

    missing_ratio = counts.get("missing", 0) / len(results)
    if missing_ratio > 0.30:
        validation["warnings"].append(f"High missing rate: {missing_ratio:.1%}")

    return validation

def grade_exam(results: list, cfg: ExamConfig) -> dict:
    total_q = len(results)
    if total_q == 0:
        return {"score": 0.0, "letter": "F"}

    labels = cfg.option_labels
    if len(labels) != cfg.options_per_question:
        labels = [f"opt_{i}" for i in range(cfg.options_per_question)]

    points_per_q = 100.0 / total_q
    score = 0.0

    # reverse grading scale so first = worst, last = best
    grading_scale = {
        labels[i]: (len(labels) - 1 - i) / (len(labels) - 1)
        for i in range(len(labels))
    }
    print(f"[DEBUG] Grading scale: {grading_scale}")

    for r in results:
        grade = r.get("grade")
        if not grade or grade == "missing":
            continue
        frac = grading_scale.get(grade, 0.0)
        score += frac * points_per_q
        print(f"[DEBUG] Q{r['question']}: grade={grade}, frac={frac:.2f}, contrib={frac * points_per_q:.2f}")

    percentage = round(score, 2)
    if percentage >= 90: letter = "A"
    elif percentage >= 80: letter = "B"
    elif percentage >= 70: letter = "C"
    elif percentage >= 60: letter = "D"
    elif percentage >= 50: letter = "E"
    else: letter = "F"

    print(f"[DEBUG] Final Score: {percentage}, Letter: {letter}")
    return {"score": percentage, "letter": letter}
