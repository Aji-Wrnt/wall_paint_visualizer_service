import math

def hex_to_rgb(hex_str: str) -> tuple:
    """Konversi string HEX (#RRGGBB) ke tuple normalisasi float (R, G, B) [0.0 - 1.0]."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        raise ValueError("Format HEX tidak valid. Gunakan format 6 karakter seperti #FF5733")
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return r, g, b

def generate_paint_recipes(target_hex: str) -> list:
    """
    Menghasilkan formula racikan cat fisik (Architectural Tinting Formula).
    
    Prinsip Fisika Tinting Mesin Cat (Toko Bangunan):
    1. Cat dinding menggunakan basis Base White / Base Clear sebagai komponen utama volume (30% - 92%).
    2. Pigmen warna pekat (Colorants: Cyan, Magenta, Yellow, Black) dicampurkan dalam persentase terukur
       berdasarkan model subtraktif warna fisik (CMYK).
    3. Formula dihitung proporsional agar total selalu 100%.
    """
    r, g, b = hex_to_rgb(target_hex)

    # Perceived Luminance (Standar ITU-R BT.601)
    perceived_lum = 0.299 * r + 0.587 * g + 0.114 * b

    # Model subtraktif warna CMYK
    k = 1.0 - max(r, g, b)
    if k >= 0.999:
        c, m, y = 0.0, 0.0, 0.0
    else:
        c = (1.0 - r - k) / (1.0 - k)
        m = (1.0 - g - k) / (1.0 - k)
        y = (1.0 - b - k) / (1.0 - k)

    total_pigment_weight = c + m + y + k

    recipes = []

    # Kasus 1: Warna Putih Bersih / Hampir Putih Murni
    if total_pigment_weight < 0.02:
        recipes.append({
            "name": "Kombinasi Tinting Standar (Paling Akurat)",
            "components": [
                {"paint": "Base White (Putih Dasar)", "percentage": 100.0}
            ]
        })
        return recipes

    # Kasus 2: Warna Hitam Pekat
    if k >= 0.95:
        recipes.append({
            "name": "Kombinasi Tinting Standar (Paling Akurat)",
            "components": [
                {"paint": "Super Black (Hitam Pekat)", "percentage": 90.0},
                {"paint": "Base White (Putih Dasar)", "percentage": 10.0}
            ]
        })
        return recipes

    # Tentukan persentase Base White berdasarkan kecerahan (Luminance) warna:
    # Warna terang (pastel/langit) butuh Base White tinggi (60% - 92%).
    # Warna gelap/pekat butuh Deep Base White lebih rendah (25% - 50%).
    base_white_pct = round(max(25.0, min(92.0, perceived_lum * 75.0 + 15.0)), 1)
    colorant_budget = 100.0 - base_white_pct

    components = [{"paint": "Base White (Putih Dasar)", "percentage": base_white_pct}]

    pigment_shares = [
        ("Primary Cyan (Biru Tinting)", c),
        ("Primary Magenta (Merah Tinting)", m),
        ("Bright Yellow (Kuning Tinting)", y),
        ("Super Black (Hitam)", k),
    ]

    for name, weight in pigment_shares:
        if weight > 0.01:
            share_pct = round((weight / total_pigment_weight) * colorant_budget, 1)
            if share_pct >= 0.5:
                components.append({"paint": name, "percentage": share_pct})

    # Normalisasi agar total persis 100.0%
    curr_total = sum(item["percentage"] for item in components)
    if curr_total > 0 and curr_total != 100.0:
        diff = round(100.0 - curr_total, 1)
        components[0]["percentage"] = round(components[0]["percentage"] + diff, 1)

    recipes.append({
        "name": "Kombinasi Tinting Standar (Paling Akurat)",
        "components": components
    })

    # Resep Sederhana (Maksimal 3 Bahan Pokok untuk Campur Manual / Cat Kiloan)
    if len(components) > 3:
        sorted_comps = sorted(components, key=lambda x: x["percentage"], reverse=True)[:3]
        sub_total = sum(item["percentage"] for item in sorted_comps)
        simple_comps = [
            {"paint": item["paint"], "percentage": round((item["percentage"] / sub_total) * 100, 1)}
            for item in sorted_comps
        ]
        simple_total = sum(item["percentage"] for item in simple_comps)
        if simple_total != 100.0:
            simple_comps[0]["percentage"] = round(simple_comps[0]["percentage"] + (100.0 - simple_total), 1)

        recipes.append({
            "name": "Kombinasi Praktis (3 Bahan Pokok)",
            "components": simple_comps
        })

    return recipes

def calculate_wall_materials(box_w_px: int, box_h_px: int, img_w: int, img_h: int) -> dict:
    """
    Estimasi dimensi fisik, kebutuhan kaleng cat dinding, dan estimasi biaya (material cat + upah tukang).
    
    Standar Industri Arsitektur Interior:
    - Rata-rata tinggi dinding interior standar Indonesia = 2.8 - 3.0 meter.
    - Daya sebar cat: 10 m2 / Liter untuk 2 lapis aplikasi + 5% waste margin (buffer ceceran/kuas).
    - Biaya material cat interior standar: Rp 60.000 / Liter (~Rp 150.000 / Galon 2.5L).
    - Upah borongan jasa tukang cat dinding standar: Rp 20.000 / m2.
    """
    # Estimasi tinggi referensi frame ruangan (~2.8 meter)
    pixel_per_meter = max(img_h / 2.8, 1.0)

    est_width_m = round(box_w_px / pixel_per_meter, 2)
    est_height_m = round(box_h_px / pixel_per_meter, 2)
    est_area_m2 = round(est_width_m * est_height_m, 2)

    # Standar pengecatan: 10 m2 / Liter untuk 2 lapis + 5% buffer
    coverage_per_liter = 10.0
    coats = 2
    waste_margin = 1.05

    total_liters = round(((est_area_m2 * coats) / coverage_per_liter) * waste_margin, 2)
    total_ml = int(total_liters * 1000)

    # Rekomendasi kemasan kaleng
    galon_2_5L = math.ceil(total_liters / 2.5)
    if total_liters < 20:
        recommended_cans = f"{galon_2_5L} Galon (2.5 Liter)"
    else:
        pails = math.ceil(total_liters / 20)
        recommended_cans = f"{pails} Pail (20 Liter)"

    # Estimasi Biaya (Material Cat & Jasa Tukang)
    cost_paint_idr = int(total_liters * 60000)
    cost_labor_idr = int(est_area_m2 * 20000)
    total_cost_idr = cost_paint_idr + cost_labor_idr

    return {
        "estimated_width_m": est_width_m,
        "estimated_height_m": est_height_m,
        "estimated_area_m2": est_area_m2,
        "paint_needed_ml": total_ml,
        "paint_needed_liters": total_liters,
        "recommended_cans": recommended_cans,
        "estimated_paint_cost_idr": f"Rp {cost_paint_idr:,}".replace(",", "."),
        "estimated_labor_cost_idr": f"Rp {cost_labor_idr:,}".replace(",", "."),
        "estimated_total_cost_idr": f"Rp {total_cost_idr:,}".replace(",", ".")
    }
