from PyQt5.QtWidgets import (
    QLineEdit, QCheckBox, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox
)


# Local imports
from .exam_config import ExamConfig, CONFIG_PATH



class SettingsDialog(QDialog):
    def __init__(self, cfg: ExamConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exam Settings")
        self.cfg = cfg

        form = QFormLayout(self)

        # Existing settings
        self.spin_options = QSpinBox()
        self.spin_options.setRange(1, 10)
        self.spin_options.setValue(cfg.options_per_question)
        form.addRow("Options per question", self.spin_options)

        self.input_labels = QLineEdit(",".join(cfg.option_labels))
        form.addRow("Option labels (comma-separated)", self.input_labels)

        # YOLO settings
        self.chk_yolo = QCheckBox("Use YOLO zone detection")
        self.chk_yolo.setChecked(cfg.use_yolo_zone_detection)
        form.addRow(self.chk_yolo)

        self.input_yolo_path = QLineEdit(cfg.yolo_model_path)
        form.addRow("YOLO model path", self.input_yolo_path)

        self.spin_confidence = QSpinBox()
        self.spin_confidence.setRange(1, 99)
        self.spin_confidence.setValue(int(cfg.yolo_confidence * 100))
        self.spin_confidence.setSuffix("%")
        form.addRow("YOLO confidence threshold", self.spin_confidence)

        # Other settings
        self.chk_adaptive = QCheckBox("Use adaptive checkbox classification")
        self.chk_adaptive.setChecked(cfg.use_adaptive_threshold)
        form.addRow(self.chk_adaptive)

        self.chk_fallback = QCheckBox("Fallback to full page if YOLO fails")
        self.chk_fallback.setChecked(cfg.fallback_to_full_page)
        form.addRow(self.chk_fallback)

        self.btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        form.addRow(self.btns)

    def accept(self):
        self.cfg.options_per_question = int(self.spin_options.value())
        labels = [s.strip() for s in self.input_labels.text().split(',') if s.strip()]
        if labels:
            self.cfg.option_labels = labels
        
        self.cfg.use_yolo_zone_detection = self.chk_yolo.isChecked()
        self.cfg.yolo_model_path = self.input_yolo_path.text().strip()
        self.cfg.yolo_confidence = self.spin_confidence.value() / 100.0
        self.cfg.use_adaptive_threshold = self.chk_adaptive.isChecked()
        self.cfg.fallback_to_full_page = self.chk_fallback.isChecked()
        
        self.cfg.to_json(CONFIG_PATH)
        super().accept()
