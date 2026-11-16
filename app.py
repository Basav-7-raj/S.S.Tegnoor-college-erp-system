from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3, hashlib, os, json
from datetime import date, timedelta
from functools import wraps
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "sstegnoor_erp_2024_secure"
DB  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "college.db")
DIR = os.path.dirname(os.path.abspath(__file__))

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def grade(pct):
    return "A+" if pct>=90 else "A" if pct>=80 else "B+" if pct>=70 else "B" if pct>=60 else "C" if pct>=50 else "D" if pct>=40 else "F"

def calculate_gpa(marks_data):
    """Calculate GPA from marks data.
    Accepts list of dicts with either 'marks_obtained'/'best_marks' key and 'total_marks'.
    """
    if not marks_data:
        return 0.0
    total_points = 0
    total_credits = 0
    grade_points = {"A+": 10, "A": 9, "B+": 8, "B": 7, "C": 6, "D": 5, "F": 0}

    for m in marks_data:
        # Support both 'marks_obtained' and 'best_marks' key names
        obtained = m.get('best_marks') or m.get('marks_obtained') or 0
        total    = m.get('total_marks') or 0
        pct = (obtained / total * 100) if total else 0
        g = grade(pct)
        points = grade_points.get(g, 0)
        credits = 4  # Default credits
        total_points += points * credits
        total_credits += credits

    return round(total_points / total_credits, 2) if total_credits else 0.0

def table_exists(conn, name):
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

# ── Template Globals ──────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return dict(now=date.today, grade_fn=grade)

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ── Auth ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        role     = request.form["role"]
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (username, hp(password), role)).fetchone()
        conn.close()
        if user:
            session["user"]       = username
            session["role"]       = role
            session["related_id"] = user["related_id"]
            return redirect(url_for("admin_dashboard" if role=="admin" else "student_dashboard"))
        flash("Invalid credentials or wrong role!", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── ADMIN ─────────────────────────────────────────────────────────────────────
@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    conn = get_db()
    stats = {
        "students":  conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "teachers":  conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0],
        "marks":     conn.execute("SELECT COUNT(*) FROM marks").fetchone()[0],
        "materials": conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0],
        "attendance": conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0],
    }

    # Top performer
    topper = conn.execute("""
        SELECT m.roll_no, s.name, s.course,
               ROUND(AVG(CAST(m.marks_obtained AS FLOAT)/m.total_marks*100),1) as avg
        FROM marks m LEFT JOIN students s ON m.roll_no=s.roll_no
        GROUP BY m.roll_no ORDER BY avg DESC LIMIT 1
    """).fetchone()

    recent = conn.execute("SELECT name,course,current_sem FROM students ORDER BY id DESC LIMIT 6").fetchall()

    # Branch counts
    branch_counts = conn.execute(
        "SELECT course as branch, COUNT(*) as cnt FROM students GROUP BY course"
    ).fetchall()

    # Semester distribution for dashboard chart
    sem_dist = conn.execute("""
        SELECT course, current_sem, COUNT(*) as cnt 
        FROM students GROUP BY course, current_sem ORDER BY course, current_sem
    """).fetchall()

    # Low attendance students (below 75%)
    low_attendance = conn.execute("""
        SELECT s.roll_no, s.name, s.course, s.current_sem,
               COUNT(CASE WHEN a.status='Present' THEN 1 END) as present,
               COUNT(*) as total,
               ROUND(COUNT(CASE WHEN a.status='Present' THEN 1 END) * 100.0 / COUNT(*), 1) as pct
        FROM students s
        LEFT JOIN attendance a ON s.roll_no = a.roll_no AND a.semester = s.current_sem
        WHERE s.current_sem IS NOT NULL
        GROUP BY s.roll_no
        HAVING total > 0 AND pct < 75
        ORDER BY pct ASC
        LIMIT 5
    """).fetchall()

    conn.close()
    return render_template("admin/dashboard.html", stats=stats, topper=topper, 
                          recent=recent, branch_counts=branch_counts, 
                          sem_dist=sem_dist, low_attendance=low_attendance)

