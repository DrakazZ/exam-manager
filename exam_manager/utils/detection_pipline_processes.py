import cv2
import numpy as np

from exam_manager.ui.exam_config import ExamConfig

def process_checkbox_rows(rows: list, zone_image: np.ndarray, cfg: ExamConfig, q_start_index: int) -> list:
    results = []
    labels = cfg.option_labels
    if len(labels) != cfg.options_per_question:
        labels = [f"opt_{i}" for i in range(cfg.options_per_question)]

    q_idx = q_start_index
    for row in rows:
        # keep only expected options
        row_sorted = row[:cfg.options_per_question]

        best_label = None
        best_score = -1.0
        best_checked = False

        for j, (x, y, w, h) in enumerate(row_sorted):
            roi = zone_image[y:y+h, x:x+w]
            checked, score, dbg = score_checkbox_robust(roi, cfg)

            if cfg.debug_cv and q_idx <= cfg.debug_dump_n:
                prefix = f"dbg/Q{q_idx:02d}_{labels[j]}_{x}-{y}-{w}x{h}"
                imgs = dbg.get("imgs", {})
                _dump_checkbox_debug(prefix, imgs)
                print(f"[DBG][Q{q_idx} {labels[j]}] wh=({w}x{h}) "
                      f"inner={dbg.get('inner_ratio',-1):.3f} "
                      f"edge={dbg.get('edge_ratio',-1):.3f} "
                      f"score={dbg.get('score',-1):.3f} checked={checked}")

            if score > best_score:
                best_score = score
                best_label = labels[j] if checked else None
                best_checked = checked

        # final decision for this question
        results.append({
            "question": q_idx,
            "grade": best_label if best_checked else "missing"
        })
        q_idx += 1
    return results


def _dump_checkbox_debug(prefix: str, img_dict: dict):
    # Saves a few stages to disk when debugging
    try:
        for k, v in img_dict.items():
            if isinstance(v, np.ndarray):
                cv2.imwrite(f"{prefix}_{k}.png", v)
    except Exception:
        pass


def score_checkbox_robust(roi_bgr: np.ndarray, cfg) -> tuple[bool, float, dict]:
    """
    Returns (is_checked, score, dbg)
    - score ~ inner_ink_ratio*1.0 + edge_density*0.5 (clamped to [0,1])
    - dbg contains all intermediate numbers for logging
    """
    dbg = {}
    if roi_bgr is None or roi_bgr.size == 0:
        return False, 0.0, {"err": "empty_roi"}

    # --- grayscale & denoise
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # --- binarize (invert so "ink" is white=255)
    _, th_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if cfg.use_adaptive_threshold:
        th_adap = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        th = cv2.bitwise_or(th_otsu, th_adap)
    else:
        th = th_otsu

    # --- crop inside to remove the frame
    h, w = th.shape[:2]
    pad = max(2, int(min(w, h) * cfg.inner_crop_pct))
    y0, y1 = pad, max(pad + 1, h - pad)
    x0, x1 = pad, max(pad + 1, w - pad)
    inner = th[y0:y1, x0:x1]
    if inner.size == 0:
        inner = th

    # (optional) light clean-up to kill tiny specks
    kernel = np.ones((2, 2), np.uint8)
    inner_clean = cv2.morphologyEx(inner, cv2.MORPH_OPEN, kernel, iterations=1)

    # --- metrics
    inner_ratio = float(np.count_nonzero(inner_clean == 255)) / float(inner_clean.size)
    edges = cv2.Canny(inner_clean, 50, 150)
    edge_ratio = float(np.count_nonzero(edges > 0)) / float(edges.size)

    # --- decision
    # Strong positive if there’s a lot of ink inside.
    strong = inner_ratio >= cfg.strong_inner_on_ratio
    # Otherwise combine ink + edges
    score = max(0.0, min(1.0, inner_ratio * 1.0 + edge_ratio * 0.5))
    weak = (inner_ratio >= cfg.min_inner_on_ratio and edge_ratio >= cfg.edge_density_thr)
    is_checked = bool(strong or (score >= cfg.min_vote_score) or weak)

    # --- debug pack
    dbg.update(dict(
        w=w, h=h, pad=pad,
        inner_ratio=inner_ratio, edge_ratio=edge_ratio, score=score,
    ))
    if getattr(cfg, "debug_cv", False):
        dbg_imgs = {
            "roi": roi_bgr,
            "gray": gray,
            "th_otsu": th_otsu,
            "th": th,
            "inner": inner,
            "inner_clean": inner_clean,
            "edges": edges,
        }
        dbg["imgs"] = dbg_imgs
    return is_checked, score, dbg

def find_shapes_in_zone(zone_bgr: np.ndarray, cfg: ExamConfig) -> list:
    gray = cv2.cvtColor(zone_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []


    print(f"[DEBUG] Total contours found: {len(contours)}")
    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)

        #if w < 5 or h < 5:
        if w < 15 or h < 15 or w > 60 or h > 60:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        area = cv2.contourArea(cnt)
        circ = 4 * np.pi * area / (peri * peri + 1e-5)

        keep = False


        if (len(approx) == 4) or (circ > 0.7):
            keep = True

        if keep:
            boxes.append((x, y, w, h))


    boxes.sort(key=lambda b: (b[1], b[0]))



    filtered_boxes = []
    boxes_sorted = sorted(boxes, key=lambda b: (b[1], b[0]))  # sort by y, then x

    for (x,y,w,h) in boxes_sorted:
        too_close = False
        for (fx,fy,fw,fh) in filtered_boxes:
            if abs(x-fx) < 5 and abs(y-fy) < 5:
                # smaller box inside bigger box, skip it
                if w*h < fw*fh:
                    too_close = True
        if not too_close:
            filtered_boxes.append((x,y,w,h))


    return filtered_boxes


def group_shapes_into_questions(candidates: list, cfg: ExamConfig) -> list:
    if not candidates:
        return []

    rows = []
    N = cfg.options_per_question
    temp = []

    for b in candidates:
        temp.append(b)
        if len(temp) == N:
            xs = [bb[0] for bb in temp]
            ys = [bb[1] for bb in temp]
            if np.std(xs) > np.std(ys):
                temp.sort(key=lambda bb: bb[0])  # horizontal
            else:
                temp.sort(key=lambda bb: bb[1])  # vertical
            rows.append(temp)
            temp = []

    return rows