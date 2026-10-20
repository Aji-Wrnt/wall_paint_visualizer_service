import cv2
import numpy as np

def hex_to_bgr(hex_str: str) -> tuple:
    """
    Konversi string HEX (#RRGGBB) ke format tuple BGR OpenCV (B, G, R).
    Contoh: '#FF5733' -> (51, 87, 255)
    """
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        raise ValueError("Format HEX tidak valid. Gunakan format 6 karakter seperti #FF5733")
    
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (b, g, r)

def apply_realistic_color(
    image_bgr: np.ndarray, 
    mask: np.ndarray, 
    target_hex: str, 
    luminance_influence: float = 0.45
) -> np.ndarray:
    """
    Menerapkan warna baru pada area mask secara realistis dengan ruang warna CIELAB.
    
    Prinsip Fisika & Computer Vision:
    1. Channel L (Luminance) merepresentasikan intensitas cahaya, bayangan alami (shadows), 
       dan tekstur mikroskopis dinding.
    2. Channel A & B (Chrominance) merepresentasikan rona warna hijau-merah dan biru-kuning.
    3. Adaptive Luminance Modulation: Menggeser kecerahan dasar ke arah warna target (warna terang
       meningkatkan L, warna gelap menurunkan L) tanpa meratakan highlight dan bayangan alami.
    4. Morphological Closing & Gaussian Feathering: Menghilangkan lubang noise (pinholes) pada 
       mask FastSAM serta menghaluskan batas tepi (anti-aliasing) agar cat menyatu alami.
    """
    if mask is None or np.sum(mask) == 0:
        return image_bgr

    # 1. Konversi warna target HEX -> BGR -> CIELAB
    target_bgr = hex_to_bgr(target_hex)
    target_pixel = np.uint8([[list(target_bgr)]])
    target_lab = cv2.cvtColor(target_pixel, cv2.COLOR_BGR2LAB)[0][0]
    target_l = float(target_lab[0])
    target_a = float(target_lab[1])
    target_b = float(target_lab[2])

    # 2. Konversi citra input ke ruang warna CIELAB dengan tipe float untuk presisi perhitungan
    img_lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_channel, a_channel, b_channel = cv2.split(img_lab)

    # 3. Mask Pre-processing (Morphological Closing + Soft Gaussian Feathering)
    # Menutup celah kecil pada segmentasi FastSAM
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # Feathering tepian agar transisi warna tidak bergerigi
    mask_soft = cv2.GaussianBlur(mask_clean, (9, 9), 0)
    alpha = (mask_soft / 255.0).astype(np.float32)

    # 4. Adaptive Luminance Modulation (Mempertahankan tekstur & bayangan namun adaptif terhadap target)
    mask_bool = mask_clean > 0
    if np.any(mask_bool):
        orig_mean_l = float(np.mean(l_channel[mask_bool]))
        # Menggeser kecerahan rata-rata menuju target_l sesuai bobot luminance_influence
        target_shift = (target_l - orig_mean_l) * luminance_influence
        new_l = np.clip(l_channel + target_shift, 0, 255)
    else:
        new_l = l_channel

    # 5. Modifikasi channel L, A, dan B secara proporsional sesuai alpha mask
    blended_l = (l_channel * (1.0 - alpha) + new_l * alpha)
    blended_a = (a_channel * (1.0 - alpha) + target_a * alpha)
    blended_b = (b_channel * (1.0 - alpha) + target_b * alpha)

    # 6. Gabungkan kembali channel LAB dan konversi kembali ke BGR
    result_lab = cv2.merge([blended_l, blended_a, blended_b]).astype(np.uint8)
    result_bgr = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)
    return result_bgr
