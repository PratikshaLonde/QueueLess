from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import get_db, init_db
from datetime import datetime

app = Flask(__name__)
CORS(app)

import os
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route("/<path:filename>")
def serve_frontend(filename):
    return send_from_directory(PROJECT_DIR, filename)


# =========================================================
# FEEDBACK TABLE
# =========================================================

def create_feedback_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                feedback TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


create_feedback_table()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return send_from_directory(PROJECT_DIR, "index.html")


# =========================================================
# SERVICES
# =========================================================

@app.route("/api/services", methods=["GET"])
def get_services():
    conn = get_db()

    try:
        services = conn.execute("""
            SELECT
                id,
                name,
                category,
                average_service_time,
                status
            FROM services
            WHERE status = 'OPEN'
            ORDER BY id
        """).fetchall()

        return jsonify([dict(service) for service in services])

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        conn.close()


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    full_name = str(data.get("full_name", "")).strip()
    college_id = str(data.get("college_id", "")).strip()
    college_name = str(data.get("college_name", "")).strip()
    college_location = str(
        data.get("college_location", "")
    ).strip()
    password = str(data.get("password", "")).strip()

    if not full_name:
        return jsonify({
            "success": False,
            "message": "Full name is required"
        }), 400

    if not college_name:
        return jsonify({
            "success": False,
            "message": "College name is required"
        }), 400

    if not college_location:
        return jsonify({
            "success": False,
            "message": "College location is required"
        }), 400

    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 400

    conn = get_db()

    try:

        existing = conn.execute("""
            SELECT id
            FROM students
            WHERE full_name = ?
        """, (full_name,)).fetchone()

        if existing:
            return jsonify({
                "success": False,
                "message": "Student already exists"
            }), 400

        # Check current students table columns
        columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        ]

        # Database with college_id
        if "college_id" in columns:

            cursor = conn.execute("""
                INSERT INTO students
                (
                    full_name,
                    college_id,
                    college_name,
                    college_location,
                    password
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                full_name,
                college_id,
                college_name,
                college_location,
                password
            ))

        # Database without college_id
        else:

            cursor = conn.execute("""
                INSERT INTO students
                (
                    full_name,
                    college_name,
                    college_location,
                    password
                )
                VALUES (?, ?, ?, ?)
            """, (
                full_name,
                college_name,
                college_location,
                password
            ))

        conn.commit()

        student_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "student": {
                "id": student_id,
                "full_name": full_name,
                "college_id": college_id,
                "college_name": college_name,
                "college_location": college_location
            },
            "student_id": student_id,
            "full_name": full_name
        }), 201

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    full_name = str(
        data.get("full_name", "")
    ).strip()

    password = str(
        data.get("password", "")
    ).strip()

    if not full_name or not password:
        return jsonify({
            "success": False,
            "message": "Name and password are required"
        }), 400

    conn = get_db()

    try:

        student = conn.execute("""
            SELECT *
            FROM students
            WHERE full_name = ?
            AND password = ?
        """, (
            full_name,
            password
        )).fetchone()

        if not student:
            return jsonify({
                "success": False,
                "message": "Invalid name or password"
            }), 401

        student_data = dict(student)

        return jsonify({
            "success": True,
            "message": "Login successful",
            "student": student_data,
            "student_id": student_data["id"],
            "full_name": student_data["full_name"]
        })

    finally:
        conn.close()


# =========================================================
# JOIN QUEUE
# =========================================================

@app.route("/api/join", methods=["POST"])
def join_queue():

    data = request.get_json() or {}

    student_id = data.get("student_id")
    service_id = data.get("service_id")

    if not student_id or not service_id:
        return jsonify({
            "success": False,
            "message": "student_id and service_id are required"
        }), 400

    conn = get_db()

    try:

        service = conn.execute("""
            SELECT *
            FROM services
            WHERE id = ?
        """, (service_id,)).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        if service["status"] != "OPEN":
            return jsonify({
                "success": False,
                "message": "This service is currently not accepting new queues"
            }), 400

        existing = conn.execute("""
            SELECT *
            FROM queues
            WHERE student_id = ?
            AND service_id = ?
            AND status IN ('WAITING', 'SERVING')
        """, (
            student_id,
            service_id
        )).fetchone()

        if existing:
            return jsonify({
                "success": False,
                "message": "You are already in this queue",
                "queue_number": existing["queue_number"],
                "status": existing["status"]
            }), 400

        last_active_queue = conn.execute("""
            SELECT MAX(queue_number) AS max_number
            FROM queues
            WHERE service_id = ?
            AND status IN ('WAITING', 'SERVING')
        """, (service_id,)).fetchone()

        if last_active_queue["max_number"] is None:
            queue_number = 1
        else:
            queue_number = last_active_queue["max_number"] + 1

        cursor = conn.execute("""
            INSERT INTO queues
            (
                student_id,
                service_id,
                queue_number,
                status
            )
            VALUES (?, ?, ?, 'WAITING')
        """, (
            student_id,
            service_id,
            queue_number
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Joined queue successfully",
            "queue_id": cursor.lastrowid,
            "queue_number": queue_number
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        conn.close()


# =========================================================
# MY QUEUES
# =========================================================

@app.route("/api/my-queues/<int:student_id>", methods=["GET"])
def my_queues(student_id):

    conn = get_db()

    try:

        queues = conn.execute("""
            SELECT
                q.id,
                q.student_id,
                q.service_id,
                q.queue_number,
                q.joined_at,
                q.status,
                s.name AS service_name,
                s.average_service_time
            FROM queues q
            JOIN services s
                ON q.service_id = s.id
            WHERE q.student_id = ?
            AND q.status IN ('WAITING', 'SERVING')
            ORDER BY q.joined_at
        """, (student_id,)).fetchall()

        result = []

        for queue in queues:

            people_ahead = conn.execute("""
                SELECT COUNT(*) AS count
                FROM queues
                WHERE service_id = ?
                AND status = 'WAITING'
                AND queue_number < ?
            """, (
                queue["service_id"],
                queue["queue_number"]
            )).fetchone()["count"]

            if queue["status"] == "SERVING":
                people_ahead = 0

            position = people_ahead + 1

            estimated_wait = (
                people_ahead *
                queue["average_service_time"]
            )

            if queue["status"] == "SERVING":
                expected_turn = "NOW"

            elif people_ahead == 0:
                expected_turn = "NEXT"

            else:
                expected_turn = f"~{estimated_wait} min"

            result.append({
                "id": queue["id"],
                "student_id": queue["student_id"],
                "service_id": queue["service_id"],
                "service_name": queue["service_name"],
                "queue_number": queue["queue_number"],
                "joined_at": queue["joined_at"],
                "status": queue["status"],
                "average_service_time":
                    queue["average_service_time"],
                "people_ahead": people_ahead,
                "position": position,
                "estimated_wait_minutes":
                    estimated_wait,
                "expected_turn": expected_turn
            })

        return jsonify(result)

    finally:
        conn.close()


# =========================================================
# QUEUE STATUS
# =========================================================

@app.route("/api/queue-status/<int:queue_id>", methods=["GET"])
def queue_status(queue_id):

    conn = get_db()

    try:

        queue = conn.execute("""
            SELECT
                q.id,
                q.student_id,
                q.service_id,
                q.queue_number,
                q.joined_at,
                q.status,
                s.name AS service_name,
                s.average_service_time
            FROM queues q
            JOIN services s
                ON q.service_id = s.id
            WHERE q.id = ?
        """, (queue_id,)).fetchone()

        if not queue:
            return jsonify({
                "success": False,
                "message": "Queue not found"
            }), 404

        people_ahead = conn.execute("""
            SELECT COUNT(*) AS count
            FROM queues
            WHERE service_id = ?
            AND status = 'WAITING'
            AND queue_number < ?
        """, (
            queue["service_id"],
            queue["queue_number"]
        )).fetchone()["count"]

        if queue["status"] == "SERVING":
            people_ahead = 0

        estimated_wait = (
            people_ahead *
            queue["average_service_time"]
        )

        return jsonify({
            "success": True,
            "queue_id": queue["id"],
            "student_id": queue["student_id"],
            "service_id": queue["service_id"],
            "service_name": queue["service_name"],
            "queue_number": queue["queue_number"],
            "status": queue["status"],
            "people_ahead": people_ahead,
            "position": people_ahead + 1,
            "estimated_wait_minutes": estimated_wait
        })

    finally:
        conn.close()


# =========================================================
# LEAVE QUEUE
# =========================================================

@app.route("/api/leave", methods=["POST"])
def leave_queue():

    data = request.get_json() or {}

    queue_id = data.get("queue_id")

    if not queue_id:
        return jsonify({
            "success": False,
            "message": "queue_id is required"
        }), 400

    conn = get_db()

    try:

        queue = conn.execute("""
            SELECT *
            FROM queues
            WHERE id = ?
        """, (queue_id,)).fetchone()

        if not queue:
            return jsonify({
                "success": False,
                "message": "Queue not found"
            }), 404

        if queue["status"] == "SERVING":
            return jsonify({
                "success": False,
                "message": "You cannot leave while being served"
            }), 400

        if queue["status"] != "WAITING":
            return jsonify({
                "success": False,
                "message": "Queue is not active"
            }), 400

        conn.execute("""
            UPDATE queues
            SET status = 'LEFT'
            WHERE id = ?
        """, (queue_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Left queue successfully"
        })

    finally:
        conn.close()


# =========================================================
# SERVE NEXT
# =========================================================

@app.route("/api/serve-next/<int:service_id>", methods=["POST"])
def serve_next(service_id):

    conn = get_db()

    try:

        service = conn.execute("""
            SELECT *
            FROM services
            WHERE id = ?
        """, (service_id,)).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        if service["status"] != "OPEN":
            return jsonify({
                "success": False,
                "message": "Service must be OPEN"
            }), 400

        currently_serving = conn.execute("""
            SELECT *
            FROM queues
            WHERE service_id = ?
            AND status = 'SERVING'
        """, (service_id,)).fetchone()

        if currently_serving:
            return jsonify({
                "success": False,
                "message": "A student is already being served",
                "queue_number":
                    currently_serving["queue_number"]
            }), 400

        next_person = conn.execute("""
            SELECT *
            FROM queues
            WHERE service_id = ?
            AND status = 'WAITING'
            ORDER BY queue_number ASC
            LIMIT 1
        """, (service_id,)).fetchone()

        if not next_person:
            return jsonify({
                "success": False,
                "message": "No students are waiting"
            }), 404

        conn.execute("""
            UPDATE queues
            SET status = 'SERVING'
            WHERE id = ?
        """, (next_person["id"],))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Next student is now being served",
            "queue_id": next_person["id"],
            "queue_number":
                next_person["queue_number"]
        })

    finally:
        conn.close()


# =========================================================
# COMPLETE SERVICE
# =========================================================

@app.route("/api/complete/<int:queue_id>", methods=["POST"])
def complete_service(queue_id):

    conn = get_db()

    try:

        queue = conn.execute("""
            SELECT *
            FROM queues
            WHERE id = ?
        """, (queue_id,)).fetchone()

        if not queue:
            return jsonify({
                "success": False,
                "message": "Queue not found"
            }), 404

        if queue["status"] != "SERVING":
            return jsonify({
                "success": False,
                "message":
                    "This queue is not currently being served"
            }), 400

        conn.execute("""
            UPDATE queues
            SET status = 'SERVED',
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (queue_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Service completed successfully"
        })

    finally:
        conn.close()