# ── STUDENTS ──────────────────────────────────────────────────────────────────
@app.route("/admin/students", methods=["GET","POST"])
@login_required("admin")
def admin_students():
    conn = get_db()
    COURSES = ["BCA","BSC","BCOM"]

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            try:
                conn.execute("""INSERT INTO students(roll_no,name,email,phone,course,current_sem,section,enrolled_date) 
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (request.form["roll_no"], request.form["name"], request.form["email"],
                     request.form["phone"], request.form["course"],
                     request.form.get("sem",1), request.form.get("section",""), str(date.today())))
                sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                uname = request.form.get("uname","").strip()
                upass = request.form.get("upass","").strip()
                if uname and upass:
                    try: 
                        conn.execute("INSERT INTO users(username,password,role,related_id) VALUES(?,?,?,?)",
                                      (uname, hp(upass), "student", sid))
                    except: flash("Username already taken!", "warning")
                conn.commit(); flash("Student added!", "success")
            except sqlite3.IntegrityError: flash("Roll No already exists!", "danger")

        elif action == "update_sem":
            conn.execute("UPDATE students SET current_sem=? WHERE id=?",
                         (request.form["sem"], request.form["sid"]))
            conn.commit(); flash("Semester updated!", "success")

        elif action == "delete":
            sid = request.form["sid"]
            conn.execute("DELETE FROM users WHERE role='student' AND related_id=?", (sid,))
            conn.execute("DELETE FROM students WHERE id=?", (sid,))
            conn.commit(); flash("Deleted!", "success")

        elif action == "import_csv":
            f = request.files.get("csvfile")
            if f:
                import csv, io
                text = f.read().decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(text))
                added = skipped = 0
                for row in reader:
                    g = lambda *ks: next((str(row.get(k,"") or "").strip() for k in ks if row.get(k)),"")
                    roll = g("roll_no","rollno","roll")
                    name = g("name","student_name")
                    if not roll or not name: skipped+=1; continue
                    try:
                        conn.execute("""INSERT INTO students(roll_no,name,email,phone,course,current_sem,section,enrolled_date) 
                            VALUES(?,?,?,?,?,?,?,?)""",
                            (roll,name,g("email"),g("phone"),g("course"),g("sem","current_sem") or 1,g("section"),str(date.today())))
                        added+=1
                    except: skipped+=1
                conn.commit(); flash(f"Imported {added}, skipped {skipped}.", "success")

    q = request.args.get("q","")
    cf = request.args.get("course","All")
    sf = request.args.get("sem","All")

    sql = "SELECT * FROM students WHERE 1=1"
    params = []
    if q: sql += " AND (name LIKE ? OR roll_no LIKE ?)"; params += [f"%{q}%"]*2
    if cf != "All": sql += " AND course=?"; params.append(cf)
    if sf != "All": sql += " AND current_sem=?"; params.append(sf)

    students = conn.execute(sql+" ORDER BY course, current_sem, roll_no", params).fetchall()
    conn.close()
    return render_template("admin/students.html", students=students, courses=COURSES, 
                          q=q, cf=cf, sf=sf, sems=list(range(1,7)))

# ── STUDENT DETAIL VIEW ───────────────────────────────────────────────────────
@app.route("/admin/student/<roll_no>")
@login_required("admin")
def admin_student_detail(roll_no):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,)).fetchone()
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))

    # All semester marks
    all_marks = conn.execute("""
        SELECT semester, subject, exam_type, marks_obtained, total_marks, exam_date
        FROM marks WHERE roll_no=? ORDER BY semester, subject, exam_date
    """, (roll_no,)).fetchall()

    # Semester-wise average
    sem_avg = conn.execute("""
        SELECT semester, 
               ROUND(AVG(CAST(marks_obtained AS FLOAT)/total_marks*100),1) as avg,
               COUNT(DISTINCT subject) as subjects
        FROM marks WHERE roll_no=? GROUP BY semester ORDER BY semester
    """, (roll_no,)).fetchall()

    # Attendance summary by semester
    att_summary = conn.execute("""
        SELECT semester, subject,
               COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present
        FROM attendance WHERE roll_no=? GROUP BY semester, subject ORDER BY semester, subject
    """, (roll_no,)).fetchall()

    # Overall attendance by semester
    sem_att = conn.execute("""
        SELECT semester,
               COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present,
               ROUND(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct
        FROM attendance WHERE roll_no=? GROUP BY semester ORDER BY semester
    """, (roll_no,)).fetchall()

    # Calculate GPA for each semester
    gpa_data = {}
    for sem in range(1, 7):
        sem_marks = conn.execute("""
            SELECT subject, MAX(marks_obtained) as best_marks, total_marks
            FROM marks WHERE roll_no=? AND semester=?
            GROUP BY subject
        """, (roll_no, sem)).fetchall()
        if sem_marks:
            gpa_data[sem] = calculate_gpa([dict(m) for m in sem_marks])

    conn.close()
    return render_template("admin/student_detail.html", student=student, all_marks=all_marks,
                          sem_avg=sem_avg, att_summary=att_summary, sem_att=sem_att, 
                          gpa_data=gpa_data, grade_fn=grade)

# ── TEACHERS ──────────────────────────────────────────────────────────────────
@app.route("/admin/teachers", methods=["GET","POST"])
@login_required("admin")
def admin_teachers():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            try:
                conn.execute("""INSERT INTO teachers(name,email,phone,department,subject,designation,joining_date) 
                    VALUES(?,?,?,?,?,?,?)""",
                    (request.form["name"], request.form["email"], request.form["phone"],
                     request.form.get("dept",""), request.form.get("subject",""),
                     request.form.get("designation","Assistant Professor"),
                     str(date.today())))
                tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                uname = request.form.get("uname","").strip()
                upass = request.form.get("upass","").strip()
                if uname and upass:
                    try: 
                        conn.execute("INSERT INTO users(username,password,role,related_id) VALUES(?,?,?,?)",
                                      (uname, hp(upass), "admin", tid))
                    except: flash("Username already taken!", "warning")
                conn.commit(); flash("Teacher added!", "success")
            except Exception as e: flash(f"Error: {str(e)}", "danger")
        elif action == "delete":
            tid = request.form["tid"]
            conn.execute("DELETE FROM users WHERE role='admin' AND related_id=?", (tid,))
            conn.execute("DELETE FROM teachers WHERE id=?", (tid,))
            conn.commit(); flash("Deleted!", "success")

    teachers = conn.execute("""
        SELECT t.*, u.username 
        FROM teachers t 
        LEFT JOIN users u ON t.id=u.related_id AND u.role='admin' 
        ORDER BY t.id DESC
    """).fetchall()
    conn.close()
    return render_template("admin/teachers.html", teachers=teachers)

# ── MARKS ─────────────────────────────────────────────────────────────────────
@app.route("/admin/marks", methods=["GET","POST"])
@login_required("admin")
def admin_marks():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            try:
                m = int(request.form["marks"])
                t = int(request.form["total"])
                if m > t: flash("Marks cannot exceed total!", "danger")
                else:
                    conn.execute("""INSERT INTO marks(roll_no,subject,exam_type,marks_obtained,total_marks,semester,exam_date,entered_by) 
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (request.form["roll_no"], request.form["subject"],
                         request.form["exam_type"], m, t,
                         request.form.get("sem",1),
                         request.form.get("exam_date", str(date.today())),
                         session["user"]))
                    conn.commit(); flash("Marks added!", "success")
            except ValueError: flash("Marks must be numbers!", "danger")
        elif action == "delete":
            conn.execute("DELETE FROM marks WHERE id=?", (request.form["mid"],))
            conn.commit(); flash("Deleted!", "success")
        elif action == "bulk_add":
            # Bulk marks entry for a class
            roll_nos = request.form.getlist("roll_nos")
            subject = request.form.get("subject","")
            exam_type = request.form.get("exam_type","Mid-Term")
            sem = request.form.get("sem", 1)
            exam_date = request.form.get("exam_date", str(date.today()))

            if not subject:
                flash("Please select a subject for bulk entry!", "danger")
            else:
                added = 0
                for roll in roll_nos:
                    marks_key = f"marks_{roll}"
                    total_key = f"total_{roll}"
                    mark_val = request.form.get(marks_key, "").strip()
                    if mark_val:
                        try:
                            m = int(mark_val)
                            t = int(request.form.get(total_key, 100))
                            if m <= t:
                                conn.execute("""INSERT INTO marks(roll_no,subject,exam_type,marks_obtained,total_marks,semester,exam_date,entered_by) 
                                    VALUES(?,?,?,?,?,?,?,?)""",
                                    (roll, subject, exam_type, m, t, sem, exam_date, session["user"]))
                                added += 1
                        except ValueError:
                            pass
                conn.commit()
                flash(f"Bulk marks saved for {added} students!", "success")

    froll  = request.args.get("roll","")
    fsem   = request.args.get("sem","")
    fcourse= request.args.get("course","")

    sql = """SELECT m.*, s.name, s.course FROM marks m 
             LEFT JOIN students s ON m.roll_no=s.roll_no WHERE 1=1"""
    params = []
    if froll: sql += " AND m.roll_no LIKE ?"; params.append(f"%{froll}%")
    if fsem:  sql += " AND m.semester=?"; params.append(fsem)
    if fcourse: sql += " AND s.course=?"; params.append(fcourse)
    marks = conn.execute(sql+" ORDER BY m.id DESC", params).fetchall()

    students = conn.execute("SELECT roll_no,name,course,current_sem FROM students ORDER BY roll_no").fetchall()

    # For bulk entry - get students by course/sem
    bulk_course = request.args.get("bulk_course","BCA")
    bulk_sem = request.args.get("bulk_sem","1")

    bulk_students = []
    if request.args.get("bulk",""):
        bulk_students = conn.execute("""
            SELECT roll_no, name, course, current_sem 
            FROM students WHERE course=? AND current_sem=? 
            ORDER BY roll_no
        """, (bulk_course, bulk_sem)).fetchall()

    bulk_subjects = []
    if bulk_course and bulk_sem:
        bulk_subjects = conn.execute("SELECT name FROM subjects WHERE course=? AND semester=?",
                                      (bulk_course, bulk_sem)).fetchall()

    conn.close()
    return render_template("admin/marks.html", marks=marks, students=students,
                           subjects=[], today=str(date.today()),
                           grade_fn=grade, froll=froll, fsem=fsem, fcourse=fcourse,
                           bulk_students=bulk_students, bulk_subjects=bulk_subjects,
                           bulk_course=bulk_course, bulk_sem=bulk_sem)

# ── DELETE MARK (separate route to avoid nested forms in tables)
@app.route("/admin/marks/delete/<int:mid>")
@login_required("admin")
def admin_delete_mark(mid):
    conn = get_db()
    conn.execute("DELETE FROM marks WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    flash("Mark entry deleted!", "success")
    return redirect(url_for("admin_marks"))

# ── AJAX APIs ─────────────────────────────────────────────────────────────────
@app.route("/api/student_info")
@login_required("admin")
def api_student_info():
    roll = request.args.get("roll","")
    conn = get_db()
    st = conn.execute("SELECT * FROM students WHERE roll_no=?", (roll,)).fetchone()
    if not st:
        conn.close()
        return jsonify({})
    subjects = [r["name"] for r in conn.execute(
        "SELECT name FROM subjects WHERE course=? AND semester=?",
        (st["course"], st["current_sem"])).fetchall()]
    conn.close()
    return jsonify({"name": st["name"], "course": st["course"],
                    "sem": st["current_sem"], "subjects": subjects})

@app.route("/api/student_all_subjects")
@login_required("admin")
def api_student_all_subjects():
    roll = request.args.get("roll","")
    sem = request.args.get("sem","")
    conn = get_db()
    st = conn.execute("SELECT course FROM students WHERE roll_no=?", (roll,)).fetchone()
    if not st:
        conn.close()
        return jsonify([])
    subjects = [r["name"] for r in conn.execute(
        "SELECT name FROM subjects WHERE course=? AND semester=?",
        (st["course"], sem)).fetchall()]
    conn.close()
    return jsonify(subjects)

# ── ATTENDANCE ────────────────────────────────────────────────────────────────
@app.route("/admin/attendance", methods=["GET","POST"])
@login_required("admin")
def admin_attendance():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            subject  = request.form.get("subject","")
            att_date = request.form.get("att_date","")
            semester = request.form.get("semester","")
            rolls    = request.form.getlist("roll_nos")

            if not subject or not att_date or not semester:
                flash("Please fill subject, date and semester!", "danger")
            elif not rolls:
                flash("No students found for this class!", "warning")
            else:
                for roll in rolls:
                    status = request.form.get(f"status_{roll}", "Absent")
                    ex = conn.execute("""SELECT id FROM attendance 
                        WHERE roll_no=? AND subject=? AND date=? AND semester=?""",
                                       (roll,subject,att_date,semester)).fetchone()
                    if ex:
                        conn.execute("""UPDATE attendance SET status=? 
                            WHERE roll_no=? AND subject=? AND date=? AND semester=?""",
                                     (status,roll,subject,att_date,semester))
                    else:
                        conn.execute("""INSERT INTO attendance(roll_no,subject,semester,date,status,marked_by) 
                            VALUES(?,?,?,?,?,?)""",
                                     (roll,subject,semester,att_date,status,session["user"]))
                conn.commit(); flash(f"Attendance saved for {len(rolls)} students!", "success")

    fcourse = request.args.get("course","BCA")
    fsem    = request.args.get("sem","1")
    students = conn.execute(
        "SELECT roll_no,name,current_sem FROM students WHERE course=? AND current_sem=? ORDER BY roll_no",
        (fcourse, fsem)).fetchall()
    subjects = conn.execute(
        "SELECT name FROM subjects WHERE course=? AND semester=?",
        (fcourse, fsem)).fetchall()

    # Attendance records with student names
    records = conn.execute("""
        SELECT a.*, s.name as sname FROM attendance a
        LEFT JOIN students s ON a.roll_no=s.roll_no
        WHERE a.semester=? AND s.course=?
        ORDER BY a.date DESC LIMIT 100
    """, (fsem, fcourse)).fetchall()

    # Low attendance alert
    low_att = conn.execute("""
        SELECT s.roll_no, s.name, 
               COUNT(CASE WHEN a.status='Present' THEN 1 END) as present,
               COUNT(*) as total
        FROM students s
        LEFT JOIN attendance a ON s.roll_no=a.roll_no AND a.semester=? AND a.subject IN 
            (SELECT name FROM subjects WHERE course=? AND semester=?)
        WHERE s.course=? AND s.current_sem=?
        GROUP BY s.roll_no
        HAVING total > 0 AND (present * 100.0 / total) < 75
    """, (fsem, fcourse, fsem, fcourse, fsem)).fetchall()

    conn.close()
    return render_template("admin/attendance.html",
                           students=students, subjects=subjects, records=records,
                           today=str(date.today()), fcourse=fcourse, fsem=fsem,
                           courses=["BCA","BSC","BCOM"], low_att=low_att)

# ── SYLLABUS ──────────────────────────────────────────────────────────────────
@app.route("/admin/syllabus", methods=["GET","POST"])
@login_required("admin")
def admin_syllabus():
    UPLOAD_DIR = os.path.join(DIR, "static", "syllabus")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "upload":
            course = request.form["course"]
            sem    = request.form["sem"]
            title  = request.form["title"]
            desc   = request.form.get("description","")
            fpath  = ""
            f = request.files.get("file")
            if f and f.filename:
                fname = f"{course}_sem{sem}_{f.filename.replace(' ','_')}"
                f.save(os.path.join(UPLOAD_DIR, fname))
                fpath = "syllabus/" + fname
            conn.execute("""INSERT INTO syllabus(course,semester,title,file_path,uploaded_by,upload_date,description) 
                VALUES(?,?,?,?,?,?,?)""",
                (course, sem, title, fpath, session["user"], str(date.today()), desc))
            conn.commit(); flash("Syllabus uploaded!", "success")
        elif action == "delete":
            row = conn.execute("SELECT file_path FROM syllabus WHERE id=?", (request.form["sid"],)).fetchone()
            if row and row["file_path"]:
                fp = os.path.join(DIR, "static", row["file_path"])
                if os.path.exists(fp):
                    try: os.remove(fp)
                    except: pass
            conn.execute("DELETE FROM syllabus WHERE id=?", (request.form["sid"],))
            conn.commit(); flash("Deleted!", "success")

    fcourse = request.args.get("course","BCA")
    syllabus = conn.execute(
        "SELECT * FROM syllabus WHERE course=? ORDER BY semester, id",
        (fcourse,)).fetchall()
    by_sem = {}
    for row in syllabus:
        sem = row["semester"]
        if sem not in by_sem: by_sem[sem] = []
        by_sem[sem].append(row)

    # Build subject list by semester for the template
    subjects = conn.execute(
        "SELECT semester, name FROM subjects WHERE course=? ORDER BY semester", (fcourse,)).fetchall()
    subj_by_sem = {}
    for row in subjects:
        sem = row["semester"]
        if sem not in subj_by_sem: subj_by_sem[sem] = []
        subj_by_sem[sem].append(row["name"])
    conn.close()
    return render_template("admin/syllabus.html", by_sem=by_sem, subj_by_sem=subj_by_sem,
                           fcourse=fcourse, courses=["BCA","BSC","BCOM"])

# ── PERFORMANCE ────────────────────────────────────────────────────────────────
@app.route("/admin/performance")
@login_required("admin")
def admin_performance():
    conn = get_db()

    # Search functionality
    search_roll = request.args.get("roll","")
    search_name = request.args.get("name","")
    search_course = request.args.get("course","")

    # Top 10 students
    toppers = conn.execute("""
        SELECT m.roll_no, s.name, s.course, s.current_sem,
               ROUND(AVG(CAST(m.marks_obtained AS FLOAT)/m.total_marks*100),1) as avg
        FROM marks m LEFT JOIN students s ON m.roll_no=s.roll_no
        GROUP BY m.roll_no ORDER BY avg DESC LIMIT 10
    """).fetchall()

    # All students average (for attention list)
    all_avg = conn.execute("""
        SELECT m.roll_no, s.name, s.course, s.current_sem,
               ROUND(AVG(CAST(m.marks_obtained AS FLOAT)/m.total_marks*100),1) as avg
        FROM marks m LEFT JOIN students s ON m.roll_no=s.roll_no
        GROUP BY m.roll_no ORDER BY avg ASC
    """).fetchall()

    # Grade distribution
    grade_dist = {"A+":0,"A":0,"B+":0,"B":0,"C":0,"D":0,"F":0}
    for row in conn.execute("SELECT marks_obtained,total_marks FROM marks WHERE total_marks>0"):
        pct = (row[0]/row[1])*100
        grade_dist[grade(pct)] += 1

    # Semester-wise average — convert to dicts so tojson works in template
    sem_avg = [dict(r) for r in conn.execute("""
        SELECT s.course, m.semester,
               ROUND(AVG(CAST(m.marks_obtained AS FLOAT)/m.total_marks*100),1) as avg
        FROM marks m LEFT JOIN students s ON m.roll_no=s.roll_no
        GROUP BY s.course, m.semester ORDER BY s.course, m.semester
    """).fetchall()]

    # Course-wise performance
    course_perf = conn.execute("""
        SELECT s.course,
               ROUND(AVG(CAST(m.marks_obtained AS FLOAT)/m.total_marks*100),1) as avg,
               COUNT(DISTINCT s.roll_no) as students
        FROM marks m LEFT JOIN students s ON m.roll_no=s.roll_no
        GROUP BY s.course
    """).fetchall()

    # Search results
    search_results = None
    if search_roll or search_name or search_course:
        sql = """
            SELECT s.roll_no, s.name, s.course, s.current_sem,
                   ROUND(AVG(CAST(m.marks_obtained AS FLOAT)/m.total_marks*100),1) as avg,
                   COUNT(m.id) as total_marks
            FROM students s
            LEFT JOIN marks m ON s.roll_no=m.roll_no
            WHERE 1=1
        """
        params = []
        if search_roll: sql += " AND s.roll_no LIKE ?"; params.append(f"%{search_roll}%")
        if search_name: sql += " AND s.name LIKE ?"; params.append(f"%{search_name}%")
        if search_course: sql += " AND s.course=?"; params.append(search_course)
        sql += " GROUP BY s.roll_no ORDER BY avg DESC"
        search_results = conn.execute(sql, params).fetchall()

    # Low attendance students
    irregular_students = conn.execute("""
        SELECT s.roll_no, s.name, s.course, s.current_sem,
               COUNT(CASE WHEN a.status='Present' THEN 1 END) as present,
               COUNT(*) as total,
               ROUND(COUNT(CASE WHEN a.status='Present' THEN 1 END) * 100.0 / COUNT(*), 1) as pct
        FROM students s
        LEFT JOIN attendance a ON s.roll_no = a.roll_no AND a.semester = s.current_sem
        WHERE s.current_sem IS NOT NULL
        GROUP BY s.roll_no
        HAVING total > 0 AND pct < 75
        ORDER BY pct ASC
    """).fetchall()

    conn.close()
    return render_template("admin/performance.html",
                           toppers=toppers, all_avg=all_avg,
                           grade_dist=grade_dist, grade_fn=grade, sem_avg=sem_avg,
                           course_perf=course_perf, search_results=search_results,
                           search_roll=search_roll, search_name=search_name,
                           search_course=search_course, irregular_students=irregular_students)

# ── STUDENT PERFORMANCE DETAIL ────────────────────────────────────────────────
@app.route("/admin/performance/<roll_no>")
@login_required("admin")
def admin_performance_detail(roll_no):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,)).fetchone()
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("admin_performance"))

    # Semester-wise marks and GPA
    sem_data = []
    for sem in range(1, 7):
        marks = conn.execute("""
            SELECT subject, MAX(marks_obtained) as best_marks, total_marks
            FROM marks WHERE roll_no=? AND semester=?
            GROUP BY subject
        """, (roll_no, sem)).fetchall()

        if marks:
            avg = conn.execute("""
                SELECT ROUND(AVG(CAST(marks_obtained AS FLOAT)/total_marks*100),1)
                FROM marks WHERE roll_no=? AND semester=?
            """, (roll_no, sem)).fetchone()[0]

            gpa = calculate_gpa([dict(m) for m in marks])

            att = conn.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present
                FROM attendance WHERE roll_no=? AND semester=?
            """, (roll_no, sem)).fetchone()

            att_pct = round((att['present'] or 0) / att['total'] * 100, 1) if att['total'] else 0

            sem_data.append({
                'semester': sem,
                'avg': avg,
                'gpa': gpa,
                'subjects': len(marks),
                'attendance': att_pct,
                'marks': [dict(m) for m in marks]
            })

    conn.close()
    return render_template("admin/performance_detail.html", student=student, 
                          sem_data=sem_data, grade_fn=grade)

# ── MATERIALS ────────────────────────────────────────────────────────────────
@app.route("/admin/materials", methods=["GET","POST"])
@login_required("admin")
def admin_materials():
    UPLOAD_DIR = os.path.join(DIR, "static", "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            fpath = ""
            f = request.files.get("matfile")
            if f and f.filename:
                fname = f.filename.replace(" ","_")
                f.save(os.path.join(UPLOAD_DIR, fname))
                fpath = "uploads/" + fname

            is_internal = 1 if request.form.get("is_internal") else 0
            year = request.form.get("year") or None
            sem_val = request.form.get("sem","") or None

            conn.execute("""INSERT INTO materials(title,subject,course,semester,material_type,file_path,description,uploaded_by,upload_date,is_internal,year) 
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (request.form["title"], request.form["subject"], request.form["course"],
                 sem_val, request.form["mtype"], fpath,
                 request.form["desc"], session["user"], str(date.today()), is_internal, year))
            conn.commit(); flash("Material uploaded!", "success")
        elif action == "delete":
            conn.execute("DELETE FROM materials WHERE id=?", (request.form["mid"],))
            conn.commit(); flash("Deleted!", "success")

    materials = conn.execute("SELECT * FROM materials ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin/materials.html", materials=materials,
                           courses=["BCA","BSC","BCOM"], types=["Study Material","Question Paper","Assignment","Notes","Other"])

