import math

# Database Warna Cat Dasar Toko Bangunan (Standard Pigments & Ready Mix)
PIGMENTS_DATABASE = {
    "Base White (Putih Dasar)": {"c": 0.0, "m": 0.0, "y": 0.0, "k": 0.0, "hex": "#FFFFFF"},
    "Super Black (Hitam)": {"c": 0.0, "m": 0.0, "y": 0.0, "k": 1.0, "hex": "#000000"},
    "Primary Cyan (Biru Tinting)": {"c": 1.0, "m": 0.0, "y": 0.0, "k": 0.0, "hex": "#0099FF"},
    "Primary Magenta (Merah Tinting)": {"c": 0.0, "m": 1.0, "y": 0.0, "k": 0.0, "hex": "#E60067"},
    "Bright Yellow (Kuning Tinting)": {"c": 0.0, "m": 0.0, "y": 1.0, "k": 0.0, "hex": "#FFD700"},
    "Chocolate Brown (Cokelat)": {"c": 0.0, "m": 0.5, "y": 0.8, "k": 0.4, "hex": "#8B4513"},
}

def hex_to_cmyk(hex_str: str) -> tuple:
    
    # Konversi warna layar HEX (RGB/Aditif) ke CMYK (Subtraktif pigmen fisik).
    
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0

    k = 1.0 - max(r, g, b)
    if k == 1.0:
        return 0.0, 0.0, 0.0, 1.0

    c = (1.0 - r - k) / (1.0 - k)
    m = (1.0 - g - k) / (1.0 - k)
    y = (1.0 - b - k) / (1.0 - k)
    return round(c, 3), round(m, 3), round(y, 3), round(k, 3)

def generate_paint_recipes(target_hex: str) -> list:
    
    # Menghasilkan 1-3 variasi kombinasi resep racikan cat dari pigmen toko bangunan.
    
    c, m, y, k = hex_to_cmyk(target_hex)
    recipes = []

    # Campuran Tinting Akurat (Base White + Pigmen Primer)
    white_part = max(0.0, 1.0 - (c + m + y + k))
    total_parts = white_part + c + m + y + k
    
    if total_parts > 0:
        recipe_primary = {
            "name": "Kombinasi Tinting Standar (Paling Akurat)",
            "components": []
        }
        if white_part > 0.02:
            recipe_primary["components"].append({"paint": "Base White (Putih Dasar)", "percentage": round((white_part/total_parts)*100, 1)})
        if c > 0.02:
            recipe_primary["components"].append({"paint": "Primary Cyan (Biru Tinting)", "percentage": round((c/total_parts)*100, 1)})
        if m > 0.02:
            recipe_primary["components"].append({"paint": "Primary Magenta (Merah Tinting)", "percentage": round((m/total_parts)*100, 1)})
        if y > 0.02:
            recipe_primary["components"].append({"paint": "Bright Yellow (Kuning Tinting)", "percentage": round((y/total_parts)*100, 1)})
        if k > 0.02:
            recipe_primary["components"].append({"paint": "Super Black (Hitam)", "percentage": round((k/total_parts)*100, 1)})
        recipes.append(recipe_primary)

    # Campuran Sederhana (3 Bahan Utama)
    if len(recipe_primary["components"]) > 3:
        sorted_comps = sorted(recipe_primary["components"], key=lambda x: x["percentage"], reverse=True)[:3]
        sub_total = sum(item["percentage"] for item in sorted_comps)
        recipe_simple = {
            "name": "Kombinasi Praktis (3 Bahan Pokok)",
            "components": [
                {"paint": item["paint"], "percentage": round((item["percentage"] / sub_total) * 100, 1)}
                for item in sorted_comps
            ]
        }
        recipes.append(recipe_simple)

    return recipes

def calculate_wall_materials(box_w_px: int, box_h_px: int, img_w: int, img_h: int) -> dict:
    
    # Estimasi dimensi fisik dan volume cat dinding berdasarkan rasio piksel ke metrik.
    # Rata-rata tinggi ruangan interior standar = 2.8 - 3.0 meter.

    # Estimasi tinggi referensi frame ruangan (asumsi tinggi foto vertikal mencakup ~2.8 meter dinding)
    pixel_per_meter = img_h / 3

    est_width_m = round(box_w_px / pixel_per_meter, 2)
    est_height_m = round(box_h_px / pixel_per_meter, 2)
    est_area_m2 = round(est_width_m * est_height_m, 2)

    # Standar pengecatan: 10 m2 / Liter untuk 2 lapis pengecatan + 5% cadangan untuk buffer
    coverage_per_liter = 10.0
    coats = 2
    waste_margin = 1.05

    total_liters = round(((est_area_m2 * coats) / coverage_per_liter) * waste_margin, 2)
    total_ml = int(total_liters * 1000)

    # Rekomendasi kemasan kaleng
    galon_2_5L = math.ceil(total_liters / 2.5)

    return {
        "estimated_width_m": est_width_m,
        "estimated_height_m": est_height_m,
        "estimated_area_m2": est_area_m2,
        "paint_needed_ml": total_ml,
        "paint_needed_liters": total_liters,
        "recommended_cans": f"{galon_2_5L} Galon (2.5 Liter)" if total_liters < 20 else f"{math.ceil(total_liters/20)} Pail (20 Liter)"
    }