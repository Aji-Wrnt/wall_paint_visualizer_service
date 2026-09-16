# AI Wall Paint Visualizer & Material Estimator

A full-stack computer vision application designed to simulate interior wall repainting realistically and estimate material/paint requirements based on user-defined regions of interest.

The system utilizes **FastSAM (Fast Segment Anything)** for zero-shot instance segmentation via bounding box prompts, applies realistic color blending by preserving natural surface textures and ambient lighting, and calculates estimated paint volume along with pigmentation mixing formulas.

---

## Key Features

- **Interactive ROI Selection**: Draw custom bounding boxes over walls or objects directly on mobile.
- **Realistic Color Simulation**: Implements shadow, highlight, and texture preservation using advanced alpha blending over predicted SAM segmentation masks.
- **Material & Cost Estimator**: Calculates wall surface area approximations and computes required paint volume (Liters/mL) and coverage based on standard architectural metrics.
- **Paint Tinting Recipes**: Translates target HEX colors into pigment dispersion breakdowns (Base, White, Tint pigments) for practical hardware/paint store mixing.
- **Cross-Platform Client**: Built with Flutter for smooth camera input, box manipulation, and instant visual feedback.

---

## System Architecture

```text
+-------------------+      HTTP Multipart / JSON      +-------------------------+
|   Flutter Client  | -----------------------------> |      FastAPI Server     |
| (Android/Desktop) |                                |      (Python / SAM)     |
+-------------------+ <----------------------------- +-------------------------+
                       Base64 Rendered Image + Report
                    
```


1. Client: Captures/loads image, captures user bounding boxes ([x1, y1, x2, y2]) and chosen colors.

2. AI Engine:

    - Decodes image & auto-corrects EXIF orientation.
    - Feeds bounding boxes into FastSAM (FastSAM-s.pt) to generate segmentation masks.
    - Blends target color onto masked pixels using surface luminance weights.
    - Generates estimation reports and base64-encoded output image.


## Tech Stack

    - Mobile Client: Flutter (Dart), image_picker, flutter_colorpicker, http
    - Backend / AI Service: FastAPI, Uvicorn, Python 3.10+
    - Computer Vision & AI: PyTorch, FastSAM (ultralytics), OpenCV, Pillow, NumPy


## Project Structure

    projek2_AiColoring/
    ├── ai_service/             # FastAPI backend & AI logic
    │   ├── app.py              # Main API endpoints & processing pipeline
    │   ├── weights/            # Model weights (e.g., FastSAM-s.pt)
    │   └── requirements.txt    # Python dependencies
    ├── mobile_client/          # Flutter mobile application
    │   ├── lib/
    │   │   └── main.dart       # Interactive UI, Canvas ROI, API integration
    │   └── pubspec.yaml        # Flutter packages
    └── README.md


## Started

1. Prerequisites
    - Python 3.10+ with Conda or virtualenv
    - Flutter SDK (v3.0+) & Android SDK / NDK installed

2. Backend Setup (ai_service)

    1. Navigate to the backend directory
    2. Create and activate a Conda environment:
        - conda create -n wall_ai_env python=3.10 -y
        - conda activate wall_ai_env
    3. Install Python dependencies:
        - pip install -r requirements.txt
    4. Download the FastSAM weights (FastSAM-s.pt) and place it inside ai_service/weights/.
    5. Run the FastAPI development server:
        - uvicorn app:app --host 0.0.0.0 --port 8000 --reload

3. Mobile Client Setup (mobile_client)

    1. Navigate to the mobile client directory:
        - cd mobile_client
    2. Install dependencies:
        - flutter pub get
    3. Run on a connected Android device:
        - flutter run
    4. Open the in-app Settings menu and configure the server URL:
        - http://<local_ip>:8000/api/v1/process-multi-objects
    
## Licences
This project is licensed under the MIT License - see the LICENSE file for details.