# ── COURSES & SECTIONS ────────────────────────────────────────────────────────
@app.route("/admin/courses")
@login_required("admin")
def admin_courses():
    conn = get_db()
    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    sections = conn.execute("""
        SELECT s.*, t.name as incharge_name 
        FROM sections s 
        LEFT JOIN teachers t ON s.incharge_teacher_id=t.id 
        ORDER BY s.course, s.name
    """).fetchall()
    teachers = conn.execute("SELECT id, name FROM teachers ORDER BY name").fetchall()
    conn.close()
    return render_template("admin/courses.html", courses=courses, sections=sections, teachers=teachers)

@app.route("/admin/courses/add_section", methods=["POST"])
@login_required("admin")
def admin_add_section():
    conn = get_db()
    conn.execute("""INSERT INTO sections(name,course,capacity,room_no,incharge_teacher_id) 
        VALUES(?,?,?,?,?)""",
        (request.form["name"], request.form["course"], 
         request.form.get("capacity",60), request.form.get("room_no",""),
         request.form.get("incharge") or None))
    conn.commit(); conn.close()
    flash("Section added!", "success")
    return redirect(url_for("admin_courses"))

# ── STUDENT PORTAL ────────────────────────────────────────────────────────────
@app.route("/student")
@login_required("student")
def student_dashboard():
    conn  = get_db()
    info  = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    roll  = info["roll_no"] if info else ""
    sem   = info["current_sem"] if info else 1

    # Current semester stats
    n_marks   = conn.execute("SELECT COUNT(*) FROM marks WHERE roll_no=? AND semester=?", (roll,sem)).fetchone()[0]
    total_att = conn.execute("SELECT COUNT(*) FROM attendance WHERE roll_no=? AND semester=?", (roll,sem)).fetchone()[0]
    present   = conn.execute("SELECT COUNT(*) FROM attendance WHERE roll_no=? AND semester=? AND status='Present'", (roll,sem)).fetchone()[0]
    avg_row   = conn.execute("SELECT ROUND(AVG(CAST(marks_obtained AS FLOAT)/total_marks*100),1) FROM marks WHERE roll_no=? AND semester=?", (roll,sem)).fetchone()
    avg       = avg_row[0] or 0
    att_pct   = round((present/total_att)*100) if total_att else 0

    # Semester summary for all semesters
    sem_summary = conn.execute("""
        SELECT semester, ROUND(AVG(CAST(marks_obtained AS FLOAT)/total_marks*100),1) as avg, 
               COUNT(*) as subjects
        FROM marks WHERE roll_no=? GROUP BY semester ORDER BY semester
    """, (roll,)).fetchall()

    # Upcoming subjects for current semester
    subjects = [r["name"] for r in conn.execute(
        "SELECT name FROM subjects WHERE course=? AND semester=? ORDER BY name",
        (info["course"], sem)).fetchall()] if info else []

    # Recent marks
    recent_marks = conn.execute("""
        SELECT subject, exam_type, marks_obtained, total_marks, semester
        FROM marks WHERE roll_no=? ORDER BY exam_date DESC LIMIT 5
    """, (roll,)).fetchall()

    # Attendance trend
    att_trend = conn.execute("""
        SELECT semester,
               COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present,
               ROUND(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct
        FROM attendance WHERE roll_no=? GROUP BY semester ORDER BY semester
    """, (roll,)).fetchall()

    conn.close()
    return render_template("student/dashboard.html", info=info,
                           n_marks=n_marks, att_pct=att_pct, avg=avg,
                           current_sem=sem, sem_summary=sem_summary,
                           subjects=subjects, recent_marks=recent_marks,
                           att_trend=att_trend)

