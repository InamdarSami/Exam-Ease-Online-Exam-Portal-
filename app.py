from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "examease_secret_key"



def get_db_connection():
    connection = sqlite3.connect("exam_ease.db", timeout=10)
    connection.row_factory = sqlite3.Row
    return connection



def create_database():

    connection = get_db_connection()
    cursor = connection.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            roll_number TEXT NOT NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            marks_per_question REAL NOT NULL,
            negative_marking REAL DEFAULT 0,
            number_of_sets INTEGER DEFAULT 1,
            result_published INTEGER DEFAULT 0
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            marks REAL NOT NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            set_number INTEGER NOT NULL,
            question_id INTEGER NOT NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            score REAL NOT NULL,
            total_marks REAL NOT NULL,
            correct INTEGER NOT NULL,
            wrong INTEGER NOT NULL,
            unanswered INTEGER NOT NULL,
            percentage REAL NOT NULL
        )
    """)


    admin = connection.execute("""
        SELECT id FROM admins
        WHERE email = ?
    """, ("admin@examease.com",)).fetchone()

    if admin is None:

        connection.execute("""
            INSERT INTO admins
            (name, email, password)
            VALUES (?, ?, ?)
        """, (
            "ExamEase Admin",
            "admin@examease.com",
            "admin123"
        ))

    connection.commit()
    connection.close()



@app.route("/")
def home():
    return render_template("index.html")



@app.route("/student-register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        name = request.form["name"]
        roll_number = request.form["roll_number"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        try:

            connection.execute("""
                INSERT INTO students
                (name, roll_number, email, password)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                roll_number,
                email,
                password
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "Email or Roll Number already registered!"

        connection.close()

        return redirect(url_for("student_login"))

    return render_template("student_register.html")



@app.route("/teacher-register", methods=["GET", "POST"])
def teacher_register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        try:

            connection.execute("""
                INSERT INTO teachers
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                password
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "Email already registered!"

        connection.close()

        return redirect(url_for("teacher_login"))

    return render_template("teacher_register.html")



@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        connection = get_db_connection()

        student = connection.execute("""
            SELECT *
            FROM students
            WHERE email = ?
            AND password = ?
        """, (
            request.form["email"],
            request.form["password"]
        )).fetchone()

        connection.close()

        if student:

            session["student_id"] = student["id"]
            session["student_name"] = student["name"]

            return redirect(url_for("student_dashboard"))

        return "Invalid email or password!"

    return render_template("student_login.html")



@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login():

    if request.method == "POST":

        connection = get_db_connection()

        teacher = connection.execute("""
            SELECT *
            FROM teachers
            WHERE email = ?
            AND password = ?
        """, (
            request.form["email"],
            request.form["password"]
        )).fetchone()

        connection.close()

        if teacher:

            session["teacher_id"] = teacher["id"]
            session["teacher_name"] = teacher["name"]

            return redirect(url_for("teacher_dashboard"))

        return "Invalid email or password!"

    return render_template("teacher_login.html")



@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        connection = get_db_connection()

        admin = connection.execute("""
            SELECT *
            FROM admins
            WHERE email = ?
            AND password = ?
        """, (
            request.form["email"],
            request.form["password"]
        )).fetchone()

        connection.close()

        if admin:

            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]

            return redirect(url_for("admin_dashboard"))

        return "Invalid admin email or password!"

    return render_template("admin_login.html")



@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    connection = get_db_connection()

    exams = connection.execute("""
        SELECT *
        FROM exams
        ORDER BY id DESC
    """).fetchall()

    results = connection.execute("""
        SELECT
            results.*,
            exams.result_published
        FROM results
        JOIN exams
        ON results.exam_id = exams.id
        WHERE results.student_id = ?
        ORDER BY results.id DESC
    """, (
        session["student_id"],
    )).fetchall()

    connection.close()

    return render_template(
        "student_dashboard.html",
        exams=exams,
        results=results
    )



@app.route("/teacher-dashboard")
def teacher_dashboard():

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    exams = connection.execute("""
        SELECT *
        FROM exams
        WHERE teacher_id = ?
        ORDER BY id DESC
    """, (
        session["teacher_id"],
    )).fetchall()

    connection.close()

    return render_template(
        "teacher_dashboard.html",
        exams=exams
    )



@app.route("/create-exam", methods=["GET", "POST"])
def create_exam():

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    if request.method == "POST":

        connection = get_db_connection()

        cursor = connection.execute("""
            INSERT INTO exams (
                teacher_id,
                exam_name,
                subject,
                duration,
                total_questions,
                marks_per_question,
                negative_marking,
                number_of_sets
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["teacher_id"],
            request.form["exam_name"],
            request.form["subject"],
            request.form["duration"],
            request.form["total_questions"],
            request.form["marks_per_question"],
            request.form["negative_marking"],
            request.form["number_of_sets"]
        ))

        exam_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "add_questions",
                exam_id=exam_id
            )
        )

    return render_template("create_exam.html")



