# Attendance Management System

## Run

```cmd
py -m pip install -r requirements.txt
python -m streamlit run dashboard.py
```

## Default Admin

Username: `admin`  
Password: `admin123`

## Notes

- Uses OpenCV only.
- No `dlib`.
- No `face_recognition`.
- Live webcam attendance opens in a separate OpenCV window.
- Press `Q` in the webcam window to stop live attendance.


## Password Security

This project uses `bcrypt` password hashing through `password_utils.py`.

- New student passwords are hashed before saving to the `users` table.
- Teacher passwords are hashed when the admin approves the teacher.
- Forgot Password stores the temporary password as a hash.
- Change Password stores the new password as a hash.
- Existing plain-text accounts can still log in because `check_password()` supports migration.

Install bcrypt:

```bash
pip install bcrypt
```



## Live Camera Inside Dashboard

The Live Face Attendance page now displays the webcam feed directly inside the Streamlit dashboard instead of opening a separate OpenCV window.

To use it:

1. Login as Admin or Teacher.
2. Open **Live Face Attendance**.
3. Click **Start Live Attendance**.
4. Allow webcam permission if Windows asks.
5. The camera feed will run inside the dashboard for 60 seconds.

