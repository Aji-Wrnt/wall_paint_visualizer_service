import cv2
import numpy as np

def hex_to_bgr(hex_str: str) -> tuple:
  
    # Konversi string HEX (#RRGGBB) ke format tuple BGR OpenCV.
    # Contoh: '#FF5733' -> (51, 87, 255)

    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        raise ValueError("Format HEX tidak valid. Gunakan format 6 karakter seperti #FF5733")
    
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (b, g, r)

def apply_realistic_color(image_bgr: np.ndarray, mask: np.ndarray, target_hex: str) -> np.ndarray:
    
    # Menerapkan warna baru pada area mask secara realistis.
    # Mempertahankan channel L (Luminance) untuk menjaga detail tekstur, highlight,
    # dan bayangan alami, lalu mengganti channel A dan B (Chrominance).
   
    # 1. Konversi warna target HEX -> BGR -> LAB
    target_bgr = hex_to_bgr(target_hex)
    target_pixel = np.uint8([[list(target_bgr)]])
    target_lab = cv2.cvtColor(target_pixel, cv2.COLOR_BGR2LAB)[0][0]
    _, target_a, target_b = target_lab

    # 2. Konversi citra input ke ruang warna LAB
    img_lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(img_lab)

    # 3. Feathering (Anti-Aliasing) pada tepian mask
    # Menggunakan Gaussian Blur agar batas antar objek/warna tidak kaku (jagged edges)
    mask_soft = cv2.GaussianBlur(mask, (7, 7), 0)
    alpha = (mask_soft / 255.0).astype(np.float32)

    # 4. Modifikasi channel warna A dan B secara proporsional sesuai alpha mask
    new_a = (a_channel * (1.0 - alpha) + target_a * alpha).astype(np.uint8)
    new_b = (b_channel * (1.0 - alpha) + target_b * alpha).astype(np.uint8)

    # 5. Gabungkan kembali channel LAB
    result_lab = cv2.merge([l_channel, new_a, new_b])
    
    # 6. Konversi kembali ke format BGR
    result_bgr = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)
    return result_bgr