@app.route("/add-questions/<int:exam_id>", methods=["GET", "POST"])
def add_questions(exam_id):

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ?
        AND teacher_id = ?
    """, (
        exam_id,
        session["teacher_id"]
    )).fetchone()

    if exam is None:

        connection.close()

        return "Exam not found or you don't have permission."

    if request.method == "POST":

        question_texts = request.form.getlist(
            "question_text[]"
        )

        option_as = request.form.getlist(
            "option_a[]"
        )

        option_bs = request.form.getlist(
            "option_b[]"
        )

        option_cs = request.form.getlist(
            "option_c[]"
        )

        option_ds = request.form.getlist(
            "option_d[]"
        )

        correct_answers = request.form.getlist(
            "correct_answer[]"
        )

        marks_list = request.form.getlist(
            "marks[]"
        )

        if len(question_texts) != exam["total_questions"]:

            connection.close()

            return (
                f"Please enter exactly "
                f"{exam['total_questions']} questions."
            )

        connection.execute("""
            DELETE FROM question_sets
            WHERE exam_id = ?
        """, (exam_id,))

        connection.execute("""
            DELETE FROM questions
            WHERE exam_id = ?
        """, (exam_id,))

        for i in range(len(question_texts)):

            connection.execute("""
                INSERT INTO questions (
                    exam_id,
                    question_text,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    correct_answer,
                    marks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exam_id,
                question_texts[i],
                option_as[i],
                option_bs[i],
                option_cs[i],
                option_ds[i],
                correct_answers[i],
                marks_list[i]
            ))

        connection.commit()
        connection.close()

        return redirect(
            url_for("generate_sets", exam_id=exam_id)
        )

    connection.close()

    return render_template(
        "add_questions.html",
        exam=exam
    )



@app.route("/my-exams")
def my_exams():

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    exams = connection.execute("""
        SELECT *
        FROM exams
        WHERE teacher_id = ?
        ORDER BY id DESC
    """, (
        session["teacher_id"],
    )).fetchall()

    connection.close()

    return render_template(
        "my_exams.html",
        exams=exams
    )



