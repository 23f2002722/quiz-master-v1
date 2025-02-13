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


@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    user = User.query.get(session["user_id"])
    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Store quiz details in session
    session['quiz_id'] = quiz.id
    session['current_question'] = 0  # Start from the first question
    session['answers'] = {}  # Store user answers

    return redirect(url_for('quiz_page'))

@app.route('/quiz_page', methods=['GET', 'POST'])
def quiz_page():
    user = User.query.get(session["user_id"])
    if 'quiz_id' not in session:
        return redirect(url_for('dashboard'))  # Redirect if quiz not started

    quiz_id = session['quiz_id']
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)
    current_index = session.get('current_question', 0)

    if request.method == 'POST':
        selected_option = request.form.get('option', 'Blank')  # Default to Blank if not selected
        session['answers'][current_index] = selected_option  # Store the answer

        # Navigation Logic
        if 'next' in request.form and current_index < total_questions - 1:
            session['current_question'] += 1
        elif 'prev' in request.form and current_index > 0:
            session['current_question'] -= 1
        elif 'submit' in request.form:
            return redirect(url_for('submit_quiz'))  # Redirect to submit page

    # Get the current question
    current_question = questions[session['current_question']]
    selected_answer = session['answers'].get(current_index, 'Blank')

    return render_template('quiz.html', 
        question=current_question, 
        current_index=current_index + 1, 
        total_questions=total_questions, 
        selected_answer=selected_answer
    )



@app.route('/submit_quiz')
def submit_quiz():
    user = User.query.get(session["user_id"])
    quiz_id = session.get('quiz_id')
    if not quiz_id:
        return redirect(url_for('dashboard'))  # Redirect if session expired

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    user_answers = session.get('answers', {})

    score = 0
    for idx, question in enumerate(questions):
        if user_answers.get(idx, 'Blank') == question.correct_option:
            score += 1

    # Store the final score in Score table
    new_score = Score(user_id=user.id, quiz_id=quiz_id, total_score=score)
    db.session.add(new_score)
    db.session.commit()

    # Clear session after submission
    session.pop('quiz_id', None)
    session.pop('current_question', None)
    session.pop('answers', None)

    flash(f"Quiz Submitted! Your Score: {score}/{len(questions)}")
    return redirect(url_for("dashboard"))



@app.route('/dashboard/view_scores')
@auth_required
def view_scores():
    user = User.query.get(session["user_id"])
    scores = (
        db.session.query(Score, Quiz)
        .join(Quiz, Score.quiz_id == Quiz.id)
        .filter(Score.user_id == user.id)
        .all()
    )

    return render_template('view_scores.html', scores=scores, user=user)