@app.route("/student/marks")
@login_required("student")
def student_marks():
    conn = get_db()
    info = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    roll = info["roll_no"] if info else ""
    fsem = request.args.get("sem", str(info["current_sem"]) if info else "1")

    marks = conn.execute(
        "SELECT * FROM marks WHERE roll_no=? AND semester=? ORDER BY subject, exam_date",
        (roll, fsem)).fetchall()

    # Calculate semester GPA
    sem_marks = conn.execute("""
        SELECT subject, MAX(marks_obtained) as best_marks, total_marks
        FROM marks WHERE roll_no=? AND semester=?
        GROUP BY subject
    """, (roll, fsem)).fetchall()
    gpa = calculate_gpa([dict(m) for m in sem_marks])

    sems_with_marks = [r[0] for r in conn.execute(
        "SELECT DISTINCT semester FROM marks WHERE roll_no=? ORDER BY semester", (roll,)).fetchall()]
    conn.close()
    return render_template("student/marks.html", marks=marks, fsem=int(fsem),
                           sems=list(range(1,7)), sems_with_marks=sems_with_marks,
                           grade_fn=grade, info=info, gpa=gpa)

@app.route("/student/attendance")
@login_required("student")
def student_attendance():
    conn = get_db()
    info = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    roll = info["roll_no"] if info else ""
    fsem = request.args.get("sem", str(info["current_sem"]) if info else "1")

    rows = conn.execute("""
        SELECT subject, COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present
        FROM attendance WHERE roll_no=? AND semester=? GROUP BY subject
    """, (roll, fsem)).fetchall()

    # Monthly attendance breakdown
    monthly = conn.execute("""
        SELECT substr(date, 1, 7) as month,
               COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present
        FROM attendance WHERE roll_no=? AND semester=?
        GROUP BY month ORDER BY month
    """, (roll, fsem)).fetchall()

    conn.close()
    return render_template("student/attendance.html", rows=rows,
                           fsem=int(fsem), sems=list(range(1,7)), info=info, monthly=monthly)

