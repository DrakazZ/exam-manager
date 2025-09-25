# exam_manager/processing/exam_processor.py

import logging
import os
import cv2
import json
import numpy as np
import zxingcpp
from cryptography.fernet import Fernet

from exam_manager.utils.helpers import crop_qr_region
from exam_manager.core.page_yolo_pipline import process_exam_page_with_zone_detection
from exam_manager.core.main_yolo import YOLOZoneDetector
from exam_manager.utils.deskew_image import deskew_image
from exam_manager.core.grading_system import grade_exam, validate_detection_results


def decode_qr_from_first_page(page_bgr: np.ndarray, key: bytes) -> dict:
    """
    Extract and decode QR from the first page using static cropping + ZXing.
    """
    # --- Step 1: Crop QR region
    deskewed = deskew_image(page_bgr)
    qr_crop = crop_qr_region(deskewed)


    # --- Step 2: Convert to grayscale for ZXing
    rgb = cv2.cvtColor(qr_crop, cv2.COLOR_BGR2RGB)


    # --- Step 3: Decode
    data = zxingcpp.read_barcode(rgb)
    if not data:
        raise ValueError("QR decode failed with ZXing")

    if isinstance(data, (list, tuple)):
        data = data[0]

    print("DEBUG - Decoded text:", data.text)  

    try:
        payload = json.loads(data.text)
    except json.JSONDecodeError:
        raise ValueError("Decoded QR is not valid JSON")

    # --- Step 4: Decrypt
    key = key[0]
    print("Using decryption key:", key)
    f = Fernet(key)
    decrypted = {
        "name": f.decrypt(payload["enc_name"].encode()).decode(),
        "id": f.decrypt(payload["enc_id"].encode()).decode(),
        "class": payload.get("class", ""),
        "university": payload.get("university", ""),
    }
    print("Decrypted name:", f.decrypt(payload["enc_name"].encode()).decode())
    print("Decrypted id:", f.decrypt(payload["enc_id"].encode()).decode())
    print("Class:", payload.get("class", ""))
    print("University:", payload.get("university", ""))
    return decrypted


def process_pdf(pdf_path: str, cfg, zone_detector, key: bytes) -> dict:
    """
    Full pipeline: convert PDF → extract QR → detect checkboxes → grade.
    Returns a summary dict (to be saved or displayed by the UI).
    """
    from exam_manager.utils.pdf import convert_pdf_to_images  # lazy import to avoid circulars

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    image_paths = convert_pdf_to_images(pdf_path)
    if not image_paths:
        raise RuntimeError("Failed to convert PDF to images.")

    # --- First page: QR
    first_path = image_paths[0]
    first_bgr = cv2.imread(first_path)
    if first_bgr is None:
        raise RuntimeError("Failed to read first page image.")

    try:
        student = decode_qr_from_first_page(first_bgr, key)
        print("Decoded student info:", student)
    except Exception as e:
        student = {
            "name": "Unknown",
            "id": "0000",
            "class": "N/A",
            "university": "N/A",
            "error": str(e)
        }

    # --- Remaining pages: checkboxes
    all_results = []
    q_counter = 1
    vis_paths = []

    for p in image_paths:
        page_bgr = cv2.imread(p)
        if page_bgr is None:
            continue

        results, vis, validation = process_exam_page_with_zone_detection(
            page_bgr, cfg, zone_detector, q_counter
        )
        all_results.extend(results)
        q_counter += len(results)

        vis_out = p.replace(".png", "_vis.png")
        cv2.imwrite(vis_out, vis)
        vis_paths.append(vis_out)

    # --- Summarize + grade
    validation = validate_detection_results(all_results)
    grading = grade_exam(all_results, cfg)
    summary = {
        "student": student,
        "results": all_results,
        "total_questions": len(all_results),
        "validation": validation,
        "grading": grading,
        "visualizations": vis_paths,
    }


    out_json = os.path.splitext(pdf_path)[0] + "_grades.json"
    with open(out_json, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, indent=2, ensure_ascii=False))

    return summary
