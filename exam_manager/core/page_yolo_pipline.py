import cv2
import numpy as np
import logging

from exam_manager.ui.exam_config import ExamConfig
from exam_manager.utils.deskew_image import deskew_image
from exam_manager.core.main_yolo import YOLOZoneDetector
from exam_manager.utils.detection_pipline_processes import (
    find_shapes_in_zone, group_shapes_into_questions, process_checkbox_rows
)
from exam_manager.core.grading_system import validate_detection_results

def process_exam_page_with_zone_detection(page_bgr: np.ndarray, cfg: ExamConfig, 
                                        zone_detector: YOLOZoneDetector, 
                                        q_start_index: int = 1):
    """
    Process exam page using YOLO to detect grading zone, then OpenCV for checkboxes
    """
    
    if cfg.enable_deskew:
        page_bgr = deskew_image(page_bgr)
    
    try:
        zone_image = None
        zone_coords = None
        processing_area = page_bgr  # Default to full page
        
        # Try YOLO zone detection first
        if cfg.use_yolo_zone_detection and zone_detector.is_available():
            zone_image, zone_coords = zone_detector.detect_grading_zone(page_bgr, cfg)

            if zone_image is not None and zone_coords is not None:
                processing_area = zone_image
                logging.info("Using YOLO-detected zone for checkbox processing")
            else:
                logging.warning("No YOLO zone detected → skipping page")
                return [], page_bgr, {"warning": "Page skipped (no zone detected)"}
                
        # Process checkboxes in the detected/selected area
        candidates = find_shapes_in_zone(processing_area, cfg)
        if not candidates:
            return [], page_bgr, {"error": "No checkbox candidates found in processing area"}

        rows = group_shapes_into_questions(candidates, cfg)
        if not rows:
            return [], page_bgr, {"error": "No valid checkbox rows detected"}

        # Process detected checkboxes
        results = process_checkbox_rows(rows, processing_area, cfg, q_start_index)
        
        validation = validate_detection_results(results)
        return results, page_bgr, validation

    except Exception as e:
        logging.error(f"Page processing failed: {e}")
        return [], page_bgr, {"error": f"Processing failed: {str(e)}"}