@app.route("/student/progress")
@login_required("student")
def student_progress():
    conn = get_db()
    info = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    roll = info["roll_no"] if info else ""

    sem_data = conn.execute("""
        SELECT semester, ROUND(AVG(CAST(marks_obtained AS FLOAT)/total_marks*100),1) as avg,
               COUNT(DISTINCT subject) as subjects
        FROM marks WHERE roll_no=? GROUP BY semester ORDER BY semester
    """, (roll,)).fetchall()

    # Calculate GPA for each semester
    gpa_data = {}
    for sem in range(1, 7):
        sem_marks = conn.execute("""
            SELECT subject, MAX(marks_obtained) as best_marks, total_marks
            FROM marks WHERE roll_no=? AND semester=?
            GROUP BY subject
        """, (roll, sem)).fetchall()
        if sem_marks:
            gpa_data[sem] = calculate_gpa([dict(m) for m in sem_marks])

    cur_sem = info["current_sem"] if info else 1
    subj_data = conn.execute(
        """SELECT subject, 
                  MAX(marks_obtained) as marks_obtained, 
                  MAX(total_marks) as total_marks
           FROM marks WHERE roll_no=? AND semester=?
           GROUP BY subject""",
        (roll, cur_sem)).fetchall()

    # Attendance data — aligned to same semesters as sem_data
    # Build a dict first for easy lookup
    att_raw = conn.execute("""
        SELECT semester,
               COUNT(*) as total,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present
        FROM attendance WHERE roll_no=? GROUP BY semester ORDER BY semester
    """, (roll,)).fetchall()
    att_by_sem = {r["semester"]: r for r in att_raw}

    # Build att_data aligned to sem_data semesters
    att_data = [att_by_sem.get(r["semester"]) for r in sem_data]

    conn.close()
    return render_template("student/progress.html", sem_data=sem_data,
                           subj_data=subj_data, info=info, grade_fn=grade,
                           gpa_data=gpa_data, att_data=att_data)

