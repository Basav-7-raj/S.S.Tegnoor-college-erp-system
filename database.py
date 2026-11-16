import os, sqlite3, hashlib, random
from datetime import date, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "college.db")

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

# Fixed subjects per course per semester
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
    "Bosch", "D\'Souza", "Fernandes", "Lobo", "Pereira", "Rebello", "Saldanha", "Vaz", "Xavier", "Zacharias",
    "Angadi", "Biradar", "Chalawadi", "Dodmani", "Ekal", "Gani", "Hiremath", "Inamdar", "Jagalur", "Kori",
    "Lamani", "Madar", "Nayak", "Odeyar", "Panchal", "Qazi", "Raddi", "Sabal", "Talawar", "Uppar",
    "Vaddar", "Waddar", "Yadav", "Zol", "Amin", "Bandi", "Chakali", "Dom", "Eeranna", "Fakirappa"
]

EXAM_TYPES = ["Mid-Term", "Final", "Internal", "Practical"]

COURSES = ["BCA", "BSC", "BCOM"]
SECTIONS = ["A", "B", "C", "D"]

def create_database():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS teachers;
        DROP TABLE IF EXISTS attendance;
        DROP TABLE IF EXISTS marks;
        DROP TABLE IF EXISTS syllabus;
        DROP TABLE IF EXISTS materials;
        DROP TABLE IF EXISTS sections;

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            related_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            full_name TEXT,
            total_sems INTEGER DEFAULT 6,
            description TEXT,
            sections TEXT
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            credits INTEGER DEFAULT 4
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            course TEXT,
            current_sem INTEGER DEFAULT 1,
            section TEXT,
            dob TEXT,
            address TEXT,
            enrolled_date TEXT
        );
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department TEXT,
            subject TEXT,
            designation TEXT DEFAULT 'Assistant Professor',
            joining_date TEXT
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            subject TEXT NOT NULL,
            semester INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_by TEXT
        );
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            subject TEXT NOT NULL,
            exam_type TEXT NOT NULL,
            marks_obtained INTEGER,
            total_marks INTEGER,
            semester INTEGER,
            exam_date TEXT,
            entered_by TEXT
        );
        CREATE TABLE IF NOT EXISTS syllabus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT,
            uploaded_by TEXT,
            upload_date TEXT,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            course TEXT,
            semester INTEGER,
            material_type TEXT,
            file_path TEXT,
            description TEXT,
            uploaded_by TEXT,
            upload_date TEXT,
            is_internal INTEGER DEFAULT 0,
            year INTEGER
        );
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            capacity INTEGER DEFAULT 60,
            room_no TEXT,
            incharge_teacher_id INTEGER
        );
    """)

    # Default admin
    c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
              ("admin", hp("admin123"), "admin"))

    # Courses with sections
    courses_data = [
        ("BCA", "Bachelor of Computer Applications", 6, "3-year undergraduate program in computer applications", "A,B,C,D"),
        ("BSC", "Bachelor of Science", 6, "3-year undergraduate program in science", "A,B,C,D"),
        ("BCOM", "Bachelor of Commerce", 6, "3-year undergraduate program in commerce", "A,B,C,D")
    ]
    for name, full, sems, desc, secs in courses_data:
        c.execute("INSERT INTO courses (name,full_name,total_sems,description,sections) VALUES (?,?,?,?,?)", 
                  (name, full, sems, desc, secs))

    # Subjects
    for course, sems in COURSE_SUBJECTS.items():
        for sem, subjects in sems.items():
            for idx, subj in enumerate(subjects):
                code = f"{course}{sem}{chr(65+idx)}"
                c.execute("INSERT INTO subjects (course,semester,name,code,credits) VALUES (?,?,?,?,?)",
                          (course, sem, subj, code, 4))

    # ── GENERATE 1200 STUDENTS ─────────────────────────────────────────────
    random.seed(42)
    total_students = 1200  # More than 1000

    # Distribute across courses: BCA=450, BSC=350, BCOM=400
    course_counts = {"BCA": 450, "BSC": 350, "BCOM": 400}

    student_id = 1
    for course, count in course_counts.items():
        # Distribute across semesters ensuring each sem has ~70-80 students
        base_per_sem = count // 6
        remainder = count % 6

        sem_counts = {}
        for sem in range(1, 7):
            sem_counts[sem] = base_per_sem + (1 if sem <= remainder else 0)

        for sem, sem_count in sem_counts.items():
            for i in range(sem_count):
                roll_no = f"{course}{sem}{str(i+1).zfill(3)}"

                # Name
                if random.random() < 0.52:
                    fname = random.choice(FIRST_NAMES_MALE)
                else:
                    fname = random.choice(FIRST_NAMES_FEMALE)
                lname = random.choice(LAST_NAMES)
                name = f"{fname} {lname}"

                email = f"{fname.lower()}.{lname.lower()}{random.randint(1,99)}@sstegnoor.edu.in"
                phone = f"{random.choice(['9','8','7'])}{random.randint(100000000,999999999)}"
                section = random.choice(SECTIONS)

                # DOB (18-24 years old)
                year = random.randint(2000, 2006)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                dob = f"{year}-{month:02d}-{day:02d}"

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

                # Create login - use roll_no as username (lowercase)
                uname = roll_no.lower()
                c.execute("INSERT INTO users (username, password, role, related_id) VALUES (?,?,?,?)",
                          (uname, hp("student123"), "student", student_id))

                student_id += 1

    # ── GENERATE 60 TEACHERS ─────────────────────────────────────────────────
    teacher_first_male = ["Dr. Rajesh", "Prof. Vikram", "Dr. Basavaraj", "Prof. Pavan", "Dr. Kiran",
                          "Prof. Ravi", "Dr. Suresh", "Prof. Ganesh", "Dr. Manoj", "Prof. Prakash",
                          "Dr. Dinesh", "Prof. Rajesh", "Dr. Naveen", "Prof. Harish", "Dr. Santosh",
                          "Prof. Mahesh", "Dr. Deepak", "Prof. Karthik", "Dr. Abhishek", "Prof. Vijay",
                          "Dr. Ajay", "Prof. Sanjay", "Dr. Nitin", "Prof. Rohit", "Dr. Siddharth",
                          "Prof. Aditya", "Dr. Harsha", "Prof. Tejas", "Dr. Shreyas", "Prof. Nikhil"]

    teacher_first_female = ["Prof. Sunita", "Dr. Anjali", "Prof. Lakshmi", "Dr. Kavita", "Prof. Deepa",
                            "Dr. Megha", "Prof. Bhavana", "Dr. Priya", "Prof. Divya", "Dr. Sneha",
                            "Prof. Kavya", "Dr. Neha", "Prof. Shreya", "Dr. Rashmi", "Prof. Aparna",
                            "Dr. Radhika", "Prof. Vani", "Dr. Swathi", "Prof. Keerthi", "Dr. Harini",
                            "Prof. Aishwarya", "Dr. Deepa", "Prof. Gayathri", "Dr. Hema", "Prof. Indira",
                            "Dr. Jyothi", "Prof. Kavitha", "Dr. Latha", "Prof. Manasa", "Dr. Navya"]

    teacher_last = ["Patil", "Sharma", "Kumar", "Gupta", "Reddy", "Rao", "Naik", "Desai", "Joshi",
                    "Kulkarni", "Hegde", "Bhat", "Kamath", "Shetty", "Gowda", "Murthy", "Iyer",
                    "Nair", "Menon", "Verma"]

    departments = {
        "BCA": ["Computer Science", "Mathematics", "English"],
        "BSC": ["Mathematics", "Physics", "Chemistry", "Statistics"],
        "BCOM": ["Commerce", "Economics", "Management", "Law"]
    }

    designations = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"]

    for i in range(60):
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
        designation = random.choice(designations)

        c.execute("""
            INSERT INTO teachers (name, email, phone, department, subject, designation, joining_date)
            VALUES (?,?,?,?,?,?,?)
        """, (name, email, phone, dept, subject, designation, str(date.today())))

        tid = c.lastrowid
        uname = f"teacher{tid:03d}"
        c.execute("INSERT INTO users (username, password, role, related_id) VALUES (?,?,?,?)",
                  (uname, hp("teacher123"), "admin", tid))

    # ── GENERATE MARKS FOR ALL STUDENTS ─────────────────────────────────────
    students = c.execute("SELECT id, roll_no, course, current_sem FROM students").fetchall()
    total_marks = 0

    for student in students:
        sid, roll_no, course, current_sem = student

        # Generate marks for EACH semester from 1 to current_sem
        for sem in range(1, current_sem + 1):
            subjects = COURSE_SUBJECTS.get(course, {}).get(sem, [])

            for subject in subjects:
                # 2-4 exams per subject
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

                    days_back = (current_sem - sem) * 180 + random.randint(1, 90)
                    exam_date = str(date.today() - timedelta(days=days_back))

                    c.execute("""
                        INSERT INTO marks (roll_no, subject, exam_type, marks_obtained, total_marks, semester, exam_date, entered_by)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (roll_no, subject, exam_type, marks, total, sem, exam_date, "admin"))
                    total_marks += 1

    # ── GENERATE ATTENDANCE FOR ALL STUDENTS ────────────────────────────────
    total_att = 0

    for student in students:
        sid, roll_no, course, current_sem = student

        for sem in range(1, current_sem + 1):
            subjects = COURSE_SUBJECTS.get(course, {}).get(sem, [])

            for subject in subjects:
                # 35-50 classes per subject per semester
                num_classes = random.randint(35, 50)

                attendance_rate = random.choices(
                    [0.95, 0.88, 0.78, 0.65],
                    weights=[25, 40, 25, 10]
                )[0]

                for class_num in range(num_classes):
                    days_back = (current_sem - sem) * 180 + random.randint(1, 170)
                    att_date = str(date.today() - timedelta(days=days_back))
                    status = "Present" if random.random() < attendance_rate else "Absent"

                    c.execute("""
                        INSERT INTO attendance (roll_no, subject, semester, date, status, marked_by)
                        VALUES (?,?,?,?,?,?)
                    """, (roll_no, subject, sem, att_date, status, "admin"))
                    total_att += 1

    # ── GENERATE MATERIALS ─────────────────────────────────────────────────
    materials_data = [
        ("Computer Fundamentals Complete Notes", "Computer Fundamentals", "BCA", 1, "Notes", "Complete unit notes with diagrams", "admin"),
        ("Data Structures Important Questions 2024", "Data Structures", "BCA", 2, "Question Paper", "Previous 5 years questions with solutions", "admin"),
        ("DBMS Normalization Assignment", "Database Management", "BCA", 3, "Assignment", "Practice problems on 1NF, 2NF, 3NF", "admin"),
        ("Java Programming Lab Manual", "Java Programming", "BCA", 3, "Study Material", "All practical exercises with code", "admin"),
        ("Python Quick Reference Guide", "Python Programming", "BCA", 4, "Notes", "Cheat sheet for exam preparation", "admin"),
        ("Machine Learning Project Template", "Machine Learning", "BCA", 5, "Study Material", "Project report format and guidelines", "admin"),
        ("Cloud Computing Case Studies", "Cloud Computing", "BCA", 5, "Assignment", "AWS and Azure deployment examples", "admin"),
        ("Cyber Security Notes", "Cyber Security", "BCA", 6, "Notes", "Network security protocols explained", "admin"),
        ("Physics I Formula Sheet", "Physics I", "BSC", 1, "Notes", "All important formulas for exams", "admin"),
        ("Chemistry Practical Manual 2024", "Chemistry I", "BSC", 1, "Study Material", "Lab instructions and safety guidelines", "admin"),
        ("Statistics Problem Set 3", "Statistics I", "BSC", 3, "Assignment", "Probability and distributions practice", "admin"),
        ("Quantum Mechanics Lecture Notes", "Quantum Mechanics", "BSC", 5, "Notes", "Detailed notes with derivations", "admin"),
        ("Financial Accounting Journal Entries", "Financial Accounting", "BCOM", 1, "Notes", "Step-by-step journal entry guide", "admin"),
        ("Income Tax Calculation Examples", "Income Tax", "BCOM", 3, "Study Material", "Solved problems for FY 2023-24", "admin"),
        ("Business Law Important Cases", "Business Law", "BCOM", 1, "Assignment", "Landmark judgments summary", "admin"),
        ("Investment Management Portfolio", "Investment Management", "BCOM", 5, "Study Material", "Portfolio analysis techniques", "admin"),
        ("Strategic Management Case Study", "Strategic Management", "BCOM", 6, "Assignment", "Tata Group strategy analysis", "admin"),
        ("English Grammar Workbook", "English", "BCA", 1, "Notes", "Grammar rules and exercises", "admin"),
        ("Mathematics I Previous Papers", "Mathematics I", "BCA", 1, "Question Paper", "Last 3 years exam papers", "admin"),
        ("Internal Exam 1 - Computer Fundamentals", "Computer Fundamentals", "BCA", 1, "Question Paper", "Internal assessment 1 question paper", "admin"),
        ("Internal Exam 2 - Data Structures", "Data Structures", "BCA", 2, "Question Paper", "Internal assessment 2 question paper", "admin"),
    ]

    for title, subject, course, sem, mtype, desc, uploaded in materials_data:
        is_internal = 1 if "Internal Exam" in title else 0
        c.execute("""
            INSERT INTO materials (title, subject, course, semester, material_type, file_path, description, uploaded_by, upload_date, is_internal, year)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (title, subject, course, sem, mtype, "", desc, uploaded, str(date.today()), is_internal, 2024))

    # ── GENERATE SYLLABUS ──────────────────────────────────────────────────
    for course in COURSES:
        for sem in range(1, 7):
            title = f"{course} Semester {sem} Syllabus 2024-25"
            c.execute("""
                INSERT INTO syllabus (course, semester, title, file_path, uploaded_by, upload_date, description)
                VALUES (?,?,?,?,?,?,?)
            """, (course, sem, title, "", "admin", str(date.today()), f"Complete syllabus for {course} Semester {sem}"))

    # ── GENERATE SECTIONS ──────────────────────────────────────────────────
    for course in COURSES:
        for section_name in ["A", "B", "C", "D"]:
            room_no = f"{random.randint(100, 200)}"
            c.execute("""
                INSERT INTO sections (name, course, capacity, room_no, incharge_teacher_id)
                VALUES (?,?,?,?,?)
            """, (section_name, course, 60, room_no, random.randint(1, 60)))

    conn.commit()

    # ── VERIFY DATA ────────────────────────────────────────────────────────
    print("=" * 60)
    print("  DATA VERIFICATION REPORT")
    print("=" * 60)

    student_count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    teacher_count = c.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
    marks_count = c.execute("SELECT COUNT(*) FROM marks").fetchone()[0]
    att_count = c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    materials_count = c.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
    syllabus_count = c.execute("SELECT COUNT(*) FROM syllabus").fetchone()[0]

    print(f"\n📊 Total Students: {student_count}")
    print(f"👨‍🏫 Total Teachers: {teacher_count}")
    print(f"📝 Total Marks Records: {marks_count}")
    print(f"📋 Total Attendance Records: {att_count}")
    print(f"📚 Total Materials: {materials_count}")
    print(f"📖 Total Syllabus: {syllabus_count}")

    print(f"\n📊 Students per Course:")
    for course in COURSES:
        count = c.execute("SELECT COUNT(*) FROM students WHERE course=?", (course,)).fetchone()[0]
        print(f"   {course}: {count} students")

    print(f"\n📊 Students per Semester (per Course):")
    for course in COURSES:
        print(f"   {course}:")
        for sem in range(1, 7):
            count = c.execute("SELECT COUNT(*) FROM students WHERE course=? AND current_sem=?", (course, sem)).fetchone()[0]
            print(f"      Sem {sem}: {count} students")

    print(f"\n📊 Marks per student (average): {marks_count // student_count}")
    print(f"📊 Attendance per student (average): {att_count // student_count}")

    print("\n" + "=" * 60)
    print("  ✅ DATABASE CREATION COMPLETE!")
    print("=" * 60)
    print("\n🔑 Default Logins:")
    print("   • Admin: admin / admin123")
    print("   • Student: bca1101 / student123 (or any roll_no lowercase)")
    print("   • Teacher: teacher001 / teacher123")

    conn.close()

if __name__ == "__main__":
    create_database()