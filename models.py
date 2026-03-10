from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20),  nullable=False)

    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    faculty_profile = db.relationship('FacultyProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    chat_messages   = db.relationship('ChatMessage',    backref='user', cascade='all, delete-orphan')

    def set_password(self, p):   self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    year       = db.Column(db.Integer, nullable=False, default=1)
    semester   = db.Column(db.Integer, nullable=False, default=1)
    branch     = db.Column(db.String(80), nullable=False)
    cgpa       = db.Column(db.Float, nullable=False, default=0.0)
    enrollments = db.relationship('Enrollment', backref='student', cascade='all, delete-orphan')


class FacultyProfile(db.Model):
    __tablename__ = 'faculty_profiles'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    faculty_id  = db.Column(db.String(20), unique=True, nullable=False)
    department  = db.Column(db.String(80), nullable=False)
    designation = db.Column(db.String(80), nullable=False, default='Assistant Professor')
    courses     = db.relationship('Course', backref='faculty', cascade='all, delete-orphan')


class Course(db.Model):
    __tablename__ = 'courses'
    id         = db.Column(db.Integer, primary_key=True)
    code       = db.Column(db.String(20), unique=True, nullable=False)
    name       = db.Column(db.String(120), nullable=False)
    credits    = db.Column(db.Integer, nullable=False, default=3)
    semester   = db.Column(db.Integer, nullable=False, default=1)
    branch     = db.Column(db.String(80), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty_profiles.id'), nullable=True)
    enrollments = db.relationship('Enrollment', backref='course', cascade='all, delete-orphan')


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    course_id      = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    grade          = db.Column(db.Float, nullable=True)
    attendance_pct = db.Column(db.Float, nullable=False, default=0.0)
    internals      = db.Column(db.Float, nullable=True)
    externals      = db.Column(db.Float, nullable=True)
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id'),)

    @property
    def grade_letter(self):
        if self.grade is None: return 'N/A'
        if self.grade >= 9.0: return 'O'
        if self.grade >= 8.0: return 'A+'
        if self.grade >= 7.0: return 'A'
        if self.grade >= 6.0: return 'B+'
        if self.grade >= 5.5: return 'B'
        if self.grade >= 5.0: return 'C'
        return 'F'

    @property
    def attendance_status(self):
        if self.attendance_pct >= 75: return 'safe'
        if self.attendance_pct >= 65: return 'warning'
        return 'danger'


class Notice(db.Model):
    __tablename__ = 'notices'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pinned     = db.Column(db.Boolean, default=False)
    author     = db.relationship('User')


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role       = db.Column(db.String(20), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def seed_database():
    if User.query.first():
        return
    os.makedirs('instance', exist_ok=True)

    dean = User(username='dean', name='Dr. Ramesh Kumar', email='dean@college.edu', role='dean')
    dean.set_password('dean123')
    db.session.add(dean)

    f1 = User(username='faculty1', name='Dr. Priya Sharma', email='priya@college.edu', role='faculty')
    f1.set_password('faculty123')
    f2 = User(username='faculty2', name='Dr. Anil Verma', email='anil@college.edu', role='faculty')
    f2.set_password('faculty123')
    db.session.add_all([f1, f2])
    db.session.flush()

    fp1 = FacultyProfile(user_id=f1.id, faculty_id='FAC001', department='Computer Science', designation='Associate Professor')
    fp2 = FacultyProfile(user_id=f2.id, faculty_id='FAC002', department='Computer Science', designation='Assistant Professor')
    db.session.add_all([fp1, fp2])
    db.session.flush()

    student_data = [
        ('student1', 'Arjun Mehta',  'arjun@college.edu',  'STU001', 3, 5, 'CSE', 8.2),
        ('student2', 'Sneha Patel',  'sneha@college.edu',  'STU002', 3, 5, 'CSE', 7.5),
        ('student3', 'Rohit Singh',  'rohit@college.edu',  'STU003', 2, 3, 'CSE', 6.1),
        ('student4', 'Divya Nair',   'divya@college.edu',  'STU004', 2, 3, 'CSE', 9.0),
    ]
    susers = []
    for uname, name, email, *_ in student_data:
        u = User(username=uname, name=name, email=email, role='student')
        u.set_password('student123')
        db.session.add(u)
        susers.append(u)
    db.session.flush()

    sprofiles = []
    for i, (uname, name, email, sid, yr, sem, branch, cgpa) in enumerate(student_data):
        sp = StudentProfile(user_id=susers[i].id, student_id=sid, year=yr, semester=sem, branch=branch, cgpa=cgpa)
        db.session.add(sp)
        sprofiles.append(sp)
    db.session.flush()

    courses_data = [
        ('CS501', 'Machine Learning',            4, 5, 'CSE', fp1.id),
        ('CS502', 'Database Management Systems', 3, 5, 'CSE', fp2.id),
        ('CS503', 'Computer Networks',           3, 5, 'CSE', fp1.id),
        ('CS504', 'Software Engineering',        3, 5, 'CSE', fp2.id),
        ('CS301', 'Data Structures',             4, 3, 'CSE', fp1.id),
        ('CS302', 'Operating Systems',           3, 3, 'CSE', fp2.id),
        ('CS303', 'Algorithms',                  4, 3, 'CSE', fp1.id),
        ('CS304', 'Object Oriented Programming', 3, 3, 'CSE', fp2.id),
    ]
    courses = []
    for code, name, cred, sem, branch, fid in courses_data:
        c = Course(code=code, name=name, credits=cred, semester=sem, branch=branch, faculty_id=fid)
        db.session.add(c)
        courses.append(c)
    db.session.flush()

    enroll_data = [
        (0,0,8.5,82,24,61),(0,1,7.0,76,19,51),(0,2,9.0,90,26,64),(0,3,6.5,68,17,48),
        (1,0,7.5,79,21,54),(1,1,8.0,85,23,57),(1,2,6.0,62,16,44),(1,3,7.0,74,20,50),
        (2,4,5.5,71,14,41),(2,5,6.0,64,15,45),(2,6,5.0,58,12,38),(2,7,7.0,80,20,50),
        (3,4,9.5,95,28,67),(3,5,9.0,92,27,63),(3,6,8.5,88,25,60),(3,7,9.0,90,27,63),
    ]
    for si, ci, grade, att, intern, extern in enroll_data:
        e = Enrollment(student_id=sprofiles[si].id, course_id=courses[ci].id,
                       grade=grade, attendance_pct=att, internals=intern, externals=extern)
        db.session.add(e)

    notices = [
        Notice(title='End Semester Exam Schedule Released',
               body='The End Semester Examinations will begin on 15th December. Students are advised to check the detailed timetable on the portal.',
               author_id=dean.id, pinned=True),
        Notice(title='Attendance Shortage Warning',
               body='Students with attendance below 75% in any subject must submit a medical certificate or leave letter to the Dean\'s office before 30th November.',
               author_id=dean.id, pinned=False),
        Notice(title='ML Project Submission Deadline',
               body='All students enrolled in CS501 Machine Learning must submit their project reports by 10th December. Late submissions will not be accepted.',
               author_id=f1.id, pinned=False),
    ]
    db.session.add_all(notices)
    db.session.commit()
    print('[SAS] Database ready.')
