import cv2
import numpy as np
import base64
from deepface import DeepFace

class PretrainedVisionAnalyzer:
    def __init__(self):
        print("[SETUP] Loading pre-trained Computer Vision models for facial analysis...")
        # DeepFace auto-downloads weights for emotion if not present
        # Haar Cascades for extremely fast robust eye detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    def decode_base64_frame(self, b64_string):
        if "," in b64_string:
            b64_string = b64_string.split(",")[1]
        img_data = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def analyze_frame(self, frame_b64):
        try:
            img = self.decode_base64_frame(frame_b64)
            if img is None:
                return {"emotion": "neutral", "eye_contact": False}

            # 1. EMOTION: using DeepFace pre-trained network
            try:
                # enforce_detection=False prevents crash if face briefly disappears
                emotions = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
                dominant_emotion = emotions[0]['dominant_emotion'] if isinstance(emotions, list) else emotions['dominant_emotion']
            except Exception as e:
                print("DeepFace minimal error:", e)
                dominant_emotion = "neutral"

            # 2. EYE CONTACT: utilizing Haar Cascades
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            eye_contact = False

            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
                if len(eyes) >= 1:
                    eye_contact = True
                    break

            return {
                "emotion": dominant_emotion,
                "eye_contact": eye_contact
            }
        except Exception as e:
            print("[CV ERROR]", e)
            return {"emotion": "neutral", "eye_contact": False}

cv_analyzer = PretrainedVisionAnalyzer()
