from database import get_db, init_db


def add_default_services():

    # Make sure database and tables exist
    init_db()

    db = get_db()

    services = [
        (
            "College Canteen",
            "Food and canteen services",
            2
        ),
        (
            "Admin Office",
            "General college administration",
            5
        ),
        (
            "Computer Lab",
            "Computer lab assistance",
            3
        ),
        (
            "Library",
            "Library services and assistance",
            4
        ),
        (
            "Accounts Office",
            "Fees and accounts related services",
            5
        ),
        (
            "Examination Cell",
            "Exam forms and examination services",
            5
        )
    ]

    for name, description, average_time in services:

        existing = db.execute(
            """
            SELECT id
            FROM services
            WHERE name = ?
            """,
            (name,)
        ).fetchone()

        if existing is None:

            db.execute(
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
                    name,
                    description,
                    average_time
                )
            )

    db.commit()
    db.close()

    print("Default college services added successfully!")


if __name__ == "__main__":
    add_default_services()