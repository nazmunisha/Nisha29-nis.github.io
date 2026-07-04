# -------------------------------------------------------------
# MAIN MENU - ATTENDANCE MANAGEMENT SYSTEM
# -------------------------------------------------------------

from login import login
from student_registration import register_student
from attendance_marking import mark_attendance
from face_registration import register_face
from face_utils import face_recognition_attendance

def main_menu(role):
    while True:
        print("\n==============================================")
        print("        ATTENDANCE MANAGEMENT SYSTEM")
        print("==============================================")
        print("1. Register Student")
        print("2. Mark Attendance (Manual)")
        print("3. Register Face")
        print("4. Face Recognition Attendance")
        print("5. Logout")
        print("6. Exit Program")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            register_student()

        elif choice == "2":
            mark_attendance()

        elif choice == "3":
            register_face()

        elif choice == "4":
            face_recognition_attendance()

        elif choice == "5":
            print("\n✔ Logged out successfully.\n")
            return

        elif choice == "6":
            print("\n✔ Exiting program. Goodbye!\n")
            exit()

        else:
            print("\n❌ Invalid choice. Try again.\n")


# -------------------------------------------------------------
# PROGRAM STARTS HERE
# -------------------------------------------------------------
if __name__ == "__main__":
    role = login()
    if role:
        main_menu(role)