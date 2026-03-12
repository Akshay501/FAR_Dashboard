from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models.user import user
from models.professor import professor
from models.teachingevaluation import teachingevaluation
from models.service import service
from models.grants import grants
import os

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
        elif current_user.role == 'professor':
            return redirect(url_for('professor_dashboard'))
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        u = user()
        if u.tryLogin(email, password):
            usr = User()
            usr.id = u.data[0]['UserID']
            usr.role = u.data[0]['Role']
            usr.professor_key = u.data[0].get('ProfessorKey')
            usr.name = u.data[0]['Name']
            login_user(usr)
            flash(f'Welcome, {usr.name}!', 'success')

            if usr.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('professor_dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/professor/dashboard')
@login_required
def professor_dashboard():
    if current_user.role != 'professor':
        return redirect(url_for('login'))

    # Fetch teaching evaluations
    te = teachingevaluation()
    te.getByProfessor(current_user.professor_key)
    evals = te.data

    # Fetch service activities
    srv = service()
    srv.getByProfessor(current_user.professor_key)
    services = srv.data

    # Fetch grants
    gr = grants()
    gr.getByProfessor(current_user.professor_key)
    grants_list = gr.data

    return render_template('professor/dashboard.html',
                           name=current_user.name,
                           professor_key=current_user.professor_key,
                           evals=evals,
                           services=services,
                           grants_list=grants_list)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied – admins only', 'danger')
        return redirect(url_for('login'))

    # Get all filter values (from GET or POST)
    search_name     = request.form.get('search_name', request.args.get('search_name', '')).strip()
    search_dept     = request.form.get('search_dept', request.args.get('search_dept', '')).strip()
    search_googleid = request.form.get('search_googleid', request.args.get('search_googleid', '')).strip()
    search_orcid    = request.form.get('search_orcid', request.args.get('search_orcid', '')).strip()

    # Build dynamic SQL query
    prof = professor()
    sql = "SELECT * FROM `PROFESSOR` WHERE 1=1"
    params = []

    if search_name:
        sql += " AND CONCAT(`FirstName`, ' ', `LastName`) LIKE %s"
        params.append(f"%{search_name}%")

    if search_dept:
        sql += " AND `Department` LIKE %s"
        params.append(f"%{search_dept}%")

    if search_googleid:
        sql += " AND `GoogleID` LIKE %s"
        params.append(f"%{search_googleid}%")

    if search_orcid:
        sql += " AND `ORCID` LIKE %s"
        params.append(f"%{search_orcid}%")

    sql += " ORDER BY `EmployeeID` ASC"

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

    # Fetch professor details
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