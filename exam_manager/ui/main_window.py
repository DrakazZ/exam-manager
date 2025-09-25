from io import BytesIO
import cv2
from PyQt5.QtWidgets import (
    QTabWidget, QWidget, QLabel, QLineEdit, QPushButton, QMessageBox,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtGui import QPixmap


# Local imports
from .settings_dialog import SettingsDialog
from .exam_config import ExamConfig, CONFIG_PATH
from ..utils.key import load_key
from ..utils.helpers import cv_to_qpixmap
from ..utils.pdf import browse_pdf_file, convert_pdf_to_images
from ..core.qr_encode import generate_qr
from ..core.pdf_processing import process_pdf
from ..core.main_yolo import YOLOZoneDetector


class StudentQRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("exam manager")
        self.resize(600, 400)
        self.cfg = ExamConfig.from_json(CONFIG_PATH)

        # NEW: Initialize YOLO zone detector
        self.zone_detector = YOLOZoneDetector(
        self.cfg.yolo_model_path, 
        self.cfg.yolo_confidence
        )

        self.tabs = QTabWidget()
        self.tabs.addTab(self.add_generation_tab(), "Generate QR Code")
        self.tabs.addTab(self.add_processing_tab(), "Process Exam PDF")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        

    # ---------- tabs ----------
    def add_generation_tab(self):
        tab = QWidget()
    # Inputs
        self.name_input = QLineEdit();  self.name_input.setPlaceholderText("Name")
        self.id_input = QLineEdit();    self.id_input.setPlaceholderText("ID Number")
        self.class_input = QLineEdit(); self.class_input.setPlaceholderText("Class")
        self.university_input = QLineEdit(); self.university_input.setPlaceholderText("University")

        self.generate_button = QPushButton("Generate QR")
        self.generate_button.clicked.connect(self.handle_generate_qr)

        self.qr_label = QLabel("QR/info will appear here.")
        self.qr_label.setMinimumHeight(220)

        self.grade_label = QLabel("info & grade will appear here.")
        self.grade_label.setMinimumHeight(220)

        layout = QVBoxLayout()
        layout.addWidget(self.name_input)
        layout.addWidget(self.id_input)
        layout.addWidget(self.class_input)
        layout.addWidget(self.university_input)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.qr_label)
        tab.setLayout(layout)
        return tab

    def add_processing_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        file_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.browse_button = QPushButton("📁 Browse PDF")
        self.browse_button.clicked.connect(self.on_browse_pdf)
        file_row.addWidget(self.file_input)
        file_row.addWidget(self.browse_button)
        layout.addLayout(file_row)

        buttons_row = QHBoxLayout()
        self.process_button = QPushButton("Process PDF → Decode QR → Grade")
        self.process_button.clicked.connect(self.on_process_pdf)
        self.settings_button = QPushButton("⚙️ Settings")
        self.settings_button.clicked.connect(self.open_settings)
        buttons_row.addWidget(self.process_button)
        buttons_row.addWidget(self.settings_button)
        layout.addLayout(buttons_row)
        layout.addWidget(self.grade_label)

        tab.setLayout(layout)
        return tab

    # ---------- Settings ----------
    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        dlg.exec_()

    # ---------- Key management ----------
    def handle_load_key(self):
        key, message = load_key()
        self.qr_label.setText(message)
        return key

    # ---------- QR generation ----------
    def handle_generate_qr(self):
        key, msg = load_key()
        if not key:
            self.qr_label.setText("❌ No key available")
            return
        self.qr_label.setText(msg)

        img = generate_qr(
            self.name_input.text().strip(),
            self.id_input.text().strip(),
            self.class_input.text().strip(),
            self.university_input.text().strip(),
            key
        )

        buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        pm = QPixmap(); pm.loadFromData(buf.read())
        self.qr_label.setPixmap(pm)
        self.qr_label.setScaledContents(True)

    # ---------- PDF handling ----------
    def on_browse_pdf(self):
        file_path = browse_pdf_file(self)  # pass self as parent so dialog is modal
        if file_path:
            self.file_input.setText(file_path)

    def on_convert_pdf(self):
        pdf_path = self.file_input.text()
        if pdf_path:
            image_paths = convert_pdf_to_images(pdf_path)
            print("Converted images:", image_paths)

    def on_process_pdf(self):
        pdf_path = self.file_input.text().strip()
        if not pdf_path:
            QMessageBox.critical(self, "Error", "Please select a valid PDF file.")
            return

        try:
            summary = process_pdf(pdf_path, self.cfg, self.zone_detector, load_key())
        except Exception as e:
            QMessageBox.critical(self, "Processing Error", str(e))
            return

        # Update GUI
        validation = summary["validation"]
        grading = summary["grading"]
        student = summary["student"]

        self.grade_label.setText(
            f"Student: {student.get('name', 'N/A')} | "
            f"ID: {student.get('id', 'N/A')} | "
            f"Class: {student.get('class', 'N/A')} | "
            f"University: {student.get('university', 'N/A')}\n"
            f"Processed {summary['total_questions']} questions. "
            f"Graded: {validation['answered_questions']} "
            f"Score: {grading['score']}% ({grading['letter']})"
            + ("".join(["⚠ " + w for w in validation.get("warnings", [])]) if validation.get("warnings") else "")
        )


