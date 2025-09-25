# Exam manager

A Python tool for securely managing student exam papers.  
It encrypts student information with **AES/Fernet**, encodes it into **QR codes**, and embeds them into exams.  
Later, it processes scanned PDFs to extract the QR code, decrypt the data, and perform grading using automated checkbox detection.

## ✨ Features
- 🔒 **Encryption & QR generation**: Encrypts sensitive student info (ID, name, etc.) with AES/Fernet and encodes it into a QR code.
- 📄 **PDF processing**: Converts PDF exam files into images for analysis.
- 🖼️ **QR detection & decoding**: Extracts the QR from the first page and decrypts the student info.
- ✅ **Grading automation**: Uses YOLO-based checkbox detection (eg `bon/moyen/non`) to classify answers and compute final grades.
- 🖥️ **GUI**: User-friendly interface built with PyQt5.

## 📦 Requirements
Dependencies are managed in `pyproject.toml` (modern) .  
Main libraries used:
- PyQt5
- OpenCV
- NumPy
- Pillow
- pdf2image
- cryptography
- qrcode
- ultralytics (YOLO)
- torch
- zxing-cpp

Install everything with:
```bash
pip install .