@app.route("/student/syllabus")
@login_required("student")
def student_syllabus():
    conn = get_db()
    info = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    course = info["course"] if info else "BCA"
    syllabus = conn.execute(
        "SELECT * FROM syllabus WHERE course=? ORDER BY semester", (course,)).fetchall()
    by_sem = {}
    for row in syllabus:
        sem = row["semester"]
        if sem not in by_sem: by_sem[sem] = []
        by_sem[sem].append(row)

    subjects = conn.execute(
        "SELECT semester, name FROM subjects WHERE course=? ORDER BY semester", (course,)).fetchall()
    subj_by_sem = {}
    for row in subjects:
        sem = row["semester"]
        if sem not in subj_by_sem: subj_by_sem[sem] = []
        subj_by_sem[sem].append(row["name"])
    conn.close()
    return render_template("student/syllabus.html", by_sem=by_sem,
                           subj_by_sem=subj_by_sem, info=info, course=course)

@app.route("/student/materials")
@login_required("student")
def student_materials():
    conn = get_db()
    info = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    course = info["course"] if info else ""
    q  = request.args.get("q","")
    ft = request.args.get("type","All")
    fs = request.args.get("sem","All")
    fi = request.args.get("internal","All")

    # Fix: compare semester as integer when filtering
    sql = "SELECT * FROM materials WHERE (course='' OR course=? OR course IS NULL)"
    params = [course]
    if q: sql += " AND (title LIKE ? OR subject LIKE ?)"; params += [f"%{q}%"]*2
    if ft != "All": sql += " AND material_type=?"; params.append(ft)
    if fs != "All":
        # semester stored as INTEGER — cast filter value to int
        try:
            sql += " AND CAST(semester AS INTEGER)=?"; params.append(int(fs))
        except ValueError:
            pass
    if fi == "1": sql += " AND is_internal=1"
    elif fi == "0": sql += " AND is_internal=0"

    materials = conn.execute(sql+" ORDER BY id DESC", params).fetchall()
    conn.close()
    return render_template("student/materials.html", materials=materials,
                           q=q, ft=ft, fs=fs, fi=fi, info=info)