# =========================================================
# RECENTLY COMPLETED QUEUE
# =========================================================

@app.route("/api/my-completed/<int:student_id>", methods=["GET"])
def my_completed(student_id):
    conn = get_db()
    try:
        queue = conn.execute("""
            SELECT
                q.id,
                q.student_id,
                q.service_id,
                q.queue_number,
                q.status,
                q.completed_at,
                s.name AS service_name
            FROM queues q
            JOIN services s ON q.service_id = s.id
            WHERE q.student_id = ?
              AND q.status = 'SERVED'
            ORDER BY q.id DESC
            LIMIT 1
        """, (student_id,)).fetchone()

        if not queue:
            return jsonify({"success": True, "completed": None})

        return jsonify({
            "success": True,
            "completed": dict(queue)
        })
    finally:
        conn.close()


# =========================================================
# ADMIN QUEUE STATUS
# =========================================================

@app.route("/api/admin-queue-status", methods=["GET"])
def admin_queue_status():

    conn = get_db()

    try:

        services = conn.execute("""
            SELECT
                id,
                name,
                category,
                average_service_time,
                status
            FROM services
            ORDER BY id
        """).fetchall()

        result = []

        for service in services:

            waiting_count = conn.execute("""
                SELECT COUNT(*) AS count
                FROM queues
                WHERE service_id = ?
                AND status = 'WAITING'
            """, (service["id"],)).fetchone()["count"]

            serving = conn.execute("""
                SELECT q.id, q.queue_number, s.full_name
                FROM queues q
                LEFT JOIN students s ON q.student_id = s.id
                WHERE q.service_id = ?
                AND q.status = 'SERVING'
                LIMIT 1
            """, (service["id"],)).fetchone()

            next_student = conn.execute("""
                SELECT q.id, q.queue_number, s.full_name
                FROM queues q
                LEFT JOIN students s ON q.student_id = s.id
                WHERE q.service_id = ?
                AND q.status = 'WAITING'
                ORDER BY q.queue_number ASC
                LIMIT 1
            """, (service["id"],)).fetchone()

            completed_today = conn.execute("""
                SELECT COUNT(*) AS count
                FROM queues
                WHERE service_id = ?
                  AND status = 'SERVED'
                  AND date(COALESCE(completed_at, joined_at), 'localtime') = date('now', 'localtime')
            """, (service["id"],)).fetchone()["count"]

            result.append({
                "id": service["id"],
                "name": service["name"],
                "category": service["category"],
                "average_service_time":
                    service["average_service_time"],
                "status": service["status"],
                "waiting_count": waiting_count,
                "serving_queue_id":
                    serving["id"] if serving else None,
                "serving_queue_number":
                    serving["queue_number"] if serving else None,
                "serving_student_name":
                    serving["full_name"] if serving else None,
                "next_queue_id":
                    next_student["id"] if next_student else None,
                "next_queue_number":
                    next_student["queue_number"] if next_student else None,
                "next_student_name":
                    next_student["full_name"] if next_student else None,
                "completed_today": completed_today,
                "completed_today": completed_today
            })

        return jsonify(result)

    finally:
        conn.close()


