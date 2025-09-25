import os
import tempfile
from PyQt5.QtWidgets import QFileDialog
from pdf2image import convert_from_path


def browse_pdf_file(parent_widget=None) -> str | None:
    file_path, _ = QFileDialog.getOpenFileName(parent_widget, "Select PDF File", "", "PDF Files (*.pdf)")
    if file_path:
        return file_path if file_path else None

def convert_pdf_to_images(pdf_path: str) -> list:
    pages_pil = convert_from_path(pdf_path)
    out_dir = tempfile.mkdtemp(prefix="exam_pages_")
    image_paths = []
    for i, img in enumerate(pages_pil, start=1):
        path = os.path.join(out_dir, f"page_{i}.png")
        img.save(path)
        image_paths.append(path)
    return image_paths