@app.route("/generate-sets/<int:exam_id>")
def generate_sets(exam_id):

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ?
        AND teacher_id = ?
    """, (
        exam_id,
        session["teacher_id"]
    )).fetchone()

    if exam is None:

        connection.close()

        return "Exam not found or you don't have permission."

    questions = connection.execute("""
        SELECT *
        FROM questions
        WHERE exam_id = ?
        ORDER BY id
    """, (
        exam_id,
    )).fetchall()

    if len(questions) != exam["total_questions"]:

        connection.close()

        return (
            f"Please add exactly "
            f"{exam['total_questions']} "
            f"questions before generating sets."
        )

    number_of_sets = int(
        exam["number_of_sets"]
    )

    if number_of_sets < 1:

        connection.close()

        return "Number of sets must be at least 1."

    connection.execute("""
        DELETE FROM question_sets
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    previous_orders = []

    for set_number in range(
        1,
        number_of_sets + 1
    ):

        shuffled = list(questions)

        for _ in range(100):

            random.shuffle(shuffled)

            current_order = tuple(
                q["id"]
                for q in shuffled
            )

            if current_order not in previous_orders:
                break

        else:

            base = list(questions)

            shift = (
                (set_number - 1)
                % len(base)
            )

            shuffled = (
                base[shift:]
                + base[:shift]
            )

            current_order = tuple(
                q["id"]
                for q in shuffled
            )

        previous_orders.append(
            current_order
        )

        for question in shuffled:

            connection.execute("""
                INSERT INTO question_sets (
                    exam_id,
                    set_number,
                    question_id
                )
                VALUES (?, ?, ?)
            """, (
                exam_id,
                set_number,
                question["id"]
            ))

    connection.commit()

    rows = connection.execute("""
        SELECT
            qs.set_number,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer
        FROM question_sets qs
        JOIN questions q
        ON qs.question_id = q.id
        WHERE qs.exam_id = ?
        ORDER BY qs.set_number, qs.id
    """, (
        exam_id,
    )).fetchall()

    connection.close()

    sets = {}

    for row in rows:

        sets.setdefault(
            row["set_number"],
            []
        ).append(row)

    return render_template(
        "set_preview.html",
        exam=exam,
        sets=sets
    )



@app.route("/start-exam/<int:exam_id>")
def start_exam(exam_id):

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    connection = get_db_connection()

    existing = connection.execute("""
        SELECT id
        FROM results
        WHERE student_id = ?
        AND exam_id = ?
        LIMIT 1
    """, (
        session["student_id"],
        exam_id
    )).fetchone()

    if existing:

        connection.close()

        return redirect(
            url_for("exam_submitted", exam_id=exam_id)
        )

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ?
    """, (
        exam_id,
    )).fetchone()

    if exam is None:

        connection.close()

        return "Exam not found."

    sets = connection.execute("""
        SELECT DISTINCT set_number
        FROM question_sets
        WHERE exam_id = ?
        ORDER BY set_number
    """, (
        exam_id,
    )).fetchall()

    if not sets:

        connection.close()

        return (
            "Question sets have not been "
            "generated for this exam yet."
        )

    exam_set_key = f"exam_set_{exam_id}"

    if exam_set_key not in session:
        session[exam_set_key] = random.choice(sets)["set_number"]

    set_number = session[exam_set_key]

    valid_set_numbers = [
        row["set_number"]
        for row in sets
    ]

    if set_number not in valid_set_numbers:
        session[exam_set_key] = random.choice(sets)["set_number"]
        set_number = session[exam_set_key]

    questions = connection.execute("""
        SELECT
            q.id,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer,
            q.marks
        FROM question_sets qs
        JOIN questions q
        ON qs.question_id = q.id
        WHERE qs.exam_id = ?
        AND qs.set_number = ?
        ORDER BY qs.id
    """, (
        exam_id,
        set_number
    )).fetchall()

    connection.close()

    if not questions:

        return "No questions found for this set."

    return render_template(
        "take_exam.html",
        exam=exam,
        questions=questions,
        set_number=set_number
    )



@app.route(
    "/submit-exam/<int:exam_id>",
    methods=["POST"]
)
def submit_exam(exam_id):

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    student_id = session["student_id"]

    connection = get_db_connection()

    existing = connection.execute("""
        SELECT id
        FROM results
        WHERE student_id = ?
        AND exam_id = ?
        LIMIT 1
    """, (
        student_id,
        exam_id
    )).fetchone()

    if existing:

        connection.close()

        return redirect(
            url_for("exam_submitted", exam_id=exam_id)
        )

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ?
    """, (
        exam_id,
    )).fetchone()

    if exam is None:

        connection.close()

        return "Exam not found."

    set_number = request.form.get(
        "set_number"
    )

    if not set_number:

        connection.close()

        return "Exam set information is missing."

    questions = connection.execute("""
        SELECT
            q.id,
            q.correct_answer,
            q.marks
        FROM question_sets qs
        JOIN questions q
        ON qs.question_id = q.id
        WHERE qs.exam_id = ?
        AND qs.set_number = ?
        ORDER BY qs.id
    """, (
        exam_id,
        set_number
    )).fetchall()

    if not questions:

        connection.close()

        return "No questions found for this exam."

    correct = 0
    wrong = 0
    unanswered = 0

    score = 0.0

    for question in questions:

        answer = request.form.get(
            f"question_{question['id']}"
        )

        if not answer:

            unanswered += 1

        elif (
            answer.upper()
            == question["correct_answer"].upper()
        ):

            correct += 1

            score += float(
                question["marks"]
            )

        else:

            wrong += 1

            score -= float(
                exam["negative_marking"]
            )

    score = max(score, 0)

    total_marks = sum(
        float(q["marks"])
        for q in questions
    )

    if total_marks:

        percentage = (
            score
            / total_marks
            * 100
        )

    else:

        percentage = 0

    connection.execute("""
        INSERT INTO results (
            student_id,
            exam_id,
            score,
            total_marks,
            correct,
            wrong,
            unanswered,
            percentage
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        exam_id,
        score,
        total_marks,
        correct,
        wrong,
        unanswered,
        percentage
    ))

    connection.commit()
    connection.close()

    session.pop(f"exam_set_{exam_id}", None)

    return redirect(
        url_for("exam_submitted", exam_id=exam_id)
    )



@app.route("/exam-submitted/<int:exam_id>")
def exam_submitted(exam_id):

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    connection = get_db_connection()

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ?
    """, (exam_id,)).fetchone()

    connection.close()

    if exam is None:
        return redirect(url_for("student_dashboard"))

    return render_template(
        "exam_submitted.html",
        exam=exam
    )


