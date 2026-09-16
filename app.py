import io
import json
import base64
import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from ultralytics import FastSAM
from color_engine import apply_realistic_color
from paint_mixer import generate_paint_recipes, calculate_wall_materials

# ui test
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Wall & Object Visualizer Engine")

#ui test 2
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Izinkan semua asal UI mengakses API ini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Memuat model FastSAM...")
model = FastSAM('FastSAM-s.pt')
print("Model FastSAM siap.")

@app.post("/api/v1/process-multi-objects")
async def process_multi_objects(
    file: UploadFile = File(...),
    # boxes_data berupa JSON string:
    # [{"id": 1, "is_wall": true, "box": [x1, y1, x2, y2], "target_hex": "#3498DB"}, ...]
    boxes_data: str = Form(...)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Format file harus JPEG, PNG, atau WEBP.")

    try:
        items = json.loads(boxes_data)
        if not isinstance(items, list) or len(items) == 0:
            raise HTTPException(status_code=422, detail="boxes_data harus berupa array objek.")

        # 1. Baca Input
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Gambar tidak valid.")

        img_h, img_w = img_bgr.shape[:2]
        result_bgr = img_bgr.copy()
        analysis_reports = []

        # 2. Proses Setiap Objek/Kotak yang Ditandai User
        for item in items:
            obj_id = item.get("id", 1)
            is_wall = item.get("is_wall", True)
            target_hex = item.get("target_hex", "#3498DB")
            x1, y1, x2, y2 = item.get("box", [0, 0, img_w, img_h])

            # Pastikan koordinat dalam batas citra
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(img_w, int(x2)), min(img_h, int(y2))
            box_w, box_h = max(1, x2 - x1), max(1, y2 - y1)

            # Segmentasi SAM menggunakan Bounding Box Prompt (BBox)
            results = model(
                img_bgr,
                bboxes=[[x1, y1, x2, y2]],
                retina_masks=True,
                verbose=False
            )

            # Jika terdeteksi mask, lakukan blending
            if results[0].masks is not None and len(results[0].masks.data) > 0:
                raw_mask = results[0].masks.data[0].cpu().numpy().astype(np.uint8) * 255
                obj_mask = cv2.resize(raw_mask, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
                result_bgr = apply_realistic_color(result_bgr, obj_mask, target_hex)

            # 3. Hitung Resep Cat untuk Semua Objek
            recipes = generate_paint_recipes(target_hex)

            report = {
                "object_id": obj_id,
                "is_wall": is_wall,
                "chosen_hex": target_hex,
                "paint_recipes": recipes,
                "material_estimation": None
            }

            # 4. Jika Objek adalah Dinding, Tambahkan Estimasi Dimensi & Jumlah Cat
            if is_wall:
                report["material_estimation"] = calculate_wall_materials(box_w, box_h, img_w, img_h)

            analysis_reports.append(report)

        # 5. Encode Citra Hasil ke Base64 (agar bisa dikirim bersama data JSON)
        _, encoded_img = cv2.imencode(".jpg", result_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        img_base64 = base64.b64encode(encoded_img.tobytes()).decode('utf-8')

        return {
            "status": "success",
            "processed_image_base64": f"data:image/jpeg;base64,{img_base64}",
            "reports": analysis_reports
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saat memproses: {str(e)}")