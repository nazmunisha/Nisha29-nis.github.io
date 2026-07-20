# ==========================================================
# Import Required Libraries
# ==========================================================

# Used to generate secure random passwords
import secrets

# Used for letters (A-Z, a-z) and numbers (0-9)
import string

# Used to send emails through Gmail SMTP
import smtplib

# Used to create email messages
from email.message import EmailMessage

# Streamlit library for creating the web application
import streamlit as st

# Import MySQL database connection
from database import get_connection

# Import Gmail credentials
from email_utils import SENDER_EMAIL, APP_PASSWORD
from password_utils import hash_password, check_password


# ==========================================================
# Function: init_session()
# Purpose : Initialize user session when application starts
# ==========================================================
def init_session():

    # Default session values
    defaults = {
        "logged_in": False,
        "role": None,
        "user_id": None,
        "student_id": None,
        "username": None,
    }

    # If session variable doesn't exist, create it
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==========================================================
# Function: logout()
# Purpose : Logout current user
# ==========================================================
def logout():

    # Clear all login information
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.student_id = None
    st.session_state.username = None

    # Display logout message
    st.warning("You have logged out.")

    # Stop the current Streamlit page
    st.stop()


# ==========================================================
# Function: login_sidebar()
# Purpose : Display login form and authenticate user
# ==========================================================
def login_sidebar():

    # Create login form inside the Streamlit sidebar
    with st.sidebar:

        # Display application logo and title
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-logo">🎓 AMS</div>
            <div class="sidebar-subtitle">Attendance Management System</div>
        </div>
        <div class="sidebar-section">Login</div>
        """, unsafe_allow_html=True)

        # User selects login role
        login_mode = st.radio("Login As", ["Admin", "Teacher", "Student"])

        # User enters username
        username = st.text_input("Username")

        # User enters password
        password = st.text_input("Password", type="password")

        # Login button
        login_btn = st.button("Login")

    # Execute login when button is clicked
    if login_btn:

        try:

            # Connect to MySQL database
            conn = get_connection()
            cur = conn.cursor(dictionary=True)

            # Find the account using the username only.
            # Passwords stored as bcrypt hashes cannot be compared
            # directly inside the SQL query.
            cur.execute(
                "SELECT * FROM users WHERE username=%s",
                (username.strip(),)
            )

            user = cur.fetchone()

            # Verify the typed password using bcrypt.
            if not user or not check_password(password.strip(), user["password"]):
                conn.close()
                st.session_state.logged_in = False
                st.error("Invalid username or password.")
                return

            # Migration support:
            # If an old account still has a plain-text password,
            # replace it with a bcrypt hash after a successful login.
            if not str(user["password"]).startswith(("$2a$", "$2b$", "$2y$")):
                upgraded_hash = hash_password(password.strip())
                cur.execute(
                    "UPDATE users SET password=%s WHERE user_id=%s",
                    (upgraded_hash, user["user_id"])
                )
                conn.commit()
                user["password"] = upgraded_hash

            conn.close()

            # Check whether selected role matches database role
            if user["role"] != login_mode:
                st.session_state.logged_in = False
                st.error(f"This account is not a {login_mode} account.")
                return

            # Store login details inside session
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user_id = user["user_id"]
            st.session_state.student_id = user.get("student_id")
            st.session_state.username = user["username"]

            # Successful login message
            st.success(f"Login successful as {user['role']}.")

        except Exception as e:
            st.error(f"Login error: {e}")


# ==========================================================
# Function: generate_temp_password()
# Purpose : Generate a secure temporary password
# ==========================================================
def generate_temp_password():

    # Generate four random letters
    letters = "".join(secrets.choice(string.ascii_letters) for _ in range(4))

    # Generate four random digits
    digits = "".join(secrets.choice(string.digits) for _ in range(4))

    # Final password example: Temp@AbCd1234
    return "Temp@" + letters + digits


# ==========================================================
# Function: send_password_reset_email()
# Purpose : Send temporary password to user's email
# ==========================================================
def send_password_reset_email(user_email, display_name, username, temp_password):

    # Create email object
    msg = EmailMessage()

    # Email subject
    msg["Subject"] = "Attendance System Password Reset"

    # Sender email
    msg["From"] = SENDER_EMAIL

    # Receiver email
    msg["To"] = user_email

    # Email content
    msg.set_content(f"""
