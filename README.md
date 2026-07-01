# Sign Language Translator 🤟

A real-time sign language detection app powered by Python (MediaPipe + OpenCV) on the backend and a clean HTML/JS interface on the frontend.

---

## Project Structure

```
Sign/
├── app.py           # Flask backend — runs webcam + gesture detection
├── back.py          # Original standalone gesture detection script (OpenCV window)
├── interface.html   # Frontend UI — Live Translation, Text to Sign, Dictionary
└── README.md        # This file
```

---

## Features

- **Live Translation** — Point your webcam at your hand; the page shows the detected gesture in real time with hand landmarks drawn on the feed.
- **Text to Sign** — Type a word or phrase and see a corresponding sign animation.
- **Dictionary** — Browse all supported gestures with visual references.

---

## Supported Gestures

👋 Common Phrases
Sign	How to Perform
Hello 👋-	Hold your hand open (B-shape) with palm facing forward, near your forehead level.
Thank You 🙏-	Hold your hand open (B-shape) with palm facing toward your face, near your chin level.
Please 🙏-	Hold your hand open (B-shape) with palm facing toward your body, near your chest level.
Love You ❤️- Extend your thumb, index, and pinky fingers while keeping the middle and ring fingers curled.
Yes 👍-	Make a fist (S-shape) and hold it steady (simulates a nodding head).
No 👎-	Extend your index and middle fingers and tap them against your extended thumb.
Sorry 😔-	Make a fist (S-shape) and hold it near your chest level.


🔤 Supported Alphabet
Letter	How to Perform
A-	Make a fist with the thumb tucked alongside the index finger.
B-	Hold all four fingers straight up and together, with the thumb folded across the palm.
D-	Extend the index finger straight up, while the other fingers and thumb touch to form a circle.
F-	Touch the tip of your index finger to your thumb, while keeping the other three fingers extended and spread.
I-	Extend the pinky finger straight up, while keeping all other fingers and thumb curled.
L-	Extend the index finger straight up and the thumb out to the side, forming an "L" shape.
U-	Extend the index and middle fingers straight up and keep them pressed together.
V-	Extend the index and middle fingers straight up and spread them apart in a "V" shape.
W-	Extend the index, middle, and ring fingers straight up and spread them apart.
Y-	Extend the thumb and pinky finger out, while keeping the index, middle, and ring fingers curled.


💡 Tips for Better Recognition
1	Lighting: Ensure your hand is well-lit and there are no strong shadows behind it.
2	Distance: Keep your hand about 1–2 feet (30–60 cm) away from the webcam.
3	Background: A plain, non-distracting background helps MediaPipe track your landmarks more accurately.
4	Orientation: Keep your palm mostly facing the camera unless the sign specifically requires a different orientation.


---

## Requirements

- Python 3.9 – 3.11 (Python 3.9.16 via Conda `spyconda` env recommended)
- A working webcam

---

## Installation

Run all commands in your terminal with the correct Python interpreter:

```bash
C:/Users/91700/.conda/spyconda/python.exe -m pip install opencv-python numpy mediapipe flask flask-cors
```

> **Important:** If `mediapipe` fails to import after installation, your NumPy version may be too new. Fix it with:
> ```bash
> C:/Users/91700/.conda/spyconda/python.exe -m pip install "numpy<2" --force-reinstall
> C:/Users/91700/.conda/spyconda/python.exe -m pip install mediapipe --force-reinstall --no-cache-dir
> ```

---

## Running the App

### Step 1 — Start the backend

Open a terminal in the `Sign/` folder and run:

```bash
C:/Users/91700/.conda/spyconda/python.exe app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

**Keep this terminal open** the entire time you use the app.

### Step 2 — Open the frontend

Double-click `interface.html` to open it in your browser, or use VS Code's Live Server extension.

### Step 3 — Start the camera

Click the **Start Camera** button on the Live Translation tab. The backend will open your webcam, start detecting gestures, and stream the annotated video to the page.

Press **Stop Camera** or close the browser tab when done.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Could not reach the Python backend" | Make sure `app.py` is running in a terminal before clicking Start Camera |
| `app.py` exits instantly with no output | Run each import individually to find the broken one: `python -c "import mediapipe; print('ok')"` |
| Hand not being detected | Make sure your hand is well-lit, against a plain background, and fills a good portion of the frame |
| Wrong camera used | Change `VideoCapture(0, cv2.CAP_DSHOW)` in `app.py` to `VideoCapture(1, ...)` or `(2, ...)` |
| Gesture always shows `...` | Your hand is detected but no gesture rule matched — try adjusting your hand position |
| Yellow squiggle under imports in VS Code | Select the `spyconda` interpreter via `Ctrl+Shift+P` → "Python: Select Interpreter" |

---

## How It Works

```
Browser (interface.html)
        |
        |  POST /camera/start
        |  GET  /video_feed  (MJPEG stream)
        |  GET  /gesture     (JSON, polled every 300ms)
        v
Flask Server (app.py @ 127.0.0.1:5000)
        |
        |  cv2.VideoCapture → frames
        |  MediaPipe Hands  → 21 hand landmarks
        |  detect_gesture() → label string
        v
Browser displays annotated video + gesture label
```

The gesture detection compares fingertip Y-coordinates against their knuckle Y-coordinates to determine whether each finger is extended or curled, then matches the combination against known gesture rules.

---

## Adding New Gestures

Open `app.py` and add a new `if` block inside the `detect_gesture()` function, following the same pattern:

```python
# "OK": index + thumb touching, other fingers extended
if (is_finger_extended(landmarks, mt, mk) and
    is_finger_extended(landmarks, rt, rk) and
    is_finger_extended(landmarks, pt, pk)):
    return "OK 👌"
```

Landmark indices follow MediaPipe's hand landmark model — [see the full map here](https://mediapipe.readthedocs.io/en/latest/solutions/hands.html).

---

## Credits

Built with [MediaPipe](https://mediapipe.dev/) · [OpenCV](https://opencv.org/) · [Flask](https://flask.palletsprojects.com/)