# =========================================================
# PAUSE SERVICE
# =========================================================

@app.route("/api/pause-service/<int:service_id>", methods=["POST"])
def pause_service(service_id):

    conn = get_db()

    try:

        service = conn.execute("""
            SELECT *
            FROM services
            WHERE id = ?
        """, (service_id,)).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        conn.execute("""
            UPDATE services
            SET status = 'PAUSED'
            WHERE id = ?
        """, (service_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                f"{service['name']} paused successfully"
        })

    finally:
        conn.close()


# =========================================================
# RESUME SERVICE
# =========================================================

@app.route("/api/resume-service/<int:service_id>", methods=["POST"])
def resume_service(service_id):

    conn = get_db()

    try:

        service = conn.execute("""
            SELECT *
            FROM services
            WHERE id = ?
        """, (service_id,)).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        conn.execute("""
            UPDATE services
            SET status = 'OPEN'
            WHERE id = ?
        """, (service_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                f"{service['name']} resumed successfully"
        })

    finally:
        conn.close()


# =========================================================
# OPEN SERVICE
# =========================================================

@app.route("/api/open-service/<int:service_id>", methods=["POST"])
def open_service(service_id):

    conn = get_db()

    try:

        service = conn.execute("""
            SELECT *
            FROM services
            WHERE id = ?
        """, (service_id,)).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        conn.execute("""
            UPDATE services
            SET status = 'OPEN'
            WHERE id = ?
        """, (service_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                f"{service['name']} opened successfully"
        })

    finally:
        conn.close()


