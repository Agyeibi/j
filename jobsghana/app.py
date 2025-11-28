from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(20))
    region = db.Column(db.String(50))
    role = db.Column(db.String(50))  # Job Finder / Job Giver
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    password = db.Column(db.String(200))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    company = db.Column(db.String(150))
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def home():
    return render_template("home.html")

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    region = request.form.get('region')
    role = request.form.get('role')
    gender = request.form.get('gender')
    dob_str = request.form.get('dob')
    password = request.form.get('password')

    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 15:
        flash("You must be at least 15 years old to register.")
        return redirect(url_for('home'))

    user = User.query.filter_by(email=email).first()
    if user:
        flash("Email already registered!")
        return redirect(url_for('home'))

    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, phone=phone, region=region, role=role, gender=gender, dob=dob, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    session['user_name'] = name
    session['user_id'] = new_user.id
    session['role'] = role
    flash("Registration successful!")
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_name'] = user.name
        session['user_id'] = user.id
        session['role'] = user.role
        flash("Login successful!")
        return redirect(url_for('dashboard'))
    flash("Invalid credentials")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_name'):
        flash("Login required!")
        return redirect(url_for('home'))

    if session['role'] == 'Job Giver':
        jobs = Job.query.filter_by(posted_by=session['user_id']).all()
    else:
        jobs = Job.query.all()  # Job Finder sees all jobs

    return render_template("dashboard.html", jobs=jobs)

@app.route('/post-job', methods=['POST'])
def post_job():
    if not session.get('user_name') or session['role'] != 'Job Giver':
        flash("Access denied")
        return redirect(url_for('home'))

    title = request.form.get('title')
    company = request.form.get('company')
    location = request.form.get('location')
    description = request.form.get('description')
    new_job = Job(title=title, company=company, location=location, description=description, posted_by=session['user_id'])
    db.session.add(new_job)
    db.session.commit()
    flash("Job posted successfully!")
    return redirect(url_for('dashboard'))

@app.route('/search')
def search():
    query = request.args.get('query')
    if not session.get('user_name'):
        flash("Register or login to search jobs")
        return redirect(url_for('home'))

    jobs = Job.query.filter(
        (Job.title.contains(query)) | 
        (Job.company.contains(query)) | 
        (Job.location.contains(query))
    ).all()
    return render_template("jobs.html", jobs=jobs, query=query)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
