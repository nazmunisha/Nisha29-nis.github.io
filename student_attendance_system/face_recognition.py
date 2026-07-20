# ==========================================================
# Purpose:
# This file manages the complete face registration and
# face recognition process used for automatic attendance.
#
# Main Features:
# - Load OpenCV face detector
# - Extract face from uploaded image
# - Extract face from live webcam frame
# - Register or update student face
# - Detect duplicate face registration
# - Train LBPH face recognizer
# - Recognize student using webcam
# - Mark attendance automatically
#
# Technologies Used:
# - Python
# - OpenCV
# - LBPH Face Recognizer
# - Pillow (PIL)
# - NumPy
# - MySQL
# ==========================================================

# Used to control cooldown timing during live attendance
import time
import streamlit as st

# Used to convert images into array format for OpenCV
import numpy as np

# Pillow is used to open uploaded image files
from PIL import Image

# Import database connection
from database import get_connection

# Import attendance marking function
from attendance import mark_attendance


# ==========================================================
# Function: get_detector()
#
# Purpose:
# Load the OpenCV Haar Cascade face detector.
#
# Explanation:
# Haar Cascade is used to find human faces in an image
# or webcam frame. It detects the position of the face.
#
# Returns:
# - detector object if loaded successfully
# - None if detector cannot be loaded
# ==========================================================
def get_detector():
    import cv2

    # Load pre-trained Haar Cascade model from OpenCV
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # If detector is empty, it means OpenCV could not load the model
    if detector.empty():
        return None

    return detector


# ==========================================================
# Function: extract_face_from_upload()
#
# Purpose:
# Extract a face from an uploaded image or camera image.
#
# Process:
# 1. Open image using Pillow.
# 2. Convert image to RGB format.
# 3. Convert image into NumPy array.
# 4. Convert image to grayscale.
# 5. Detect face using Haar Cascade.
# 6. Crop the largest detected face.
# 7. Resize face to 200x200 pixels.
#
# Why resize?
# All faces must have the same size so that LBPH can compare
# them correctly.
#
# Returns:
# - processed face image
# - None if no face is detected
# ==========================================================
def extract_face_from_upload(image_file, size=(200, 200)):
    import cv2

    # Open uploaded image using Pillow and convert it to RGB
    image = Image.open(image_file).convert("RGB")

    # Convert Pillow image into NumPy array for OpenCV
    arr = np.array(image)

    # Convert RGB image to grayscale because face recognition
    # works better and faster on grayscale images
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Load face detector
    detector = get_detector()

    if detector is None:
        return None

    # Detect faces in the grayscale image
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    # If no face is found, return None
    if len(faces) == 0:
        return None

    # If multiple faces are found, select the largest face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

    # Crop only the face area
    face = gray[y:y + h, x:x + w]

    # Resize face to fixed size
    return cv2.resize(face, size)


# ==========================================================
# Function: extract_face_from_frame()
#
# Purpose:
# Extract a face from a live webcam frame.
#
# Difference from upload function:
# Webcam frames already come from OpenCV, so Pillow is not used.
#
# Returns:
# - processed face image
# - face box coordinates (x, y, width, height)
# ==========================================================
def extract_face_from_frame(frame, detector, size=(200, 200)):
    import cv2

    # Convert webcam frame from BGR to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    # If no face is detected
    if len(faces) == 0:
        return None, None

    # Select the largest detected face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

    # Crop face region
    face = gray[y:y + h, x:x + w]

    # Return resized face and box location
    return cv2.resize(face, size), (x, y, w, h)


