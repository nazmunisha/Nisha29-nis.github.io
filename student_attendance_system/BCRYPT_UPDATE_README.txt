BCRYPT PASSWORD SECURITY UPDATE
================================

Updated modules:
- auth.py
- database.py
- student_management.py
- teacher_management.py
- email_utils.py
- password_utils.py

New utility:
- migrate_passwords.py

WHAT CHANGED
------------
1. New student passwords are hashed before insertion into users.
2. New teacher passwords are hashed when registration is submitted.
3. Approved teacher accounts reuse the existing bcrypt hash.
4. Login now loads the account by username and checks the password
   using bcrypt.
5. Existing plain-text passwords are automatically converted to
   bcrypt when ensure_schema() runs.
6. A manual migration utility is included.

HOW TO APPLY TO YOUR EXISTING DATABASE
--------------------------------------
Option A:
Run the Streamlit application normally. ensure_schema() will migrate
old passwords automatically.

Option B:
Run:
    python migrate_passwords.py

HOW TO VERIFY
-------------
In MySQL Workbench run:

SELECT user_id, username, password, role
FROM users;

Hashed passwords should start with:
    $2a$
    $2b$
or
    $2y$

IMPORTANT
---------
Do not compare password values directly in SQL. bcrypt hashes are
different each time even for the same password. Always use
check_password().

The users can keep using their existing passwords after migration.
