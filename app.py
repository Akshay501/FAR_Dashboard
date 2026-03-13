from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models.user import user
from models.professor import professor
from models.teachingevaluation import teachingevaluation
from models.service import service
from models.grants import grants
from pdf_generator import generate_far_pdf  # For PDF export
import os
import json  # For JSON handling in scholarly outputs

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Change in production!

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    u = user()
    u.getById(user_id)
    if len(u.data) == 0:
        return None
    usr = User()
    usr.id = u.data[0]['UserID']
    usr.role = u.data[0]['Role']
    usr.professor_key = u.data[0].get('ProfessorKey')
    usr.name = u.data[0]['Name']
    return usr

@app.route('/home')
@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('professor_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        u = user()
        if u.tryLogin(email, password):
            usr = load_user(u.data[0]['UserID'])
            login_user(usr)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/professor/dashboard')
@login_required
def professor_dashboard():
    if current_user.role != 'professor':
        flash('Access denied – professors only', 'danger')
        return redirect(url_for('login'))

    professor_key = current_user.professor_key

    te = teachingevaluation()
    teachings = te.getByProfessor(professor_key)

    svc = service()
    services = svc.getByProfessor(professor_key)

    g = grants()
    grants_list = g.getByProfessor(professor_key)

    prof = professor()
    pubs = prof.getScholarlyOutputs(professor_key)  # Fetch scholarly outputs (JSON list of dicts)

    return render_template('professor/dashboard.html',  # Updated path to match your structure
                           name=current_user.name,
                           teachings=teachings,
                           services=services,
                           grants_list=grants_list,
                           publications=pubs)

@app.route('/import_bibtex', methods=['POST'])
@login_required
def import_bibtex():
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    bibtex_str = request.form.get('bibtex')  # Or handle file upload: request.files['file'].read().decode()
    prof = professor()
    prof.importFromBibTeX(current_user.professor_key, bibtex_str)
    flash('BibTeX imported successfully!', 'success')
    return redirect(url_for('professor_dashboard'))

@app.route('/add_scholarly', methods=['POST'])
@login_required
def add_scholarly():
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    entry_dict = {
        'type': request.form.get('type'),
        'title': request.form.get('title'),
        'authors': request.form.get('authors'),
        'venue': request.form.get('venue'),
        'year': int(request.form.get('year', 0)),
        'doi': request.form.get('doi'),
        'url': request.form.get('url')
    }
    prof = professor()
    prof.addScholarlyOutput(current_user.professor_key, entry_dict)
    flash('Scholarly output added!', 'success')
    return redirect(url_for('professor_dashboard'))

@app.route('/edit_teaching/<int:eval_id>', methods=['GET', 'POST'])
@login_required
def edit_teaching(eval_id):
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    te = teachingevaluation()
    te.getById(eval_id)
    if len(te.data) == 0 or te.data[0]['ProfessorKey'] != current_user.professor_key:
        flash('Evaluation not found or access denied', 'danger')
        return redirect(url_for('professor_dashboard'))

    if request.method == 'POST':
        # Update fields from form
        te.data[0]['Term'] = request.form.get('Term')
        # Add other fields as needed (e.g., Course, Enrollment, etc. - expand form in template)
        te.update()
        flash('Teaching evaluation updated!', 'success')
        return redirect(url_for('professor_dashboard'))

    return render_template('professor/edit_teaching.html', eval=te.data[0])  # Updated path to match your structure

@app.route('/export_far')
@login_required
def export_far():
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    professor_key = current_user.professor_key
    pdf_bytes = generate_far_pdf(professor_key)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=faculty_activity_report.pdf'
    return response

@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied – admins only', 'danger')
        return redirect(url_for('login'))

    search_name = request.form.get('search_name', '') if request.method == 'POST' else ''
    search_dept = request.form.get('search_dept', '') if request.method == 'POST' else ''
    search_googleid = request.form.get('search_googleid', '') if request.method == 'POST' else ''
    search_orcid = request.form.get('search_orcid', '') if request.method == 'POST' else ''

    prof = professor()
    sql = "SELECT * FROM `PROFESSOR` WHERE 1=1"
    params = []

    if search_name:
        sql += " AND (FirstName LIKE %s OR LastName LIKE %s)"
        params.extend([f"%{search_name}%", f"%{search_name}%"])

    if search_dept:
        sql += " AND Department LIKE %s"
        params.append(f"%{search_dept}%")

    if search_googleid:
        sql += " AND GoogleID LIKE %s"
        params.append(f"%{search_googleid}%")

    if search_orcid:
        sql += " AND ORCID LIKE %s"
        params.append(f"%{search_orcid}%")

    prof.cur.execute(sql, params)
    professors = prof.cur.fetchall()

    return render_template('admin/dashboard.html',
                           professors=professors,
                           search_name=search_name,
                           search_dept=search_dept,
                           search_googleid=search_googleid,
                           search_orcid=search_orcid)

@app.route('/admin/professor/<int:professor_key>')
@login_required
def admin_view_professor(professor_key):
    if current_user.role != 'admin':
        flash('Access denied – admins only', 'danger')
        return redirect(url_for('login'))

    prof = professor()
    prof.getById(professor_key)
    if len(prof.data) == 0:
        flash('Professor not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    professor_data = prof.data[0]

    return render_template('admin/view_professor.html',
                           professor=professor_data)

if __name__ == '__main__':
    app.run(debug=True)