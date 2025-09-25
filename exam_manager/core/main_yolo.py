import os
import cv2
import numpy as np
import logging
from ultralytics import YOLO

from exam_manager.ui.exam_config import ExamConfig



class YOLOZoneDetector:
    def __init__(self, model_path: str, confidence: float = 0.5):
        self.model = None
        self.confidence = confidence
        try:
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
                print(f"YOLO zone detection model loaded from {model_path}")
            else:
                logging.warning(f"YOLO model not found at {model_path}")
        except Exception as e:
            logging.error(f"Failed to load YOLO model: {e}")
            
    def is_available(self) -> bool:
        return self.model is not None
    
    def detect_grading_zone(self, page_image: np.ndarray, cfg: ExamConfig) -> tuple:
        """
        Detect the grading zone (checkbox area) in the page
        Returns (zone_image, zone_coords) where zone_coords is (x, y, w, h)
        Returns (None, None) if detection fails
        """
        if not self.is_available():
            return None, None
            
        try:
            results = self.model(page_image, conf=self.confidence)
            
            best_detection = None
            best_confidence = 0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        conf = float(box.conf[0].cpu().numpy())
                        if conf > best_confidence:
                            best_confidence = conf
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            best_detection = (int(x1), int(y1), int(x2-x1), int(y2-y1), conf)
                            print(best_detection)
            
            if best_detection is None:
                logging.warning("No grading zone detected by YOLO")
                return None, None
            
            x, y, w, h, conf = best_detection
            
            # Expand the detected zone slightly to ensure we don't miss edges
            expand = cfg.zone_expansion_factor
            img_h, img_w = page_image.shape[:2]
            
            x_exp = max(0, int(x - w * expand))
            y_exp = max(0, int(y - h * expand))
            w_exp = min(img_w - x_exp, int(w * (1 + 2 * expand)))
            h_exp = min(img_h - y_exp, int(h * (1 + 2 * expand)))
            
            # Crop the zone from the original image
            zone_image = page_image[y_exp:y_exp+h_exp, x_exp:x_exp+w_exp]
            zone_coords = (x_exp, y_exp, w_exp, h_exp)

            if zone_image is not None:
                print(f"[DEBUG] Zone crop shape: {zone_image.shape}, coords={zone_coords}")

            
            logging.info(f"Grading zone detected with confidence {conf:.2f} at ({x_exp}, {y_exp}, {w_exp}, {h_exp})")
            return zone_image, zone_coords
            
        except Exception as e:
            logging.error(f"YOLO zone detection failed: {e}")
            return None, None
        
