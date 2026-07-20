"""
One-time password migration utility.

Run:
    python migrate_passwords.py

It converts old plain-text passwords in the users and teachers
tables into bcrypt hashes while keeping the same login passwords.
"""

from database import get_connection
from password_utils import hash_password, is_bcrypt_hash


def migrate_table(cursor, table_name, id_column):
    cursor.execute(
        f"SELECT {id_column}, password FROM {table_name}"
    )

    rows = cursor.fetchall()
    migrated = 0

    for record_id, stored_password in rows:
        if not is_bcrypt_hash(stored_password):
            cursor.execute(
                f"UPDATE {table_name} SET password=%s "
                f"WHERE {id_column}=%s",
                (hash_password(stored_password), record_id)
            )
            migrated += 1

    return migrated


def main():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        users_migrated = migrate_table(
            cursor, "users", "user_id"
        )
        teachers_migrated = migrate_table(
            cursor, "teachers", "teacher_id"
        )

        conn.commit()

        print(
            f"Migration completed. Users updated: {users_migrated}; "
            f"Teachers updated: {teachers_migrated}"
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
