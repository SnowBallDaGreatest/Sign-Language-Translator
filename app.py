"""
Flask backend for the Sign Language Translator.

This version separates visually similar signs:
- Hello vs Please vs Thank You
- A vs S vs Sorry

Heuristics used:
- Hello: Hand open, palm forward, near head level (usually higher y).
- Please: Hand flat on chest (usually lower y, palm facing body - tricky in 2D).
- Thank You: Hand moving away from chin (lower y, palm towards face).
- A: Thumb alongside index.
- S: Thumb across fingers.
- Sorry: Fist on chest (S-shape, lower y).

Run with:
    pip install flask flask-cors mediapipe==0.10.14 opencv-python-headless
    python app.py
"""

import threading
import time
import cv2
import mediapipe as mp
from flask import Flask, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ---- shared state, guarded by a lock since the camera runs in a thread ----
state_lock = threading.Lock()
latest_frame = None
latest_gesture = "..."
camera_running = False
_cap = None
_thread = None

def is_finger_extended(landmarks, tip, knuckle):
    return landmarks[tip].y < landmarks[knuckle].y

def detect_gesture(landmarks):
    # Landmarks for finger tips and knuckles
    tt, tk = 4, 2   # Thumb
    it, ik = 8, 6   # Index
    mt, mk = 12, 10 # Middle
    rt, rk = 16, 14 # Ring
    pt, pk = 20, 18 # Pinky
    
    # Finger extension states
    index_ext = is_finger_extended(landmarks, it, ik)
    middle_ext = is_finger_extended(landmarks, mt, mk)
    ring_ext = is_finger_extended(landmarks, rt, rk)
    pinky_ext = is_finger_extended(landmarks, pt, pk)
    
    # Thumb extension
    thumb_ext = abs(landmarks[tt].x - landmarks[5].x) > 0.06

    # --- Separation Logic ---

    # 1. Open Hand Group (Hello, Please, Thank You, B)
    if index_ext and middle_ext and ring_ext and pinky_ext:
        # Check vertical position (y-coordinate)
        # Assuming 0 is top, 1 is bottom
        wrist_y = landmarks[0].y
        
        if wrist_y < 0.4: # Hand is high
            return "Hello 👋"
        elif 0.4 <= wrist_y < 0.7: # Hand is mid-level
            return "Thank You 🙏"
        else: # Hand is low
            return "Please 🙏"

    # 2. Fist Group (A, S, Sorry, E)
    if not index_ext and not middle_ext and not ring_ext and not pinky_ext:
        wrist_y = landmarks[0].y
        
        # Distinguish A vs S based on thumb position
        # A: Thumb is alongside index (landmark 4 x is far from 5 x)
        # S: Thumb is across fingers (landmark 4 x is close to 5 x)
        thumb_across = abs(landmarks[tt].x - landmarks[it].x) < 0.05
        
        if wrist_y > 0.7:
            return "Sorry 😔"
        
        if thumb_across:
            return "S"
        else:
            if landmarks[tt].y < landmarks[it].y:
                return "A"
            else:
                return "E"

    # --- Other Signs ---

    # Love You: Thumb, Index, Pinky extended
    if index_ext and pinky_ext and thumb_ext and not middle_ext and not ring_ext:
        return "Love You ❤️"

    # Y: Thumb and pinky extended
    if thumb_ext and pinky_ext and not index_ext and not middle_ext and not ring_ext:
        return "Y"

    # L: Index and thumb extended
    if index_ext and thumb_ext and not middle_ext and not ring_ext and not pinky_ext:
        return "L"

    # W: Index, middle, ring extended
    if index_ext and middle_ext and ring_ext and not pinky_ext:
        return "W"

    # F: Middle, ring, pinky extended, index touching thumb
    if middle_ext and ring_ext and pinky_ext and not index_ext:
        return "F"

    # V / U
    if index_ext and middle_ext and not ring_ext and not pinky_ext:
        if abs(landmarks[it].x - landmarks[mt].x) > 0.05:
            return "V"
        else:
            return "U"

    # D: Index extended
    if index_ext and not middle_ext and not ring_ext and not pinky_ext:
        return "D"

    # I: Pinky extended
    if pinky_ext and not index_ext and not middle_ext and not ring_ext:
        return "I"

    return "..."

def camera_loop():
    global latest_frame, latest_gesture, camera_running, _cap

    _cap = cv2.VideoCapture(0)
    if not _cap.isOpened():
        print("ERROR: Could not open webcam.")
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        while camera_running and _cap.isOpened():
            ret, frame = _cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(img_rgb)

            gesture_label = "..."
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    gesture_label = detect_gesture(hand_landmarks.landmark)
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )
                color = (0, 128, 255)
            else:
                color = (0, 0, 255)

            cv2.putText(
                frame, gesture_label, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 4, cv2.LINE_AA,
            )

            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                with state_lock:
                    latest_frame = buf.tobytes()
                    latest_gesture = gesture_label

            time.sleep(0.01)

    _cap.release()

def mjpeg_generator():
    boundary = b"--frame"
    while True:
        with state_lock:
            frame = latest_frame
        if frame is not None:
            yield (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
        time.sleep(0.03)

@app.route("/video_feed")
def video_feed():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

@app.route("/gesture")
def gesture():
    with state_lock:
        g = latest_gesture
    return jsonify({"gesture": g})

@app.route("/camera/start", methods=["POST"])
def camera_start():
    global camera_running, _thread
    if not camera_running:
        camera_running = True
        _thread = threading.Thread(target=camera_loop, daemon=True)
        _thread.start()
    return jsonify({"status": "started"})

@app.route("/camera/stop", methods=["POST"])
def camera_stop():
    global camera_running
    camera_running = False
    return jsonify({"status": "stopped"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