@app.route("/student/profile")
@login_required("student")
def student_profile():
    conn = get_db()
    info = conn.execute("SELECT * FROM students WHERE id=?", (session["related_id"],)).fetchone()
    subjects = []
    if info:
        subjects = [r["name"] for r in conn.execute(
            "SELECT name FROM subjects WHERE course=? AND semester=? ORDER BY name",
            (info["course"], info["current_sem"])).fetchall()]

    # Overall stats
    roll = info["roll_no"] if info else ""
    overall_avg = conn.execute("""
        SELECT ROUND(AVG(CAST(marks_obtained AS FLOAT)/total_marks*100),1)
        FROM marks WHERE roll_no=?
    """, (roll,)).fetchone()[0] or 0

    overall_att = conn.execute("""
        SELECT ROUND(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
        FROM attendance WHERE roll_no=?
    """, (roll,)).fetchone()[0] or 0

    total_subjects = conn.execute("SELECT COUNT(DISTINCT subject) FROM marks WHERE roll_no=?", (roll,)).fetchone()[0]

    conn.close()
    return render_template("student/profile.html", info=info, subjects=subjects,
                           overall_avg=overall_avg, overall_att=overall_att,
                           total_subjects=total_subjects)

# ── TEACHER SYLLABUS VIEW ─────────────────────────────────────────────────────
@app.route("/admin/teacher_syllabus")
@login_required("admin")
def admin_teacher_syllabus():
    conn = get_db()
    course = request.args.get("course","BCA")
    syllabus = conn.execute(
        "SELECT * FROM syllabus WHERE course=? ORDER BY semester", (course,)).fetchall()
    by_sem = {}
    for row in syllabus:
        sem = row["semester"]
        if sem not in by_sem: by_sem[sem] = []
        by_sem[sem].append(row)

    subjects = conn.execute(
        "SELECT semester, name FROM subjects WHERE course=? ORDER BY semester", (course,)).fetchall()
    subj_by_sem = {}
    for row in subjects:
        sem = row["semester"]
        if sem not in subj_by_sem: subj_by_sem[sem] = []
        subj_by_sem[sem].append(row["name"])
    conn.close()
    return render_template("admin/teacher_syllabus.html", by_sem=by_sem,
                           subj_by_sem=subj_by_sem, course=course,
                           courses=["BCA","BSC","BCOM"])

if __name__ == "__main__":
    import database
    database.create_database()
    app.run(debug=True, port=5000)