# =========================================================
# CLOSE SERVICE
# =========================================================

@app.route("/api/close-service/<int:service_id>", methods=["POST"])
def close_service(service_id):

    conn = get_db()

    try:

        service = conn.execute("""
            SELECT *
            FROM services
            WHERE id = ?
        """, (service_id,)).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        conn.execute("""
            UPDATE services
            SET status = 'CLOSED'
            WHERE id = ?
        """, (service_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                f"{service['name']} closed successfully"
        })

    finally:
        conn.close()


# =========================================================
# FEEDBACK
# =========================================================

ADMIN_SECRET_KEY = "QL-ADMIN-9174"

def ensure_feedback_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                student_name TEXT,
                rating INTEGER DEFAULT 5,
                message TEXT,
                feedback TEXT,
                service_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(feedback)").fetchall()}
        migrations = {
            "student_name": "ALTER TABLE feedback ADD COLUMN student_name TEXT",
            "rating": "ALTER TABLE feedback ADD COLUMN rating INTEGER DEFAULT 5",
            "message": "ALTER TABLE feedback ADD COLUMN message TEXT",
            "feedback": "ALTER TABLE feedback ADD COLUMN feedback TEXT",
            "service_id": "ALTER TABLE feedback ADD COLUMN service_id INTEGER"
        }
        for column, sql in migrations.items():
            if column not in columns:
                conn.execute(sql)
        conn.execute("UPDATE feedback SET message = feedback WHERE (message IS NULL OR message = '') AND feedback IS NOT NULL")
        conn.execute("UPDATE feedback SET feedback = message WHERE (feedback IS NULL OR feedback = '') AND message IS NOT NULL")
        conn.execute("UPDATE feedback SET rating = 5 WHERE rating IS NULL OR rating < 1 OR rating > 5")
        conn.commit()
    finally:
        conn.close()

