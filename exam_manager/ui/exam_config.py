import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exam_config.json")

class ExamConfig:
    def __init__(self):
        self.options_per_question = 3      # default number of options per question
        self.option_labels = ["bon", "moyen", "non"]  # labels, highest→lowest
        self.use_adaptive_threshold = True # robust mode (voting of 3 methods)
        self.black_ratio_threshold = 0.22  # used by simple classifier
        self.qr_crop_region = None         # (x,y,w,h) or None
        self.enable_deskew = False         # optional

        # YOLO zone detection settings
        self.use_yolo_zone_detection = True
        self.yolo_model_path = "W:/stage25/model/runs/detect/checkbox_optimized/weights/best.pt"
        self.yolo_confidence = 0.5
        self.zone_expansion_factor = 0.05  # Expand detected zone by 5%
        self.fallback_to_full_page = True  # If YOLO fails, process full page
        
        # instance attributes
        self.debug_cv: bool = True
        self.debug_dump_n: int = 24          # dump first N checkboxes for inspection
        self.inner_crop_pct: float = 0.18     # % of min(w,h) trimmed on each side to skip the frame
        self.min_inner_on_ratio: float = 0.06 # ink ratio that suggests a mark is present
        self.strong_inner_on_ratio: float = 0.12
        self.edge_density_thr: float = 0.06
        self.min_vote_score: float = 0.12     # combined score threshold
        self.use_adaptive_threshold: bool = True


    @classmethod
    def from_json(cls, json_path: str):
        cfg = cls()
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
        return cfg

    def to_json(self, json_path: str):
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)


