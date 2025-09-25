import os
import json
from cryptography.fernet import Fernet
import qrcode




def generate_qr(name, student_id, student_class, university, key):
        fernet = Fernet(key)
        encrypted_name = fernet.encrypt(name.encode()).decode()
        encrypted_id = fernet.encrypt(student_id.encode()).decode()

        student_data = {
            "enc_name": encrypted_name,
            "enc_id": encrypted_id,
            "class": student_class,
            "university": university,
        }
        json_string = json.dumps(student_data)

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=8, border=2)
        qr.add_data(json_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        out_dir = os.path.join(os.path.expanduser("~"), "qrdb")
        os.makedirs(out_dir, exist_ok=True)
        filename = os.path.join(out_dir, f"qr_{encrypted_name}.png")
        img.save(filename)

        return img       