ensure_feedback_table()

@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    student_id = request.args.get("student_id")
    conn = get_db()
    try:
        if student_id:
            rows = conn.execute("""
                SELECT
                    f.id, f.student_id,
                    COALESCE(f.student_name, s.full_name) AS student_name,
                    COALESCE(f.rating, 5) AS rating,
                    COALESCE(f.message, f.feedback, '') AS message,
                    COALESCE(f.feedback, f.message, '') AS feedback,
                    f.service_id, f.created_at
                FROM feedback f
                LEFT JOIN students s ON f.student_id = s.id
                WHERE f.student_id = ?
                ORDER BY f.id DESC
            """, (student_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT
                    f.id, f.student_id,
                    COALESCE(f.student_name, s.full_name) AS student_name,
                    COALESCE(f.rating, 5) AS rating,
                    COALESCE(f.message, f.feedback, '') AS message,
                    COALESCE(f.feedback, f.message, '') AS feedback,
                    f.service_id, f.created_at
                FROM feedback f
                LEFT JOIN students s ON f.student_id = s.id
                ORDER BY f.id DESC
            """).fetchall()
        return jsonify({"success": True, "feedback": [dict(row) for row in rows]})
    except Exception as e:
        print("GET FEEDBACK ERROR:", e)
        return jsonify({"success": False, "message": str(e), "feedback": []}), 500
    finally:
        conn.close()

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json() or {}
    student_id = data.get("student_id")
    raw_feedback = str(data.get("feedback") or data.get("message") or "").strip()
    try:
        rating = int(data.get("rating") or 5)
    except (TypeError, ValueError):
        rating = 5
    service_id = data.get("service_id")

    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required"}), 400
    if not raw_feedback:
        return jsonify({"success": False, "message": "Feedback cannot be empty"}), 400
    if len(raw_feedback) > 500:
        return jsonify({"success": False, "message": "Feedback must be 500 characters or less"}), 400
    rating = max(1, min(5, rating))

    conn = get_db()
    try:
        student = conn.execute("SELECT id, full_name FROM students WHERE id = ?", (student_id,)).fetchone()
        if not student:
            return jsonify({"success": False, "message": "Student not found"}), 404

        service_name = ""
        if service_id:
            service = conn.execute("SELECT name FROM services WHERE id = ?", (service_id,)).fetchone()
            if service:
                service_name = service["name"]

        message = raw_feedback
        if service_name and not raw_feedback.startswith("[Service:"):
            message = f"[Service: {service_name}] {raw_feedback}"

        cursor = conn.execute("""
            INSERT INTO feedback
                (student_id, student_name, rating, message, feedback, service_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, student["full_name"], rating, message, message, service_id))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": cursor.lastrowid
        }), 201
    except Exception as e:
        conn.rollback()
        print("SAVE FEEDBACK ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/feedback/<int:feedback_id>", methods=["DELETE"])