# ==========================================================
# Function: load_recognition_model()
#
# Purpose:
# Load all registered faces from the database and train the
# LBPH face recognition model.
#
# LBPH Meaning:
# LBPH = Local Binary Pattern Histogram.
# It recognises faces by comparing texture patterns.
#
# Process:
# 1. Read saved face data from MySQL.
# 2. Decode binary image data.
# 3. Resize each face to 200x200.
# 4. Train LBPH model using faces and student IDs.
#
# Returns:
# - trained LBPH recognizer
# - None if no registered faces are available
# ==========================================================
def load_recognition_model():
    import cv2

    # cv2.face is available only in opencv-contrib-python
    if not hasattr(cv2, "face"):
        return None

    # Connect to database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Load all registered face images
    cur.execute("SELECT student_id, encoding FROM face_data")
    rows = cur.fetchall()

    conn.close()

    # List to store face images
    faces = []

    # List to store matching student IDs
    labels = []

    for row in rows:
        # Convert binary data from MySQL back into NumPy array
        arr = np.frombuffer(row["encoding"], dtype=np.uint8)

        # Decode image from binary format into grayscale image
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

        if img is not None:
            # Resize image for consistent training size
            img = cv2.resize(img, (200, 200))

            # Add face image to training list
            faces.append(img)

            # Add student ID as the label
            labels.append(int(row["student_id"]))

    # If no faces are found, recognition model cannot be trained
    if not faces:
        return None

    # Create LBPH face recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    # Train recognizer using face images and student IDs
    recognizer.train(faces, np.array(labels))

    return recognizer


# ==========================================================
# Function: register_face()
#
# Purpose:
# Register or update a student's face in the database.
#
# Process:
# 1. Extract face from uploaded image.
# 2. Check if the same face is already registered
#    for another student.
# 3. Convert processed face into PNG binary data.
# 4. Save new face or update existing face in MySQL.
#
# Duplicate Face Protection:
# This prevents the same face being registered under
# multiple student IDs.
#
# Returns:
# - True/False
# - message explaining result
# ==========================================================
def register_face(student_id, image_file):
    import cv2

    # Convert student ID to integer
    student_id = int(student_id)

    # Extract face from uploaded image
    face = extract_face_from_upload(image_file)

    # Stop if no face is detected
    if face is None:
        return False, "No face detected. Try again with clear lighting."

    # ------------------------------------------------------
    # Duplicate Face Detection
    # ------------------------------------------------------
    # Load recognition model using existing registered faces
    recognizer = load_recognition_model()

    if recognizer is not None:
        try:
            # Predict whether uploaded face matches an existing student
            predicted_id, confidence = recognizer.predict(face)
            predicted_id = int(predicted_id)

            # Lower confidence means stronger match.
            # If same face belongs to another student, block registration.
            if confidence <= 60 and predicted_id != student_id:
                return (
                    False,
                    f"This face is already registered for Student ID {predicted_id}."
                )

        except Exception:
            # If duplicate check fails, continue registration instead of crashing
            pass

    # Convert processed face image into PNG format
    ok, buffer = cv2.imencode(".png", face)

    if not ok:
        return False, "Could not process face."

    # Convert encoded image into binary bytes for MySQL
    blob = buffer.tobytes()

    # Connect to database
    conn = get_connection()
    cur = conn.cursor()

    # Check if this student already has a registered face
    cur.execute(
        "SELECT student_id FROM face_data WHERE student_id=%s",
        (student_id,)
    )
    exists = cur.fetchone()

    # If face already exists, update it
    if exists:
        cur.execute(
            "UPDATE face_data SET encoding=%s WHERE student_id=%s",
            (blob, student_id)
        )
        msg = "Face updated successfully."

    # Otherwise insert new face record
    else:
        cur.execute(
            "INSERT INTO face_data (student_id, encoding) VALUES (%s, %s)",
            (student_id, blob)
        )
        msg = "Face registered successfully."

    # Save database changes
    conn.commit()

    # Close database connection
    conn.close()

    return True, msg


