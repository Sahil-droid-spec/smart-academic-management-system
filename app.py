import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import (db, seed_database, User, StudentProfile, FacultyProfile,
                    Course, Enrollment, Notice, ChatMessage)
from ai.assistant import get_ai_response


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs('instance', exist_ok=True)

    db.init_app(app)

    lm = LoginManager()
    lm.init_app(app)
    lm.login_view = 'login'
    lm.login_message = 'Please log in to continue.'

    @lm.user_loader
    def load_user(uid):
        return db.session.get(User, int(uid))

    with app.app_context():
        db.create_all()
        seed_database()

    def role_required(*roles):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not current_user.is_authenticated:
                    return redirect(url_for('login'))
                if current_user.role not in roles:
                    flash('Access denied.', 'danger')
                    return redirect(url_for('dashboard'))
                return f(*args, **kwargs)
            return wrapped
        return decorator

    # ── AUTH ──────────────────────────────────────────────────
    @app.route('/', methods=['GET', 'POST'])
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        error = None
        if request.method == 'POST':
            u = User.query.filter_by(username=request.form.get('username', '').strip()).first()
            if u and u.check_password(request.form.get('password', '').strip()):
                login_user(u, remember=True)
                return redirect(url_for('dashboard'))
            error = 'Invalid username or password.'
        return render_template('login.html', error=error)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role == 'student': return redirect(url_for('student_dashboard'))
        if current_user.role == 'faculty': return redirect(url_for('faculty_dashboard'))
        if current_user.role == 'dean':    return redirect(url_for('dean_dashboard'))
        return redirect(url_for('login'))

    # ── STUDENT ───────────────────────────────────────────────
    @app.route('/student')
    @login_required
    @role_required('student')
    def student_dashboard():
        profile = current_user.student_profile
        enrollments = (Enrollment.query
                       .filter_by(student_id=profile.id)
                       .join(Course).order_by(Course.code).all())
        notices = Notice.query.order_by(Notice.pinned.desc(), Notice.created_at.desc()).limit(5).all()
        total_credits  = sum(e.course.credits for e in enrollments)
        earned_credits = sum(e.course.credits for e in enrollments if e.grade and e.grade >= 5.0)
        avg_att = (sum(e.attendance_pct for e in enrollments) / len(enrollments)) if enrollments else 0
        at_risk = [e for e in enrollments if e.attendance_pct < 75]
        return render_template('student.html', profile=profile, enrollments=enrollments,
                               notices=notices, total_credits=total_credits,
                               earned_credits=earned_credits, avg_attendance=round(avg_att, 1),
                               at_risk_courses=at_risk)

    # ── FACULTY ───────────────────────────────────────────────
    @app.route('/faculty')
    @login_required
    @role_required('faculty')
    def faculty_dashboard():
        fp = current_user.faculty_profile
        courses = Course.query.filter_by(faculty_id=fp.id).all()
        course_stats = []
        for course in courses:
            enrolls = Enrollment.query.filter_by(course_id=course.id).all()
            graded = [e for e in enrolls if e.grade is not None]
            avg_grade = sum(e.grade for e in graded) / len(graded) if graded else 0
            avg_att   = sum(e.attendance_pct for e in enrolls) / len(enrolls) if enrolls else 0
            at_risk   = len([e for e in enrolls if e.attendance_pct < 75])
            course_stats.append({'course': course, 'enrollments': enrolls,
                                  'count': len(enrolls), 'avg_grade': round(avg_grade, 2),
                                  'avg_att': round(avg_att, 1), 'at_risk': at_risk})
        notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
        total_students = sum(c['count'] for c in course_stats)
        return render_template('faculty.html', fp=fp, course_stats=course_stats,
                               notices=notices, total_students=total_students)

    @app.route('/faculty/update-grade', methods=['POST'])
    @login_required
    @role_required('faculty')
    def update_grade():
        data = request.get_json()
        e = db.session.get(Enrollment, data.get('enrollment_id'))
        if not e:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        if e.course.faculty_id != current_user.faculty_profile.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        if data.get('grade')      is not None: e.grade          = float(data['grade'])
        if data.get('attendance') is not None: e.attendance_pct = float(data['attendance'])
        if data.get('internals')  is not None: e.internals      = float(data['internals'])
        if data.get('externals')  is not None: e.externals      = float(data['externals'])
        sp = e.student
        all_e = Enrollment.query.filter_by(student_id=sp.id).all()
        graded = [x for x in all_e if x.grade is not None]
        if graded:
            sp.cgpa = round(sum(x.grade * x.course.credits for x in graded) /
                            sum(x.course.credits for x in graded), 2)
        db.session.commit()
        return jsonify({'success': True, 'cgpa': sp.cgpa, 'grade_letter': e.grade_letter})

    @app.route('/faculty/post-notice', methods=['POST'])
    @login_required
    @role_required('faculty', 'dean')
    def post_notice():
        title  = request.form.get('title', '').strip()
        body   = request.form.get('body',  '').strip()
        pinned = request.form.get('pinned') == 'on'
        if title and body:
            db.session.add(Notice(title=title, body=body, author_id=current_user.id, pinned=pinned))
            db.session.commit()
            flash('Notice posted.', 'success')
        else:
            flash('Title and content are required.', 'danger')
        return redirect(request.referrer or url_for('faculty_dashboard'))

    # ── DEAN ──────────────────────────────────────────────────
    @app.route('/dean')
    @login_required
    @role_required('dean')
    def dean_dashboard():
        students  = StudentProfile.query.join(User).order_by(StudentProfile.cgpa.desc()).all()
        faculties = FacultyProfile.query.join(User).all()
        courses   = Course.query.all()
        notices   = Notice.query.order_by(Notice.pinned.desc(), Notice.created_at.desc()).all()
        total_students = len(students)
        avg_cgpa  = round(sum(s.cgpa for s in students) / max(total_students, 1), 2)
        low_cgpa  = [s for s in students if s.cgpa < 6.0]
        all_e     = Enrollment.query.all()
        low_att   = len({e.student_id for e in all_e if e.attendance_pct < 75})
        grade_dist = {'O': 0, 'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'F': 0}
        for e in all_e:
            gl = e.grade_letter
            if gl in grade_dist: grade_dist[gl] += 1
        return render_template('dean.html', students=students, faculties=faculties,
                               courses=courses, notices=notices, total_students=total_students,
                               avg_cgpa=avg_cgpa, low_cgpa=low_cgpa, low_att_count=low_att,
                               grade_dist=grade_dist)

    @app.route('/dean/delete-notice/<int:nid>', methods=['POST'])
    @login_required
    @role_required('dean')
    def delete_notice(nid):
        n = Notice.query.get_or_404(nid)
        db.session.delete(n)
        db.session.commit()
        flash('Notice deleted.', 'success')
        return redirect(url_for('dean_dashboard'))

    # ── AI CHAT ───────────────────────────────────────────────
    @app.route('/ai/chat', methods=['POST'])
    @login_required
    def ai_chat():
        msg = request.get_json().get('message', '').strip()
        if not msg: return jsonify({'error': 'Empty'}), 400
        db.session.add(ChatMessage(user_id=current_user.id, role='user', content=msg))
        db.session.flush()
        history = (ChatMessage.query.filter_by(user_id=current_user.id)
                   .order_by(ChatMessage.created_at.asc()).limit(20).all())
        messages = [{'role': m.role, 'content': m.content} for m in history]
        reply = get_ai_response(messages, app.config['GROQ_API_KEY'], app.config['GROQ_MODEL'])
        db.session.add(ChatMessage(user_id=current_user.id, role='assistant', content=reply))
        db.session.commit()
        return jsonify({'reply': reply})

    @app.route('/ai/history')
    @login_required
    def ai_history():
        msgs = (ChatMessage.query.filter_by(user_id=current_user.id)
                .order_by(ChatMessage.created_at.asc()).limit(30).all())
        return jsonify([{'role': m.role, 'content': m.content} for m in msgs])

    @app.route('/ai/clear', methods=['POST'])
    @login_required
    def ai_clear():
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/enrollment/<int:eid>')
    @login_required
    def get_enrollment(eid):
        e = Enrollment.query.get_or_404(eid)
        return jsonify({'id': e.id, 'grade': e.grade, 'attendance_pct': e.attendance_pct,
                        'internals': e.internals, 'externals': e.externals})

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