def delete_student_feedback(feedback_id):
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required"}), 400

    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM feedback WHERE id = ? AND student_id = ?", (feedback_id, student_id)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "Feedback not found"}), 404
        conn.execute("DELETE FROM feedback WHERE id = ? AND student_id = ?", (feedback_id, student_id))
        conn.commit()
        return jsonify({"success": True, "message": "Feedback deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/admin-feedback", methods=["GET"])
def admin_feedback():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT
                f.id, f.student_id,
                COALESCE(f.student_name, s.full_name) AS student_name,
                COALESCE(f.rating, 5) AS rating,
                COALESCE(f.message, f.feedback, '') AS message,
                COALESCE(f.feedback, f.message, '') AS feedback,
                f.service_id, f.created_at
            FROM feedback f
            LEFT JOIN students s ON f.student_id = s.id
            ORDER BY f.id DESC
        """).fetchall()
        return jsonify({"success": True, "feedback": [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/admin-feedback/<int:feedback_id>", methods=["DELETE"])
def delete_feedback(feedback_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "Feedback not found"}), 404
        conn.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Feedback deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/admin-feedback", methods=["DELETE"])
def delete_all_feedback():
    conn = get_db()
    try:
        result = conn.execute("DELETE FROM feedback")
        conn.commit()
        return jsonify({"success": True, "message": f"All feedback deleted successfully ({result.rowcount} removed)"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


# =========================================================
# ADMIN DAILY ACTIVITY
# =========================================================

@app.route("/api/admin-daily-activity", methods=["GET"])
def admin_daily_activity():
    requested_date = request.args.get("date")
    if not requested_date:
        requested_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    try:
        services = conn.execute("SELECT id, name FROM services ORDER BY id").fetchall()
        activity = []
        for service in services:
            count = conn.execute("""
                SELECT COUNT(*) AS count
                FROM queues
                WHERE service_id = ?
                  AND status IN ('SERVED', 'COMPLETED')
                  AND completed_at IS NOT NULL
                  AND date(completed_at, 'localtime') = ?
            """, (service["id"], requested_date)).fetchone()["count"]
            activity.append({
                "service_id": service["id"],
                "service_name": service["name"],
                "name": service["name"],
                "completed_count": count,
                "completed": count,
                "count": count
            })
        return jsonify({"success": True, "date": requested_date, "activity": activity})
    except Exception as e:
        print("ADMIN DAILY ACTIVITY ERROR:", e)
        return jsonify({"success": False, "message": str(e), "activity": []}), 500
    finally:
        conn.close()

@app.route("/api/admin-previous-activity", methods=["GET"])
def admin_previous_activity():
    from datetime import timedelta
    previous_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    conn = get_db()
    try:
        services = conn.execute("SELECT id, name FROM services ORDER BY id").fetchall()
        activity = []
        for service in services:
            count = conn.execute("""
                SELECT COUNT(*) AS count
                FROM queues
                WHERE service_id = ?
                  AND status IN ('SERVED', 'COMPLETED')
                  AND completed_at IS NOT NULL
                  AND date(completed_at, 'localtime') = ?
            """, (service["id"], previous_date)).fetchone()["count"]
            activity.append({
                "service_id": service["id"],
                "service_name": service["name"],
                "name": service["name"],
                "completed_count": count,
                "completed": count,
                "count": count
            })
        return jsonify({"success": True, "date": previous_date, "previous_date": previous_date, "activity": activity})
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "activity": []}), 500
    finally:
        conn.close()

# =========================================================
# DEBUG DATABASE
# =========================================================

@app.route("/api/debug-db", methods=["GET"])
def debug_db():

    conn = get_db()

    try:

        students = conn.execute("""
            SELECT *
            FROM students
            ORDER BY id
        """).fetchall()

        services = conn.execute("""
            SELECT *
            FROM services
            ORDER BY id
        """).fetchall()

        queues = conn.execute("""
            SELECT *
            FROM queues
            ORDER BY id
        """).fetchall()

        return jsonify({
            "students":
                [dict(x) for x in students],

            "services":
                [dict(x) for x in services],

            "queues":
                [dict(x) for x in queues]
        })

    finally:
        conn.close()


# =========================================================
# ADMIN REGISTER
# =========================================================

@app.route("/api/admin-register", methods=["POST"])
def admin_register():
    data = request.get_json() or {}
    full_name = str(data.get("full_name", "")).strip()
    admin_id = str(data.get("admin_id", "")).strip()
    college_name = str(data.get("college_name", "")).strip()
    department = str(data.get("department", "")).strip()
    password = str(data.get("password", "")).strip()
    secret_key = str(data.get("secret_key", data.get("secret", ""))).strip()

    if not full_name or not admin_id or not password:
        return jsonify({"success": False, "message": "Full name, Admin ID and password are required."}), 400

    if secret_key != ADMIN_SECRET_KEY:
        return jsonify({"success": False, "message": "Invalid admin secret key."}), 403

    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                admin_id TEXT UNIQUE NOT NULL,
                college_name TEXT,
                department TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        existing = conn.execute("SELECT id FROM admins WHERE admin_id = ?", (admin_id,)).fetchone()
        if existing:
            return jsonify({"success": False, "message": "Admin ID already exists."}), 409
        conn.execute("""
            INSERT INTO admins
                (full_name, admin_id, college_name, department, password)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, admin_id, college_name, department, password))
        conn.commit()
        return jsonify({"success": True, "message": "Admin registered successfully.", "login_id": admin_id}), 201
    except Exception as e:
        conn.rollback()
        print("ADMIN REGISTER ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/api/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    admin_id = str(data.get("admin_id", "")).strip()
    password = str(data.get("password", "")).strip()
    if not admin_id or not password:
        return jsonify({"success": False, "message": "Admin ID and password are required."}), 400
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                admin_id TEXT UNIQUE NOT NULL,
                college_name TEXT,
                department TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        admin = conn.execute("""SELECT id, full_name, admin_id, college_name, department FROM admins WHERE admin_id = ? AND password = ?""", (admin_id, password)).fetchone()
        if not admin:
            return jsonify({"success": False, "message": "Invalid Admin ID or password."}), 401
        return jsonify({"success": True, "message": "Admin login successful.", "admin": dict(admin)}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# =========================================================
# GENERIC SERVICE STATUS
# =========================================================

@app.route("/api/service-status/<int:service_id>", methods=["POST"])
def service_status(service_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip().upper()
    allowed = {"OPEN", "PAUSED", "CLOSED"}

    if status not in allowed:
        return jsonify({
            "success": False,
            "message": "Status must be OPEN, PAUSED or CLOSED"
        }), 400

    conn = get_db()
    try:
        service = conn.execute(
            "SELECT id, name FROM services WHERE id = ?",
            (service_id,)
        ).fetchone()

        if not service:
            return jsonify({
                "success": False,
                "message": "Service not found"
            }), 404

        conn.execute(
            "UPDATE services SET status = ? WHERE id = ?",
            (status, service_id)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": f"{service['name']} is now {status}",
            "status": status
        })
    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    finally:
        conn.close()


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    init_db()
    ensure_feedback_table()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )