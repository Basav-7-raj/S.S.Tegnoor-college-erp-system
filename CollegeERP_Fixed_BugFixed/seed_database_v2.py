import os, sqlite3, hashlib, random
from datetime import date, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "college.db")

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ── CONFIG ──────────────────────────────────────────────────────────────────
COURSES = ["BCA", "BSC", "BCOM"]
SECTIONS = ["A", "B", "C"]
SEMESTERS = list(range(1, 7))

# Subjects per course per semester
COURSE_SUBJECTS = {
    "BCA": {
        1: ["Computer Fundamentals", "Mathematics I", "English", "C Programming", "Environmental Studies"],
        2: ["Data Structures", "Mathematics II", "OOP with C++", "Digital Electronics", "Communication Skills"],
        3: ["Database Management", "Operating Systems", "Java Programming", "Web Technology", "Numerical Methods"],
        4: ["Computer Networks", "Software Engineering", "Python Programming", "Data Mining", "Web Design Lab"],
        5: ["Mobile Computing", "Cloud Computing", "Machine Learning", "Project Management", "Elective I"],
        6: ["Advanced Web Tech", "Cyber Security", "Big Data Analytics", "Project Work", "Elective II"],
    },
    "BSC": {
        1: ["Mathematics I", "Physics I", "Chemistry I", "English", "Environmental Studies"],
        2: ["Mathematics II", "Physics II", "Chemistry II", "Computer Applications", "Communication Skills"],
        3: ["Mathematics III", "Physics III", "Chemistry III", "Statistics I", "Practical I"],
        4: ["Mathematics IV", "Physics IV", "Chemistry IV", "Statistics II", "Practical II"],
        5: ["Advanced Mathematics", "Quantum Mechanics", "Organic Chemistry", "Elective I", "Project I"],
        6: ["Complex Analysis", "Electromagnetism", "Inorganic Chemistry", "Elective II", "Project II"],
    },
    "BCOM": {
        1: ["Financial Accounting", "Business Economics", "Business Law", "English", "Environmental Studies"],
        2: ["Advanced Accounting", "Business Statistics", "Company Law", "Communication Skills", "Computer Applications"],
        3: ["Corporate Accounting", "Income Tax", "Banking & Finance", "Cost Accounting", "Business Maths"],
        4: ["Auditing", "Business Management", "Financial Management", "Advanced Tax", "Project I"],
        5: ["Advanced Financial Accounting", "International Business", "Investment Management", "Elective I", "Project II"],
        6: ["Strategic Management", "Financial Markets", "Advanced Auditing", "Elective II", "Project Work"],
    }
}

# Student names (Karnataka style)
FIRST_NAMES_MALE = [
    "Arjun", "Rahul", "Vikram", "Basavaraj", "Pavan", "Kiran", "Ravi", "Suresh", "Ganesh", "Manoj",
    "Prakash", "Dinesh", "Rajesh", "Naveen", "Harish", "Santosh", "Mahesh", "Deepak", "Karthik", "Abhishek",
    "Vijay", "Ajay", "Sanjay", "Nitin", "Rohit", "Siddharth", "Aditya", "Harsha", "Tejas", "Shreyas",
    "Nikhil", "Akash", "Varun", "Sourabh", "Chaitanya", "Mohan", "Shiva", "Anil", "Sunil", "Ramesh",
    "Krishna", "Murthy", "Gopal", "Hanumantha", "Eshwar", "Shankar", "Madhu", "Raghav", "Bharath", "Yogesh",
    "Lokesh", "Nagesh", "Jagadish", "Veeresh", "Mallesh", "Raju", "Sharan", "Vinay", "Pradeep", "Sandeep",
    "Chandra", "Govind", "Hemanth", "Indra", "Jeevan", "Kalyan", "Laxman", "Mukesh", "Nanda", "Omprakash",
    "Praveen", "Qadir", "Ramu", "Sathish", "Tilak", "Umesh", "Venu", "Waseem", "Xavier", "Yashwanth",
    "Zahir", "Balaji", "Chandru", "Dev", "Eknath", "Firoz", "Gururaj", "Harshavardhan", "Ibrahim", "Jagannath",
    "Keshav", "Lohith", "Madhukar", "Narasimha", "Omkar", "Prithvi", "Raghunath", "Surya", "Tarun", "Upendra"
]

FIRST_NAMES_FEMALE = [
    "Priya", "Anjali", "Pooja", "Neha", "Divya", "Kavya", "Megha", "Shreya", "Sneha", "Rashmi",
    "Bhavana", "Lakshmi", "Sowmya", "Nandini", "Aparna", "Radhika", "Vani", "Swathi", "Keerthi", "Harini",
    "Aishwarya", "Deepa", "Gayathri", "Hema", "Indira", "Jyothi", "Kavitha", "Latha", "Manasa", "Navya",
    "Ooha", "Padma", "Rani", "Sahana", "Tanuja", "Usha", "Vijaya", "Winnie", "Yamini",
    "Zara", "Amrutha", "Chaitra", "Darshini", "Eshwari", "Fathima", "Gowri", "Harshitha", "Ishwarya", "Janaki",
    "Kusuma", "Lavanya", "Mahalakshmi", "Nirmala", "Parvathi", "Rohini", "Savitha", "Thara",
    "Uma", "Varsha", "Anusha", "Bindu", "Chandana", "Durga", "Eshika", "Ganga", "Hamsa", "Indumathi",
    "Jaya", "Kalpana", "Lasya", "Madhavi", "Nalini", "Ojaswini", "Pallavi", "Ranjitha", "Sushma", "Tejaswini"
]

LAST_NAMES = [
    "Patil", "Sharma", "Kumar", "Singh", "Gupta", "Reddy", "Rao", "Naik", "Desai", "Joshi",
    "Kulkarni", "Hegde", "Bhat", "Pai", "Kamath", "Mallya", "Shetty", "Gowda", "Murthy", "Iyer",
    "Nair", "Menon", "Pillai", "Rajan", "Verma", "Agarwal", "Jain", "Shah", "Mehta", "Gupta",
    "Choudhary", "Yadav", "Malik", "Khanna", "Arora", "Bajaj", "Dutta", "Ghosh", "Banerjee", "Chatterjee",
    "Mishra", "Tiwari", "Shukla", "Pandey", "Dwivedi", "Tripathi", "Saxena", "Mathur", "Bhardwaj", "Chauhan",
    "Rathore", "Solanki", "Parmar", "Thakur", "Bhatt", "Rawat", "Khatri", "Tanwar", "Sisodia", "Hada",
    "Bosch", "D'Souza", "Fernandes", "Lobo", "Pereira", "Rebello", "Saldanha", "Vaz", "Xavier", "Zacharias",
    "Angadi", "Biradar", "Chalawadi", "Dodmani", "Ekal", "Gani", "Hiremath", "Inamdar", "Jagalur", "Kori",
    "Lamani", "Madar", "Nayak", "Odeyar", "Panchal", "Qazi", "Raddi", "Sabal", "Talawar", "Uppar",
    "Vaddar", "Waddar", "Yadav", "Zol", "Amin", "Bandi", "Chakali", "Dom", "Eeranna", "Fakirappa"
]

EXAM_TYPES = ["Mid-Term", "Final", "Internal", "Practical"]

# ── GENERATE STUDENTS ────────────────────────────────────────────────────────
def generate_students(conn, total=1000):
    c = conn.cursor()
    c.execute("DELETE FROM students")
    c.execute("DELETE FROM users WHERE role='student'")

    # Random distribution ensuring minimum 70 per semester per course
    # 6 semesters * 70 = 420 minimum per course
    # We'll distribute ~1000 randomly but ensure each course-sem has 70+

    # First, calculate how many per course (random but balanced)
    base = total // 3
    remainder = total % 3

    bca_count = base + random.randint(-40, 60)
    bsc_count = base + random.randint(-40, 60)
    bcom_count = total - bca_count - bsc_count

    # Ensure minimums
    min_per_course = 6 * 70  # 6 semesters * 70 students
    bca_count = max(bca_count, min_per_course)
    bsc_count = max(bsc_count, min_per_course)
    bcom_count = max(bcom_count, min_per_course)

    # Adjust to total
    total_calculated = bca_count + bsc_count + bcom_count
    if total_calculated > total:
        # Scale down proportionally
        factor = total / total_calculated
        bca_count = int(bca_count * factor)
        bsc_count = int(bsc_count * factor)
        bcom_count = total - bca_count - bsc_count

    distribution = {"BCA": bca_count, "BSC": bsc_count, "BCOM": bcom_count}

    print(f"   Distribution: BCA={bca_count}, BSC={bsc_count}, BCOM={bcom_count} (Total: {sum(distribution.values())})")

    student_id = 1
    for course, num in distribution.items():
        print(f"\n   Creating {num} {course} students...")

        # Distribute across semesters ensuring 70+ per sem
        sem_counts = {}
        remaining = num
        for sem in range(6, 0, -1):  # Start from sem 6
            if sem == 1:
                sem_counts[sem] = remaining
            else:
                # Random between 70 and remaining/(sem) * 1.5
                max_for_sem = min(remaining - (sem-1)*70, int(remaining/sem * 1.3))
                min_for_sem = 70
                sem_counts[sem] = random.randint(min_for_sem, max( min_for_sem, max_for_sem))
                remaining -= sem_counts[sem]

        print(f"   Semester distribution: {dict(sorted(sem_counts.items()))}")

        for sem, count in sem_counts.items():
            for i in range(count):
                roll_no = f"{course}{sem}{str(i+1).zfill(3)}"

                # Name
                if random.random() < 0.52:
                    fname = random.choice(FIRST_NAMES_MALE)
                else:
                    fname = random.choice(FIRST_NAMES_FEMALE)
                lname = random.choice(LAST_NAMES)
                name = f"{fname} {lname}"

                # Email
                email = f"{fname.lower()}.{lname.lower()}{random.randint(1,99)}@sstegnoor.edu.in"

                # Phone
                phone = f"{random.choice(['9','8','7'])}{random.randint(100000000,999999999)}"

                # Section
                section = random.choice(SECTIONS)

                # DOB (18-24 years old)
                year = random.randint(2000, 2006)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                dob = f"{year}-{month:02d}-{day:02d}"

                # Address
                addresses = [
                    "Tegnoor, Bagalkot District, Karnataka",
                    "Hungund, Bagalkot, Karnataka",
                    "Badami, Bagalkot, Karnataka",
                    "Bilagi, Bagalkot, Karnataka",
                    "Mudhol, Bagalkot, Karnataka",
                    "Jamkhandi, Bagalkot, Karnataka",
                    "Guledgudda, Bagalkot, Karnataka",
                    "Rabakavi Banahatti, Karnataka",
                    "Ilkal, Bagalkot, Karnataka",
                    "Kerur, Bagalkot, Karnataka",
                    "Bagalkot City, Karnataka",
                    "Gajendragad, Karnataka",
                    "Ron, Gadag District, Karnataka",
                    "Nargund, Gadag, Karnataka",
                    "Lakshmeshwar, Gadag, Karnataka"
                ]
                address = random.choice(addresses)

                c.execute("""
                    INSERT INTO students (roll_no, name, email, phone, course, current_sem, section, dob, address, enrolled_date)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (roll_no, name, email, phone, course, sem, section, dob, address, str(date.today())))

                # Create login
                uname = roll_no.lower()
                c.execute("INSERT INTO users (username, password, role, related_id) VALUES (?,?,?,?)",
                          (uname, hp("student123"), "student", student_id))

                student_id += 1

    conn.commit()
    print(f"\n✅ Created {student_id-1} students with logins")
    return distribution

# ── GENERATE TEACHERS ───────────────────────────────────────────────────────
def generate_teachers(conn, ratio=30):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students")
    student_count = c.fetchone()[0]
    teacher_count = max(1, student_count // ratio)

    c.execute("DELETE FROM teachers")
    c.execute("DELETE FROM users WHERE role='admin' AND username!='admin'")

    departments = {
        "BCA": ["Computer Science", "Mathematics", "English"],
        "BSC": ["Mathematics", "Physics", "Chemistry", "Statistics"],
        "BCOM": ["Commerce", "Economics", "Management", "Law"]
    }

    # Teacher name pools
    teacher_first_male = ["Dr. Rajesh", "Prof. Vikram", "Dr. Basavaraj", "Prof. Pavan", "Dr. Kiran",
                          "Prof. Ravi", "Dr. Suresh", "Prof. Ganesh", "Dr. Manoj", "Prof. Prakash",
                          "Dr. Dinesh", "Prof. Rajesh", "Dr. Naveen", "Prof. Harish", "Dr. Santosh",
                          "Prof. Mahesh", "Dr. Deepak", "Prof. Karthik", "Dr. Abhishek", "Prof. Vijay"]

    teacher_first_female = ["Prof. Sunita", "Dr. Anjali", "Prof. Lakshmi", "Dr. Kavita", "Prof. Deepa",
                            "Dr. Megha", "Prof. Bhavana", "Dr. Priya", "Prof. Divya", "Dr. Sneha",
                            "Prof. Kavya", "Dr. Neha", "Prof. Shreya", "Dr. Rashmi", "Prof. Aparna",
                            "Dr. Radhika", "Prof. Vani", "Dr. Swathi", "Prof. Keerthi", "Dr. Harini"]

    teacher_last = ["Patil", "Sharma", "Kumar", "Gupta", "Reddy", "Rao", "Naik", "Desai", "Joshi",
                    "Kulkarni", "Hegde", "Bhat", "Kamath", "Shetty", "Gowda", "Murthy", "Iyer",
                    "Nair", "Menon", "Verma"]

    for i in range(teacher_count):
        if random.random() < 0.4:
            fname = random.choice(teacher_first_male)
        else:
            fname = random.choice(teacher_first_female)
        lname = random.choice(teacher_last)
        name = f"{fname} {lname}"

        course = random.choice(COURSES)
        dept = random.choice(departments[course])

        email = f"teacher{i+1:03d}@sstegnoor.edu.in"
        phone = f"{random.choice(['9','8','7'])}{random.randint(100000000,999999999)}"

        # Get subjects for this course
        all_subjects = []
        for sem_subjects in COURSE_SUBJECTS[course].values():
            all_subjects.extend(sem_subjects)
        subject = random.choice(all_subjects)

        c.execute("""
            INSERT INTO teachers (name, email, phone, department, subject)
            VALUES (?,?,?,?,?)
        """, (name, email, phone, dept, subject))

        tid = c.lastrowid
        uname = f"teacher{i+1:03d}"
        c.execute("INSERT INTO users (username, password, role, related_id) VALUES (?,?,?,?)",
                  (uname, hp("teacher123"), "admin", tid))

        if (i+1) % 5 == 0:
            print(f"   Created {i+1}/{teacher_count} teachers...")

    conn.commit()
    print(f"\n✅ Created {teacher_count} teachers (1:{ratio} ratio)")

# ── GENERATE MARKS ──────────────────────────────────────────────────────────
def generate_marks(conn):
    c = conn.cursor()
    c.execute("DELETE FROM marks")

    students = c.execute("SELECT id, roll_no, course, current_sem FROM students").fetchall()
    total_marks = 0

    print(f"\n   Generating marks for {len(students)} students...")
    print("   Each student gets marks for ALL semesters from 1 to current_sem")

    for student in students:
        sid, roll_no, course, current_sem = student

        # Generate marks for EACH semester from 1 to current_sem (COMPLETE HISTORY)
        for sem in range(1, current_sem + 1):
            subjects = COURSE_SUBJECTS.get(course, {}).get(sem, [])

            for subject in subjects:
                # Multiple exams per subject (2-4 exams)
                num_exams = random.randint(2, 4)

                for _ in range(num_exams):
                    exam_type = random.choice(EXAM_TYPES)
                    total = random.choice([50, 100])

                    # Realistic marks distribution
                    performance = random.choices(
                        ["excellent", "good", "average", "poor"],
                        weights=[15, 40, 35, 10]
                    )[0]

                    if performance == "excellent":
                        marks = random.randint(int(total*0.85), total)
                    elif performance == "good":
                        marks = random.randint(int(total*0.70), int(total*0.85))
                    elif performance == "average":
                        marks = random.randint(int(total*0.50), int(total*0.70))
                    else:
                        marks = random.randint(int(total*0.30), int(total*0.50))

                    # Exam date in the past (older semesters = older dates)
                    days_back = (current_sem - sem) * 180 + random.randint(1, 90)
                    exam_date = str(date.today() - timedelta(days=days_back))

                    c.execute("""
                        INSERT INTO marks (roll_no, subject, exam_type, marks_obtained, total_marks, semester, exam_date)
                        VALUES (?,?,?,?,?,?,?)
                    """, (roll_no, subject, exam_type, marks, total, sem, exam_date))
                    total_marks += 1

        if sid % 200 == 0:
            print(f"   Progress: {sid}/{len(students)} students done...")

    conn.commit()
    print(f"\n✅ Created {total_marks} mark records")
    print(f"   Average marks per student: {total_marks // len(students)}")

# ── GENERATE ATTENDANCE ─────────────────────────────────────────────────────
def generate_attendance(conn):
    c = conn.cursor()
    c.execute("DELETE FROM attendance")

    students = c.execute("SELECT id, roll_no, course, current_sem FROM students").fetchall()
    total_att = 0

    print(f"\n   Generating attendance for {len(students)} students...")
    print("   Each student gets attendance for ALL semesters from 1 to current_sem")

    for student in students:
        sid, roll_no, course, current_sem = student

        # Generate attendance for EACH semester from 1 to current_sem (COMPLETE HISTORY)
        for sem in range(1, current_sem + 1):
            subjects = COURSE_SUBJECTS.get(course, {}).get(sem, [])

            for subject in subjects:
                # 30-50 classes per subject per semester
                num_classes = random.randint(35, 50)

                # Attendance rate (some students are regular, some not)
                attendance_rate = random.choices(
                    [0.95, 0.88, 0.78, 0.65],
                    weights=[25, 40, 25, 10]
                )[0]

                for class_num in range(num_classes):
                    # Older semesters = older dates
                    days_back = (current_sem - sem) * 180 + random.randint(1, 170)
                    att_date = str(date.today() - timedelta(days=days_back))
                    status = "Present" if random.random() < attendance_rate else "Absent"

                    c.execute("""
                        INSERT INTO attendance (roll_no, subject, semester, date, status)
                        VALUES (?,?,?,?,?)
                    """, (roll_no, subject, sem, att_date, status))
                    total_att += 1

        if sid % 200 == 0:
            print(f"   Progress: {sid}/{len(students)} students done...")

    conn.commit()
    print(f"\n✅ Created {total_att} attendance records")
    print(f"   Average attendance records per student: {total_att // len(students)}")

# ── GENERATE MATERIALS ──────────────────────────────────────────────────────
def generate_materials(conn):
    c = conn.cursor()
    c.execute("DELETE FROM materials")

    sample_materials = [
        ("Computer Fundamentals Complete Notes", "Computer Fundamentals", "BCA", 1, "Notes", "Complete unit notes with diagrams"),
        ("Data Structures Important Questions 2024", "Data Structures", "BCA", 2, "Question Paper", "Previous 5 years questions with solutions"),
        ("DBMS Normalization Assignment", "Database Management", "BCA", 3, "Assignment", "Practice problems on 1NF, 2NF, 3NF"),
        ("Java Programming Lab Manual", "Java Programming", "BCA", 3, "Study Material", "All practical exercises with code"),
        ("Python Quick Reference Guide", "Python Programming", "BCA", 4, "Notes", "Cheat sheet for exam preparation"),
        ("Machine Learning Project Template", "Machine Learning", "BCA", 5, "Study Material", "Project report format and guidelines"),
        ("Cloud Computing Case Studies", "Cloud Computing", "BCA", 5, "Assignment", "AWS and Azure deployment examples"),
        ("Cyber Security Notes", "Cyber Security", "BCA", 6, "Notes", "Network security protocols explained"),
        ("Physics I Formula Sheet", "Physics I", "BSC", 1, "Notes", "All important formulas for exams"),
        ("Chemistry Practical Manual 2024", "Chemistry I", "BSC", 1, "Study Material", "Lab instructions and safety guidelines"),
        ("Statistics Problem Set 3", "Statistics I", "BSC", 3, "Assignment", "Probability and distributions practice"),
        ("Quantum Mechanics Lecture Notes", "Quantum Mechanics", "BSC", 5, "Notes", "Detailed notes with derivations"),
        ("Financial Accounting Journal Entries", "Financial Accounting", "BCOM", 1, "Notes", "Step-by-step journal entry guide"),
        ("Income Tax Calculation Examples", "Income Tax", "BCOM", 3, "Study Material", "Solved problems for FY 2023-24"),
        ("Business Law Important Cases", "Business Law", "BCOM", 1, "Assignment", "Landmark judgments summary"),
        ("Investment Management Portfolio", "Investment Management", "BCOM", 5, "Study Material", "Portfolio analysis techniques"),
        ("Strategic Management Case Study", "Strategic Management", "BCOM", 6, "Assignment", "Tata Group strategy analysis"),
        ("English Grammar Workbook", "English", "BCA", 1, "Notes", "Grammar rules and exercises"),
        ("Mathematics I Previous Papers", "Mathematics I", "BCA", 1, "Question Paper", "Last 3 years exam papers"),
    ]

    for title, subject, course, sem, mtype, desc in sample_materials:
        c.execute("""
            INSERT INTO materials (title, subject, course, semester, material_type, file_path, description, uploaded_by, upload_date)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (title, subject, course, sem, mtype, "", desc, "admin", str(date.today())))

    conn.commit()
    print(f"\n✅ Created {len(sample_materials)} sample materials")

# ── GENERATE SYLLABUS ───────────────────────────────────────────────────────
def generate_syllabus(conn):
    c = conn.cursor()
    c.execute("DELETE FROM syllabus")

    for course in COURSES:
        for sem in range(1, 7):
            title = f"{course} Semester {sem} Syllabus 2024-25"
            c.execute("""
                INSERT INTO syllabus (course, semester, title, file_path, uploaded_by, upload_date)
                VALUES (?,?,?,?,?,?)
            """, (course, sem, title, "", "admin", str(date.today())))

    conn.commit()
    print(f"\n✅ Created {len(COURSES)*6} syllabus entries")

# ── VERIFY DATA ─────────────────────────────────────────────────────────────
def verify_data(conn):
    c = conn.cursor()

    print("\n" + "="*60)
    print("  DATA VERIFICATION REPORT")
    print("="*60)

    # Students per course
    print("\n📊 Students per Course:")
    for course in COURSES:
        count = c.execute("SELECT COUNT(*) FROM students WHERE course=?", (course,)).fetchone()[0]
        print(f"   {course}: {count} students")

    # Students per semester per course
    print("\n📊 Students per Semester (per Course):")
    for course in COURSES:
        print(f"   {course}:")
        for sem in range(1, 7):
            count = c.execute("SELECT COUNT(*) FROM students WHERE course=? AND current_sem=?", (course, sem)).fetchone()[0]
            status = "✅" if count >= 70 else "⚠️"
            print(f"      Sem {sem}: {count} students {status}")

    # Teachers
    teacher_count = c.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
    print(f"\n👨‍🏫 Total Teachers: {teacher_count}")

    # Marks
    marks_count = c.execute("SELECT COUNT(*) FROM marks").fetchone()[0]
    print(f"📝 Total Marks Records: {marks_count}")

    # Attendance
    att_count = c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    print(f"📋 Total Attendance Records: {att_count}")

    # Sample student check
    sample = c.execute("SELECT roll_no, name, course, current_sem FROM students WHERE current_sem >= 3 LIMIT 1").fetchone()
    if sample:
        roll, name, course, sem = sample
        print(f"\n🔍 Sample Student: {name} ({roll}) - {course} Sem {sem}")

        # Check their marks history
        marks_semesters = c.execute("SELECT DISTINCT semester FROM marks WHERE roll_no=? ORDER BY semester", (roll,)).fetchall()
        print(f"   Marks available for semesters: {[m[0] for m in marks_semesters]}")

        # Check their attendance history
        att_semesters = c.execute("SELECT DISTINCT semester FROM attendance WHERE roll_no=? ORDER BY semester", (roll,)).fetchall()
        print(f"   Attendance available for semesters: {[a[0] for a in att_semesters]}")

    print("\n" + "="*60)

# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  S S TEGNOOR DEGREE COLLEGE - DATABASE SEEDER v2.0")
    print("  Complete Historical Data Generation")
    print("="*60 + "\n")

    # Ensure database exists
    import database
    database.create_database()

    conn = get_db()

    print("\n🎓 STEP 1: Generating Students (Random Distribution)...")
    distribution = generate_students(conn, 1000)

    print("\n👨‍🏫 STEP 2: Generating Teachers (1:30 ratio)...")
    generate_teachers(conn, 30)

    print("\n📝 STEP 3: Generating COMPLETE Marks History...")
    print("   (All semesters from 1 to current_sem for each student)")
    generate_marks(conn)

    print("\n📋 STEP 4: Generating COMPLETE Attendance History...")
    print("   (All semesters from 1 to current_sem for each student)")
    generate_attendance(conn)

    print("\n📚 STEP 5: Generating Materials...")
    generate_materials(conn)

    print("\n📖 STEP 6: Generating Syllabus...")
    generate_syllabus(conn)

    print("\n🔍 STEP 7: Verifying Data...")
    verify_data(conn)

    conn.close()

    print("\n" + "="*60)
    print("  ✅ DATABASE SEEDING COMPLETE!")
    print("="*60)
    print("\n📊 Summary:")
    print("   • ~1000 Students with COMPLETE historical data")
    print("   • ~34 Teachers with login accounts")
    print("   • Marks for ALL semesters (1 to current_sem)")
    print("   • Attendance for ALL semesters (1 to current_sem)")
    print("   • Sample study materials")
    print("   • Syllabus entries for all courses")
    print("\n🔑 Default Logins:")
    print("   • Admin: admin / admin123")
    print("   • Student: bca11001 / student123 (sem 1)")
    print("   • Student: bca55001 / student123 (sem 5)")
    print("   • Teacher: teacher001 / teacher123")
    print("\n🚀 Run: python app.py")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