Hello {display_name},

Your Attendance Management System password has been reset.

Username: {username}
Temporary Password: {temp_password}

Please log in using this temporary password and change it immediately.

Regards,
Attendance Management System
""")

    # Connect securely to Gmail SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        # Login using Gmail App Password
        smtp.login(SENDER_EMAIL, APP_PASSWORD)

        # Send email
        smtp.send_message(msg)


# ==========================================================
# Function: reset_user_password()
# Purpose : Forgot Password feature
# ==========================================================
def reset_user_password(identifier):

    """
    User enters either:

    • Username
    OR
    • Registered Email Address

    System searches Student account first,
    then Teacher account.

    If found,
    a temporary password is generated,
    saved into database,
    and emailed to the user.
    """

    # Remove unnecessary spaces
    identifier = identifier.strip()

    # Check empty input
    if not identifier:
        return False, "Please enter username or email."

    # Connect to database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        # -------------------------------
        # Search Student Account
        # -------------------------------
        cur.execute("""
            SELECT u.user_id,
                   u.username,
                   s.name AS display_name,
                   s.email
            FROM users u
            JOIN students s
            ON u.student_id = s.student_id
            WHERE u.role='Student'
            AND (u.username=%s OR s.email=%s)
            LIMIT 1
        """, (identifier, identifier))

        account = cur.fetchone()

        # -------------------------------
        # Search Teacher Account
        # -------------------------------
        if not account:

            cur.execute("""
                SELECT u.user_id,
                       u.username,
                       t.full_name AS display_name,
                       t.email
                FROM users u
                JOIN teachers t
                ON u.username=t.username
                WHERE u.role='Teacher'
                AND (u.username=%s OR t.email=%s)
                LIMIT 1
            """, (identifier, identifier))

            account = cur.fetchone()

        # -------------------------------
        # Check Admin Account
        # -------------------------------
        if not account:

            cur.execute("""
                SELECT user_id
                FROM users
                WHERE role='Admin'
                AND username=%s
                LIMIT 1
            """, (identifier,))

            admin = cur.fetchone()

            if admin:
                return False, "Admin password reset is not available."

        # No account found
        if not account:
            return False, "No student or teacher account found."

        # Email missing
        if not account.get("email"):
            return False, "Registered email not found."

        # Generate temporary password
        temp_password = generate_temp_password()

        # Update database password
        # Store only the hashed version of the temporary password.
        hashed_temp_password = hash_password(temp_password)

        cur.execute(
            "UPDATE users SET password=%s WHERE user_id=%s",
            (hashed_temp_password, account["user_id"])
        )

        # Save changes
        conn.commit()

        # Send password reset email
        send_password_reset_email(
            account["email"],
            account.get("display_name") or account["username"],
            account["username"],
            temp_password
        )

        return True, "Temporary password sent successfully."

    except Exception as e:

        # Undo database changes if error occurs
        conn.rollback()

        return False, f"Password reset failed: {e}"

    finally:

        # Always close database connection
        conn.close()


# ==========================================================
# Function: forgot_password_ui()
# Purpose : Display Forgot Password interface
# ==========================================================
def forgot_password_ui():

    # Create collapsible section
    with st.expander("🔑 Forgot Password"):

        # Create form
        with st.form("forgot_password_form"):

            # Username or email input
            identifier = st.text_input("Username or Email")

            # Submit button
            submit = st.form_submit_button("Send Temporary Password")

        # Execute password reset
        if submit:

            ok, msg = reset_user_password(identifier)

            if ok:
                st.success(msg)
            else:
                st.error(msg)