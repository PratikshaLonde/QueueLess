import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "queueless.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():

    conn = get_db()

    try:

        # =========================================================
        # STUDENTS TABLE
        # =========================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                college_id TEXT,
                college_name TEXT,
                college_location TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        student_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        }

        student_new_columns = [
            ("college_id", "TEXT"),
            ("college_name", "TEXT"),
            ("college_location", "TEXT"),
            ("created_at", "TIMESTAMP")
        ]

        for col, definition in student_new_columns:

            if col not in student_columns:

                conn.execute(
                    f"ALTER TABLE students ADD COLUMN {col} {definition}"
                )


        # =========================================================
        # SERVICES TABLE
        # =========================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                average_service_time INTEGER NOT NULL DEFAULT 5,
                status TEXT NOT NULL DEFAULT 'OPEN'
            )
        """)

        service_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(services)"
            ).fetchall()
        }


        if "name" not in service_columns:

            conn.execute(
                "ALTER TABLE services ADD COLUMN name TEXT"
            )

            if "service_name" in service_columns:

                conn.execute("""
                    UPDATE services
                    SET name = service_name
                    WHERE name IS NULL
                """)


        if "category" not in service_columns:

            conn.execute(
                "ALTER TABLE services ADD COLUMN category TEXT"
            )

            if "service_type" in service_columns:

                conn.execute("""
                    UPDATE services
                    SET category = service_type
                    WHERE category IS NULL
                """)


        service_new_columns = [
            ("description", "TEXT"),
            ("average_service_time", "INTEGER DEFAULT 5"),
            ("status", "TEXT DEFAULT 'OPEN'")
        ]

        for col, definition in service_new_columns:

            if col not in service_columns:

                conn.execute(
                    f"ALTER TABLE services ADD COLUMN {col} {definition}"
                )


        # =========================================================
        # QUEUES TABLE
        # =========================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                queue_number INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'WAITING',
                called_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY(student_id)
                    REFERENCES students(id),
                FOREIGN KEY(service_id)
                    REFERENCES services(id)
            )
        """)

        queue_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(queues)"
            ).fetchall()
        }


        queue_new_columns = [
            ("called_at", "TIMESTAMP"),
            ("completed_at", "TIMESTAMP"),
            ("item_name", "TEXT"),
            ("estimated_time", "INTEGER")
        ]

        for col, definition in queue_new_columns:

            if col not in queue_columns:

                conn.execute(
                    f"ALTER TABLE queues ADD COLUMN {col} {definition}"
                )


        # =========================================================
        # FEEDBACK TABLE
        # =========================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                student_name TEXT,
                rating INTEGER DEFAULT 5,
                message TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id)
                    REFERENCES students(id)
            )
        """)

        feedback_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(feedback)"
            ).fetchall()
        }


        feedback_new_columns = [
            ("student_name", "TEXT"),
            ("rating", "INTEGER DEFAULT 5"),
            ("message", "TEXT"),
            ("feedback", "TEXT"),
            ("created_at", "TIMESTAMP")
        ]

        for col, definition in feedback_new_columns:

            if col not in feedback_columns:

                conn.execute(
                    f"ALTER TABLE feedback ADD COLUMN {col} {definition}"
                )


        conn.execute("""
            UPDATE feedback
            SET message = feedback
            WHERE
                (message IS NULL OR message = '')
                AND feedback IS NOT NULL
        """)

        conn.execute("""
            UPDATE feedback
            SET feedback = message
            WHERE
                (feedback IS NULL OR feedback = '')
                AND message IS NOT NULL
        """)


        # =========================================================
        # CREATE SERVICES
        # =========================================================

        services = [

            (
                "College Canteen",
                "Food",
                "Food and canteen services",
                2
            ),

            (
                "Admin Office",
                "Administration",
                "General college administration",
                5
            ),

            (
                "Computer Lab",
                "Computer",
                "Computer lab assistance",
                3
            ),

            (
                "Library",
                "Library",
                "Library services and assistance",
                4
            ),

            (
                "Accounts Office",
                "Accounts",
                "Fees and accounts related services",
                5
            ),

            (
                "Examination Cell",
                "Examination",
                "Exam forms and examination services",
                5
            )

        ]


        # =========================================================
        # INSERT MISSING SERVICES
        # =========================================================

        for name, category, description, avg_time in services:

            existing = conn.execute(
                """
                SELECT id
                FROM services
                WHERE LOWER(name) = LOWER(?)
                """,
                (name,)
            ).fetchone()


            if existing is None:

                conn.execute(
                    """
                    INSERT INTO services
                    (
                        name,
                        category,
                        description,
                        average_service_time,
                        status
                    )
                    VALUES (?, ?, ?, ?, 'OPEN')
                    """,
                    (
                        name,
                        category,
                        description,
                        avg_time
                    )
                )


        # =========================================================
        # SERVICE-SPECIFIC WORK OPTIONS
        # =========================================================
        #
        # Format:
        # service name
        #     work name
        #     time in minutes
        #
        # These are used by the student College Services page.
        # =========================================================

        SERVICE_OPTIONS = {

            "Admin Office": [

                ("Admission", 20),

                ("Issue Fee Receipt", 5),

                ("Bonafide Certificate", 10),

                ("Document Verification", 10),

                ("Scholarship/Form Submission", 15),

                ("ID Card Related Work", 10)

            ],


            "Computer Lab": [

                ("Generate Email & Password", 5),

                ("Password Reset", 3),

                ("Software Installation", 15),

                ("Printing", 2),

                ("Assignment Submission", 5),

                ("Computer/Lab Assistance", 10)

            ],


            "Library": [

                ("Issue Library Card", 5),

                ("New Book Issue", 3),

                ("Book Return", 2),

                ("Book Renewal", 2),

                ("Fine Payment", 3),

                ("Library Account Update", 5)

            ],


            "College Canteen": [

                ("Tea", 1),

                ("Coffee", 2),

                ("Sandwich", 5),

                ("Burger", 10),

                ("Noodles", 15),

                ("Special Meal", 20),

                ("Pizza", 30)

            ],


            "Accounts Office": [

                ("Fee Payment", 5),

                ("Fee Receipt", 5),

                ("Scholarship Payment", 10),

                ("Refund Request", 15),

                ("Account Verification", 10),

                ("Payment Issue", 10)

            ],


            "Examination Cell": [

                ("Exam Registration", 10),

                ("Hall Ticket Issue", 5),

                ("Marks Card", 10),

                ("Exam Form Correction", 15),

                ("Certificate Request", 10),

                ("Exam Related Help", 5)

            ]

        }


        # =========================================================
        # ITEM OPTIONS TABLE
        # =========================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS service_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                estimated_time INTEGER NOT NULL DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(service_id)
                    REFERENCES services(id)
                    ON DELETE CASCADE
            )
        """)


        # =========================================================
        # ADD CORRECT OPTIONS WITHOUT DUPLICATES
        # =========================================================

        for service_name, options in SERVICE_OPTIONS.items():

            service = conn.execute(
                """
                SELECT id
                FROM services
                WHERE LOWER(name) = LOWER(?)
                """,
                (service_name,)
            ).fetchone()


            if service is None:
                continue


            service_id = service["id"]


            for item_name, estimated_time in options:

                existing_option = conn.execute(
                    """
                    SELECT id
                    FROM service_options
                    WHERE service_id = ?
                    AND LOWER(item_name) = LOWER(?)
                    """,
                    (
                        service_id,
                        item_name
                    )
                ).fetchone()


                if existing_option is None:

                    conn.execute(
                        """
                        INSERT INTO service_options
                        (
                            service_id,
                            item_name,
                            estimated_time
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            service_id,
                            item_name,
                            estimated_time
                        )
                    )


        # =========================================================
        # COMMIT EVERYTHING
        # =========================================================

        conn.commit()


        print()
        print("==============================================")
        print(" QueueLess database initialized successfully")
        print("==============================================")
        print(f"Database: {DATABASE}")
        print()


        # Show services

        service_rows = conn.execute(
            """
            SELECT
                id,
                name,
                average_service_time,
                status
            FROM services
            ORDER BY id
            """
        ).fetchall()


        print("Services:")

        for row in service_rows:

            print(
                f"  {row['id']}. "
                f"{row['name']} "
                f"({row['average_service_time']} min) "
                f"[{row['status']}]"
            )


        print()


        # Show work options count

        option_rows = conn.execute(
            """
            SELECT
                s.name,
                COUNT(so.id) AS total
            FROM services s
            LEFT JOIN service_options so
                ON so.service_id = s.id
            GROUP BY s.id
            ORDER BY s.id
            """
        ).fetchall()


        print("Work options:")

        for row in option_rows:

            print(
                f"  {row['name']}: "
                f"{row['total']} options"
            )


        print()


    except Exception as e:

        conn.rollback()

        print()
        print("Database initialization failed.")
        print("Error:", e)
        print()

        raise


    finally:

        conn.close()


if __name__ == "__main__":

    init_db()