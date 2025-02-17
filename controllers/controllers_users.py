import io
import csv
from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *
from controllers.controllers_login import *
from controllers.controllers_admin import *
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from sqlalchemy import func
from functools import wraps

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("index"))

    return inner


# ==================
# Start Quiz
# ==================
@app.route('/start_quiz/<int:quiz_id>', methods=['GET'])
@auth_required
def start_quiz(quiz_id):
    user = User.query.get(session["user_id"])
    quiz = Quiz.query.get_or_404(quiz_id)

    existing_score = Score.query.filter_by(user_id=user.id, quiz_id=quiz.id).first()
    if existing_score:
        flash("You have already attempted this quiz!", "warning")
        return redirect(url_for('dashboard'))

    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    if not questions:
        flash("No questions available for this quiz.", "warning")
        return redirect(url_for('dashboard'))

    session['quiz_state'] = {
        'quiz_id': int(quiz.id), 
        'user_id': int(user.id), 
        'current_question': 0, 
        'responses': {},
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
        'time_duration': int(quiz.time_duration) * 60  
    }

    return redirect(url_for('quiz_page'))


# ==================
# Quiz Page
# ==================
@app.route('/quiz_page', methods=['GET', 'POST'])
@auth_required
def quiz_page():
    user = User.query.get(session["user_id"])
    quiz_state = session.get('quiz_state')

    if not quiz_state:
        flash("No active quiz found!", "danger")
        return redirect(url_for('dashboard'))

    quiz_id = quiz_state['quiz_id']
    current_index = quiz_state['current_question']  # Keep as integer for navigation
    questions = Question.query.filter_by(quiz_id=quiz_id).all()


    if request.method == 'POST':
        selected_option = request.form.get('option')

        if selected_option is not None:
            quiz_state['responses'][str(current_index)] = selected_option

        if 'next' in request.form and current_index < len(questions) -1:
            quiz_state['current_question'] += 1
        elif 'prev' in request.form and current_index > 0:
            quiz_state['current_question'] -= 1
        elif 'submit' in request.form:
            if selected_option is not None:
                quiz_state['responses'][str(current_index)] = selected_option
            session['quiz_state'] = quiz_state
            session.modified = True
            return redirect(url_for('submit_quiz'))


        session['quiz_state'] = quiz_state
        session.modified = True  # Ensure Flask saves the updated session

        return redirect(url_for('quiz_page'))


    elapsed_time = (datetime.now() - datetime.strptime(quiz_state['start_time'], '%Y-%m-%d %H:%M:%S')).total_seconds()
    time_left = max(0, quiz_state['time_duration'] - elapsed_time)


    current_question = questions[current_index]
    selected_answer = quiz_state['responses'].get(str(current_index), None)
   
    return render_template('quiz.html', 
                           question=current_question, 
                           total=len(questions), 
                           index=current_index + 1, 
                           time_left=int(time_left), 
                           selected=selected_answer, 
                           user=user)

# ==================
# Submit Quiz
# ==================
@app.route('/submit_quiz', methods=['POST', 'GET'])
@auth_required
def submit_quiz():
    user = User.query.get(session["user_id"])
    quiz_state = session.get('quiz_state')

    if not quiz_state:
        flash("Quiz session expired or invalid submission!", "danger")
        return redirect(url_for('dashboard'))

    quiz_id = quiz_state['quiz_id']
    user_id = user.id
    responses = quiz_state['responses']
    print(responses)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    total_score = 0

    for index, question in enumerate(questions):
        selected_answer = str(responses.get(str(index), "")).strip().lower()
        correct_answer = str(question.correct_option).strip().lower()
        print(selected_answer,correct_answer)
        if selected_answer == correct_answer:
            total_score += 1

    new_score = Score(user_id=user_id, quiz_id=quiz_id, total_score=total_score, timestamp=datetime.now())
    db.session.add(new_score)
    db.session.commit()

    session.pop('quiz_state', None)
    
    flash(f"Quiz submitted! Your score: {total_score}/{len(questions)}", "success")
    return redirect(url_for('dashboard'))


# ==================
# Score card
# ==================
@app.route('/dashboard/scores/<int:user_id>')
@auth_required
def view_scores(user_id):
    user = User.query.get(session["user_id"])

    scores = db.session.query(Score, Quiz).join(Quiz, Score.quiz_id == Quiz.id).filter(Score.user_id == user_id).all()
    quiz_questions_count = {
    quiz.id: db.session.query(Question).filter(Question.quiz_id == quiz.id).count()
    for quiz in Quiz.query.all()
}
    return render_template('scores.html', scores=scores, quiz_questions_count=quiz_questions_count, user=user)


# ==================
# Summary
# ==================
@app.route('/summary')
@auth_required
def summary():
    user = User.query.get(session["user_id"])

    if user.role == "admin":
        subject_wise_top_scores = db.session.query(
            Subject.name,
            db.func.max(Score.total_score).label('top_score')
        ).join(Chapter, Chapter.subject_id == Subject.id)\
         .join(Quiz, Quiz.chapter_id == Chapter.id)\
         .join(Score, Score.quiz_id == Quiz.id)\
         .group_by(Subject.name)\
         .all()

        subject_wise_user_attempts = db.session.query(
            Subject.name,
            db.func.count(db.distinct(Score.user_id)).label('user_count')
        ).join(Chapter, Chapter.subject_id == Subject.id)\
         .join(Quiz, Quiz.chapter_id == Chapter.id)\
         .join(Score, Score.quiz_id == Quiz.id)\
         .group_by(Subject.name)\
         .all()

        return render_template('summary_admin.html', 
                               subject_wise_top_scores=subject_wise_top_scores, 
                               subject_wise_user_attempts=subject_wise_user_attempts, 
                               user=user)
    else:
        subject_wise_attempts = db.session.query(
            Subject.name,
            db.func.count(Score.id).label('attempt_count')
        ).join(Chapter, Chapter.subject_id == Subject.id)\
         .join(Quiz, Quiz.chapter_id == Chapter.id)\
         .join(Score, Score.quiz_id == Quiz.id)\
         .filter(Score.user_id == user.id)\
         .group_by(Subject.name)\
         .all()

        month_wise_attempts = db.session.query(
            db.func.strftime('%Y-%m', Score.timestamp).label('month'),
            db.func.count(Score.id).label('attempt_count')
        ).filter(Score.user_id == user.id)\
         .group_by(db.func.strftime('%Y-%m', Score.timestamp))\
         .all()

        return render_template('summary_user.html', 
                               subject_wise_attempts=subject_wise_attempts, 
                               month_wise_attempts=month_wise_attempts, 
                               user=user)

# ==================
# Quiz Analytics
# ==================
@app.route('/quiz_analytics/<int:quiz_id>')
@auth_required
def quiz_analytics(quiz_id):
    user = User.query.get(session["user_id"])

    if user.role != "admin":
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('dashboard'))

    quiz_attempts = db.session.query(
        User.id,
        User.full_name,
        User.username,
        Score.total_score,
        Score.timestamp,
        Score.quiz_id
    ).join(Score, Score.user_id == User.id)\
     .filter(Score.quiz_id == quiz_id)\
     .all()
    quiz_questions_count = {
    quiz_id: db.session.query(Question).filter(Question.quiz_id == quiz_id).count()
}
    return render_template('quiz_analytics.html', 
                           quiz_attempts=quiz_attempts, 
                           quiz_id=quiz_id,
                           quiz_questions_count=quiz_questions_count,
                           user=user)