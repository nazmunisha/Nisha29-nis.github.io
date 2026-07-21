import time
import numpy as np
from PIL import Image

from database import get_connection
from attendance import mark_attendance


# --------------------------------------------------
# OpenCV Face Detector
# --------------------------------------------------
def get_detector():
    import cv2

    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    if detector.empty():
        return None

    return detector


# --------------------------------------------------
# Extract Face From Uploaded / Camera Image
# --------------------------------------------------
def extract_face_from_upload(image_file, size=(200, 200)):
    import cv2

    image = Image.open(image_file).convert("RGB")
    arr = np.array(image)

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    detector = get_detector()
    if detector is None:
        return None

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face = gray[y:y + h, x:x + w]

    return cv2.resize(face, size)


# --------------------------------------------------
# Extract Face From Webcam Frame
# --------------------------------------------------
def extract_face_from_frame(frame, detector, size=(200, 200)):
    import cv2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        return None, None

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face = gray[y:y + h, x:x + w]

    return cv2.resize(face, size), (x, y, w, h)


# --------------------------------------------------
# Load LBPH Recognition Model From Database Faces
# --------------------------------------------------
def load_recognition_model():
    import cv2

    if not hasattr(cv2, "face"):
        return None

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT student_id, encoding FROM face_data")
    rows = cur.fetchall()

    conn.close()

    faces = []
    labels = []

    for row in rows:
        arr = np.frombuffer(row["encoding"], dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

        if img is not None:
            img = cv2.resize(img, (200, 200))
            faces.append(img)
            labels.append(int(row["student_id"]))

    if not faces:
        return None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    return recognizer


# --------------------------------------------------
# Register / Update Face With Duplicate Face Protection
# --------------------------------------------------
def register_face(student_id, image_file):
    import cv2

    student_id = int(student_id)

    face = extract_face_from_upload(image_file)

    if face is None:
        return False, "No face detected. Try again with clear lighting."

    # Duplicate face detection:
    # If this face already belongs to another student, block registration.
    recognizer = load_recognition_model()

    if recognizer is not None:
        try:
            predicted_id, confidence = recognizer.predict(face)
            predicted_id = int(predicted_id)

            # Lower confidence means better match.
            # 60 is practical for this simple OpenCV LBPH project.
            if confidence <= 60 and predicted_id != student_id:
                return (
                    False,
                    f"This face is already registered for Student ID {predicted_id}."
                )

        except Exception:
            # If duplicate checking fails, continue registration rather than crashing.
            pass

    ok, buffer = cv2.imencode(".png", face)

    if not ok:
        return False, "Could not process face."

    blob = buffer.tobytes()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT student_id FROM face_data WHERE student_id=%s",
        (student_id,)
    )
    exists = cur.fetchone()

    if exists:
        cur.execute(
            "UPDATE face_data SET encoding=%s WHERE student_id=%s",
            (blob, student_id)
        )
        msg = "Face updated successfully."
    else:
        cur.execute(
            "INSERT INTO face_data (student_id, encoding) VALUES (%s, %s)",
            (student_id, blob)
        )
        msg = "Face registered successfully."

    conn.commit()
    conn.close()

    return True, msg


# --------------------------------------------------
# Live Attendance In Separate OpenCV Window
# --------------------------------------------------
def start_live_attendance():
    import cv2

    detector = get_detector()
    if detector is None:
        return False, "OpenCV face detector not found."

    recognizer = load_recognition_model()
    if recognizer is None:
        return False, "No registered faces found or opencv-contrib-python missing."

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return False, "Camera not found. Check webcam permission."

    last_seen = {}
    cooldown = 5

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        face, box = extract_face_from_frame(frame, detector)

        if face is not None and box is not None:
            predicted_id, confidence = recognizer.predict(face)
            predicted_id = int(predicted_id)

            x, y, w, h = box

            if confidence <= 70:
                now = time.time()

                if predicted_id not in last_seen or now - last_seen[predicted_id] > cooldown:
                    marked, name, message = mark_attendance(predicted_id)
                    last_seen[predicted_id] = now
                else:
                    name = f"Student {predicted_id}"
                    message = "Already processed"

                color = (0, 255, 0)
                label = f"{name} - {message}"
            else:
                color = (0, 0, 255)
                label = f"Unknown ({confidence:.1f})"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        cv2.putText(
            frame,
            "Press Q to stop",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow("Live Face Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    return True, "Live attendance stopped."


# --------------------------------------------------
# Live Attendance Inside Streamlit Dashboard
# Optional: use this if dashboard.py passes placeholders.
# --------------------------------------------------
def start_live_attendance_inside_dashboard(
    frame_placeholder=None,
    status_placeholder=None,
    duration=60
):
    import cv2

    detector = get_detector()
    if detector is None:
        return False, "OpenCV face detector not found."

    recognizer = load_recognition_model()
    if recognizer is None:
        return False, "No registered faces found or opencv-contrib-python missing."

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return False, "Camera not found. Check webcam permission."

    last_seen = {}
    cooldown = 5
    start_time = time.time()

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        face, box = extract_face_from_frame(frame, detector)

        if face is not None and box is not None:
            predicted_id, confidence = recognizer.predict(face)
            predicted_id = int(predicted_id)

            x, y, w, h = box

            if confidence <= 70:
                now = time.time()

                if predicted_id not in last_seen or now - last_seen[predicted_id] > cooldown:
                    marked, name, message = mark_attendance(predicted_id)
                    last_seen[predicted_id] = now
                else:
                    name = f"Student {predicted_id}"
                    message = "Already processed"

                color = (0, 255, 0)
                label = f"{name} - {message}"

                if status_placeholder:
                    status_placeholder.success(label)
            else:
                color = (0, 0, 255)
                label = f"Unknown ({confidence:.1f})"

                if status_placeholder:
                    status_placeholder.warning(label)

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if frame_placeholder:
            frame_placeholder.image(
                frame_rgb,
                channels="RGB",
                use_container_width=True
            )

        if time.time() - start_time > duration:
            break

    cap.release()

    return True, "Live attendance stopped."
