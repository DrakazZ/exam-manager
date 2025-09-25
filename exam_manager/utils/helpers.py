import cv2
import numpy as np
from PIL import Image
from PyQt5.QtGui import QPixmap
from io import BytesIO

def pil_to_cv(img_pil: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

def cv_to_qpixmap(img_cv: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    buf = BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    pm = QPixmap()
    pm.loadFromData(buf.read())
    return pm



def crop_qr_region(page_bgr: np.ndarray) -> np.ndarray:
    # assume QR always in top-right corner
    x, y, w, h = 1363, 78, 217, 217
    qr_crop = page_bgr[y:y+h, x:x+w]
    cv2.imwrite("debug_qr_crop.png", qr_crop)  # debug save
    return qr_crop