# ==========================================================
# Function: get_student_name()
#
# Purpose:
# Get the student's real name from the database using
# the student_id predicted by LBPH.
# ==========================================================
def get_student_name(student_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT name FROM students WHERE student_id=%s",
        (int(student_id),)
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return row["name"]

    return f"Student {student_id}"


# ==========================================================
# Function: get_student_details()
#
# Purpose:
# Get complete student details for the recognition card
# displayed inside the Streamlit dashboard.
# ==========================================================
def get_student_details(student_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT student_id, roll_no, name, department, class, email, photo
        FROM students
        WHERE student_id=%s
    """, (int(student_id),))

    row = cur.fetchone()
    conn.close()

    if row:
        return row

    return {
        "student_id": int(student_id),
        "roll_no": "",
        "name": f"Student {student_id}",
        "department": "",
        "class": "",
        "email": "",
        "photo": None
    }


# ==========================================================
# Function: format_attendance_status()
#
# Purpose:
# Convert backend attendance messages into clear dashboard
# statuses for the live recognition card.
# ==========================================================
def format_attendance_status(marked, message):
    message_text = str(message or "").lower()

    if marked:
        return "Attendance Marked Successfully", "#16a34a", "#dcfce7", "✅"

    if "already" in message_text:
        return "Attendance Already Marked Today", "#ca8a04", "#fef9c3", "🟡"

    return message or "Attendance Processed", "#2563eb", "#dbeafe", "ℹ️"


# ==========================================================
# Function: show_recognition_details()
#
# Purpose:
# Display a professional student information card when
# a face is recognised during live attendance.
# ==========================================================
def show_recognition_details(
    detail_placeholder,
    student,
    confidence,
    status_text,
    status_color,
    status_bg,
    status_icon
):
    import base64
    from datetime import datetime

    if not detail_placeholder:
        return

    confidence_score = max(0, min(100, 100 - float(confidence)))
    current_time = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")

    photo_html = """
    <div style='width:96px;height:96px;border-radius:50%;background:#eef4ff;
    display:flex;align-items:center;justify-content:center;font-size:44px;
    border:3px solid white;box-shadow:0 8px 20px rgba(0,0,0,.12);'>👤</div>
    """

    if student.get("photo"):
        img = base64.b64encode(student["photo"]).decode()
        photo_html = f"""
        <img src="data:image/png;base64,{img}"
        style="width:96px;height:96px;border-radius:50%;object-fit:cover;
        border:3px solid white;box-shadow:0 8px 20px rgba(0,0,0,.12);">
        """

    name = student.get("name", "Unknown")
    student_id = student.get("student_id", "")
    roll_no = student.get("roll_no", "")
    department = student.get("department", "")
    class_name = student.get("class", "")

    card = f"""
    <div style="background:white;border:1px solid #e6edf8;border-radius:22px;
    padding:22px;box-shadow:0 14px 35px rgba(15,23,42,.10);margin-top:10px;">
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;">
            {photo_html}
            <div>
                <div style="font-size:24px;font-weight:800;color:#081b45;">
                    {name}
                </div>
                <div style="font-size:14px;color:#64748b;font-weight:600;">
                    Student ID: {student_id} | Roll No: {roll_no}
                </div>
            </div>
        </div>

        <div style="background:{status_bg};color:{status_color};border-radius:999px;
        padding:10px 14px;font-weight:800;text-align:center;margin-bottom:14px;">
            {status_icon} {status_text}
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:#f8fbff;border-radius:14px;padding:12px;">
                <b>Department</b><br>{department}
            </div>
            <div style="background:#f8fbff;border-radius:14px;padding:12px;">
                <b>Class</b><br>{class_name}
            </div>
            <div style="background:#eff6ff;border-radius:14px;padding:12px;color:#1d4ed8;">
                <b>Confidence</b><br>{confidence_score:.1f}%
            </div>
            <div style="background:#fff7ed;border-radius:14px;padding:12px;color:#9a3412;">
                <b>Time</b><br>{current_time}
            </div>
        </div>
    </div>
    """

    detail_placeholder.markdown(card, unsafe_allow_html=True)


# ==========================================================
# Function: show_unknown_face_details()
#
# Purpose:
# Display a professional warning card when the detected face
# does not match a registered student.
# ==========================================================
def show_unknown_face_details(detail_placeholder, confidence):
    if not detail_placeholder:
        return

    confidence_score = max(0, min(100, 100 - float(confidence)))

    detail_placeholder.markdown(f"""
    <div style="background:white;border:1px solid #fee2e2;border-radius:22px;
    padding:22px;box-shadow:0 14px 35px rgba(15,23,42,.10);margin-top:10px;">
        <div style="font-size:52px;text-align:center;">❌</div>
        <h3 style="color:#dc2626;margin-top:0;text-align:center;">Unknown Face</h3>
        <p style="color:#64748b;text-align:center;">
            This face is not registered in the Attendance Management System.
        </p>
        <div style="background:#fee2e2;color:#991b1b;border-radius:14px;padding:12px;text-align:center;font-weight:800;">
            Recognition Confidence: {confidence_score:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================
# Function: start_live_attendance()
#
# Purpose:
# Start live face recognition attendance using a separate
# OpenCV webcam window.
# ==========================================================
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
                    marked = False
                    name = get_student_name(predicted_id)
                    message = "Already processed"

                status_text, _, _, status_icon = format_attendance_status(marked, message)
                color = (0, 255, 0) if marked else (0, 215, 255)
                label = f"{status_icon} {name} - {status_text}"

            else:
                color = (0, 0, 255)
                label = f"Unknown ({confidence:.1f})"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
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


# ==========================================================
# Function: start_live_attendance_inside_dashboard()
#
# Purpose:
# Run live face attendance inside the Streamlit dashboard.
#
# Returns:
# - True/False
# - message
# ==========================================================


def start_live_attendance_inside_dashboard(
    frame_placeholder=None,
    status_placeholder=None,
    detail_placeholder=None,
    duration=60
):
    import cv2
    from datetime import datetime

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

    def show_student_details(student, confidence, status_text, status_type):
        if not detail_placeholder:
            return

        confidence_score = max(0, min(100, 100 - float(confidence)))
        current_time = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")

        with detail_placeholder.container():
            if student.get("photo"):
                st.image(student["photo"], width=120)
            else:
                st.markdown("### 👤")

            st.markdown(f"### {student.get('name', '')}")
            st.write(f"**Student ID:** {student.get('student_id', '')}")
            st.write(f"**Roll No:** {student.get('roll_no', '')}")
            st.write(f"**Department:** {student.get('department', '')}")
            st.write(f"**Class:** {student.get('class', '')}")

            if status_type == "marked":
                st.success(f"✅ {status_text}")
            elif status_type == "already":
                st.warning(f"🟡 {status_text}")
            else:
                st.info(f"ℹ️ {status_text}")

            st.write(f"**Recognition Confidence:** {confidence_score:.1f}%")
            st.write(f"**Attendance Time:** {current_time}")

    def show_unknown_details(confidence):
        if not detail_placeholder:
            return

        confidence_score = max(0, min(100, 100 - float(confidence)))

        with detail_placeholder.container():
            st.error("❌ Unknown Face")
            st.write("This face is not registered in the system.")
            st.write(f"**Confidence:** {confidence_score:.1f}%")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        face_img, box = extract_face_from_frame(frame, detector)

        if face_img is not None and box is not None:
            predicted_id, confidence = recognizer.predict(face_img)
            predicted_id = int(predicted_id)
            x, y, w, h = box

            if confidence <= 70:
                now = time.time()
                student = get_student_details(predicted_id)
                name = student.get("name", get_student_name(predicted_id))

                if predicted_id not in last_seen or now - last_seen[predicted_id] > cooldown:
                    marked, db_name, message = mark_attendance(predicted_id)
                    last_seen[predicted_id] = now
                else:
                    marked = False
                    message = "Already processed"

                if marked:
                    status_text = "Attendance Marked Successfully"
                    status_type = "marked"
                    box_color = (0, 180, 0)
                else:
                    status_text = "Attendance Already Marked Today"
                    status_type = "already"
                    box_color = (0, 215, 255)

                if status_placeholder:
                    if marked:
                        status_placeholder.success(f"{name}: {status_text}")
                    else:
                        status_placeholder.warning(f"{name}: {status_text}")

                show_student_details(student, confidence, status_text, status_type)

                label = f"{name} - {status_text}"

            else:
                box_color = (0, 0, 255)
                label = "Unknown Face"

                if status_placeholder:
                    status_placeholder.error("Unknown face detected.")

                show_unknown_details(confidence)

            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 3)
            cv2.rectangle(
                frame,
                (x, max(0, y - 35)),
                (min(frame.shape[1] - 1, x + max(w, 420)), y),
                box_color,
                -1
            )
            cv2.putText(
                frame,
                label,
                (x + 8, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
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