@app.route("/student-results")
def student_results():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    connection = get_db_connection()

    results = connection.execute("""
        SELECT
            results.*,
            exams.exam_name,
            exams.subject
        FROM results
        JOIN exams
        ON results.exam_id = exams.id
        WHERE results.student_id = ?
        AND exams.result_published = 1
        ORDER BY results.id DESC
    """, (
        session["student_id"],
    )).fetchall()

    connection.close()

    return render_template(
        "student_results.html",
        results=results
    )



@app.route("/teacher-results/<int:exam_id>")
def teacher_results(exam_id):

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ?
        AND teacher_id = ?
    """, (
        exam_id,
        session["teacher_id"]
    )).fetchone()

    if exam is None:

        connection.close()

        return (
            "Exam not found or "
            "you don't have permission."
        )

    results = connection.execute("""
        SELECT
            results.*,
            students.name,
            students.email,
            students.roll_number
        FROM results
        JOIN students
        ON results.student_id = students.id
        WHERE results.exam_id = ?
        ORDER BY results.percentage DESC
    """, (
        exam_id,
    )).fetchall()

    connection.close()

    return render_template(
        "teacher_results.html",
        exam=exam,
        results=results
    )



@app.route("/publish-results/<int:exam_id>")
def publish_results(exam_id):

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    connection.execute("""
        UPDATE exams
        SET result_published = 1
        WHERE id = ?
        AND teacher_id = ?
    """, (
        exam_id,
        session["teacher_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("teacher_dashboard")
    )



@app.route("/hide-results/<int:exam_id>")
def hide_results(exam_id):

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    connection.execute("""
        UPDATE exams
        SET result_published = 0
        WHERE id = ?
        AND teacher_id = ?
    """, (
        exam_id,
        session["teacher_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("teacher_dashboard")
    )



@app.route("/delete-exam/<int:exam_id>")
def delete_exam(exam_id):

    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    connection = get_db_connection()

    exam = connection.execute("""
        SELECT id
        FROM exams
        WHERE id = ?
        AND teacher_id = ?
    """, (
        exam_id,
        session["teacher_id"]
    )).fetchone()

    if exam is None:

        connection.close()

        return (
            "Exam not found or "
            "you don't have permission."
        )

    connection.execute("""
        DELETE FROM results
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    connection.execute("""
        DELETE FROM question_sets
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    connection.execute("""
        DELETE FROM questions
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    connection.execute("""
        DELETE FROM exams
        WHERE id = ?
    """, (
        exam_id,
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("teacher_dashboard")
    )





@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    students = connection.execute("""
        SELECT *
        FROM students
        ORDER BY id DESC
    """).fetchall()

    teachers = connection.execute("""
        SELECT *
        FROM teachers
        ORDER BY id DESC
    """).fetchall()

    exams = connection.execute("""
        SELECT
            exams.*,
            teachers.name AS teacher_name
        FROM exams
        JOIN teachers
        ON exams.teacher_id = teachers.id
        ORDER BY exams.id DESC
    """).fetchall()

    results = connection.execute("""
        SELECT
            results.*,
            students.name AS student_name,
            students.roll_number,
            exams.exam_name
        FROM results
        JOIN students
        ON results.student_id = students.id
        JOIN exams
        ON results.exam_id = exams.id
        ORDER BY results.id DESC
    """).fetchall()

    total_students = connection.execute("""
        SELECT COUNT(*) AS count
        FROM students
    """).fetchone()["count"]

    total_teachers = connection.execute("""
        SELECT COUNT(*) AS count
        FROM teachers
    """).fetchone()["count"]

    total_exams = connection.execute("""
        SELECT COUNT(*) AS count
        FROM exams
    """).fetchone()["count"]

    total_results = connection.execute("""
        SELECT COUNT(*) AS count
        FROM results
    """).fetchone()["count"]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        teachers=teachers,
        exams=exams,
        results=results,
        total_students=total_students,
        total_teachers=total_teachers,
        total_exams=total_exams,
        total_results=total_results
    )



@app.route(
    "/admin/delete-student/<int:student_id>"
)
def admin_delete_student(student_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM results
        WHERE student_id = ?
    """, (
        student_id,
    ))

    connection.execute("""
        DELETE FROM students
        WHERE id = ?
    """, (
        student_id,
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_dashboard")
    )



@app.route(
    "/admin/delete-teacher/<int:teacher_id>"
)
def admin_delete_teacher(teacher_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    exams = connection.execute("""
        SELECT id
        FROM exams
        WHERE teacher_id = ?
    """, (
        teacher_id,
    )).fetchall()

    for exam in exams:

        exam_id = exam["id"]

        connection.execute("""
            DELETE FROM results
            WHERE exam_id = ?
        """, (
            exam_id,
        ))

        connection.execute("""
            DELETE FROM question_sets
            WHERE exam_id = ?
        """, (
            exam_id,
        ))

        connection.execute("""
            DELETE FROM questions
            WHERE exam_id = ?
        """, (
            exam_id,
        ))

        connection.execute("""
            DELETE FROM exams
            WHERE id = ?
        """, (
            exam_id,
        ))

    connection.execute("""
        DELETE FROM teachers
        WHERE id = ?
    """, (
        teacher_id,
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_dashboard")
    )



@app.route(
    "/admin/delete-exam/<int:exam_id>"
)
def admin_delete_exam(exam_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM results
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    connection.execute("""
        DELETE FROM question_sets
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    connection.execute("""
        DELETE FROM questions
        WHERE exam_id = ?
    """, (
        exam_id,
    ))

    connection.execute("""
        DELETE FROM exams
        WHERE id = ?
    """, (
        exam_id,
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_dashboard")
    )



@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )



if __name__ == "__main__":

    create_database()

    app.run(debug=True)
