from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import secrets
import json

app = Flask(__name__)
apikey = secrets.token_hex(16)
app.secret_key = apikey
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mcq_app.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    department = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)






# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin

            # Check if the user has already submitted the exam
            existing_result = Result.query.filter_by(user_id=user.id).first()
            if existing_result:
                return redirect(url_for('test_result'))  # Redirect to result page if exam is submitted

            return redirect(url_for('dashboard'))  # Redirect to dashboard if no result

        return 'Invalid credentials'

    return render_template('login.html')



@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))




@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if session.get('submitted'):
        return redirect(url_for('test_result'))
    return render_template('dashboard.html')




@app.route('/get_questions', methods=['GET'])
def get_questions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    # Check if question order is already in session
    if 'question_order' not in session:
        questions = Question.query.all()
        question_ids = [q.id for q in questions]
        random.shuffle(question_ids)  # Shuffle question IDs randomly
        session['question_order'] = question_ids
    else:
        question_ids = session['question_order']

    # Fetch questions in the shuffled order stored in session
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    question_data = []
    for question in sorted(questions, key=lambda q: question_ids.index(q.id)):
        question_data.append({
            'id': question.id,
            'text': question.text,
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'option_d': question.option_d
        })

    return jsonify({'questions': question_data})




@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        text = request.form['text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']
        question = Question(text=text, option_a=option_a, option_b=option_b, option_c=option_c, option_d=option_d, correct_option=correct_option)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    questions = Question.query.all()
    results = Result.query.all()
    return render_template('admin_dashboard.html', questions=questions, results=results)




@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    answered_questions = request.form.get('answers', '{}')
    answered_questions = json.loads(answered_questions)  # Parse JSON string to a dictionary
    score = 0
    result_details = []

    for question_id, selected_option in answered_questions.items():
        question = Question.query.get(question_id)
        is_correct = question and selected_option == question.correct_option
        if is_correct:
            score += 1

        # Store each submission
        submission = Submission(
            user_id=user_id,
            question_id=question_id,
            selected_option=selected_option,
            is_correct=is_correct
        )
        db.session.add(submission)

        # Prepare result details for rendering on result.html
        result_details.append({
            'question': question,
            'user_answer': selected_option,
            'correct_option': question.correct_option,
            'is_correct': is_correct
        })

    # Store the overall result
    result = Result(user_id=user_id, score=score)
    db.session.add(result)
    db.session.commit()

    # Set session flag to indicate exam submission
    session['submitted'] = True

    # Redirect to the result page
    return render_template('report.html', score=score, result_details=result_details)




@app.route('/test_result')
def test_result():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    user_id = session['user_id']

    # Fetch result for the logged-in user
    result = Result.query.filter_by(user_id=user_id).first()
    if not result:
        return redirect(url_for('dashboard'))  # Redirect if no result is found

    # Fetch all submissions for the logged-in user
    submissions = Submission.query.filter_by(user_id=user_id).all()
    result_details = []

    for submission in submissions:
        question = Question.query.get(submission.question_id)
        result_details.append({
            'question': question,
            'user_answer': submission.selected_option,
            'correct_option': question.correct_option,
            'is_correct': submission.is_correct
        })

    return render_template(
        'report.html',
        score=result.score,
        result_details=result_details
    )




@app.route('/analytics')
def analytics():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    total_users = User.query.count()
    total_results = Result.query.count()
    pass_count = Result.query.filter(Result.score >= 5).count()  # Assuming passing score is 5
    return render_template('analytics.html', total_users=total_users, total_results=total_results, pass_count=pass_count)





@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        department = request.form['department']
        password = request.form['password']
        is_admin = 'is_admin' in request.form  # Check if the checkbox is checked

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new user
        new_user = User(username=username, name=name, department=department, password_hash=hashed_password, is_admin=is_admin)

        # Add to the database
        db.session.add(new_user)
        db.session.commit()

        # Flash success message
        flash("User added successfully", "success")

        return redirect(url_for('add_user'))  # Redirect to the same page to clear the form

    return render_template('admin_dashboard.html')




# Route to modify a question that has been previously entered
@app.route('/modify/<int:question_id>', methods=['GET', 'POST'])
def modify_question(question_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        question.text = request.form['text']
        question.option_a = request.form['option_a']
        question.option_b = request.form['option_b']
        question.option_c = request.form['option_c']
        question.option_d = request.form['option_d']
        question.correct_option = request.form['correct_option']

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('modify_question.html', question=question)



# Route to delete a question that is no longer needed
@app.route('/delete/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))



@app.route('/clear_results', methods=['POST'])
def clear_results():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    try:
        # Delete all records in Result and Submission tables
        db.session.query(Result).delete()
        db.session.query(Submission).delete()
        db.session.commit()
        flash("All results and submissions have been cleared successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('admin_dashboard'))





with app.app_context():
    db.create_all()
    user_exists = User.query.filter_by(username="oluwatobi.akomolafe@oryoltd.com").first()

    if not user_exists:
        # Creating the new user
        hashed_password = generate_password_hash("12345")
        new_user = User(username="oluwatobi.akomolafe@oryoltd.com", name="Oluwatobi Akomolafe", department='Technical', password_hash=hashed_password, is_admin=True)

        # Add user to the database
        db.session.add(new_user)
        db.session.commit()
        print("User 'oluwatobi.akomolafe@oryoltd.com' added successfully!")
    else:
        print("User 'oluwatobi.akomolafe@oryoltd.com' already exists!")

if __name__ == '__main__':
    app.run(debug=True)
