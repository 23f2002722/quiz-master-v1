import io
import csv
from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *
from controllers.controllers1 import *
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
            return redirect(url_for("home"))

    return inner

# ================
# Dashboard Route 
# ================
@app.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard():
        user = User.query.get(session["user_id"])
        if user.role=="user":
            return render_template("dashboard.html",user=user)
        else:
             subject=db.session.query(Subject).all()
             chapters=db.session.query(Chapter).all()
             chapter_questions_count = {
        chapter.id: db.session.query(Question)
        .join(Quiz)
        .filter(Quiz.chapter_id == chapter.id)
        .count()
        for chapter in chapters
    }
             return render_template("admin.html",user=user,subject=subject,chapters=chapters,chapter_questions_count=chapter_questions_count)

# ================
# Add Subject 
# ================
@app.route("/dashboard/admin/add_subject", methods=["GET", "POST"])
@auth_required
def add_subject():
        user = User.query.get(session["user_id"])
        if request.method=="POST":
             name = request.form.get("name")
             description = request.form.get("description")
             subject = Subject(name=name,description=description)
             db.session.add(subject)
             db.session.commit()
             return redirect(url_for("dashboard"))
             
        else:
             return render_template("add_subject.html",user=user)
        
# ================
# Delete Subject 
# ================
@app.route("/dashboard/admin/delete_subject/<int:subject_id>", methods=["POST"])
@auth_required
def delete_subject(subject_id):
    sub = Subject.query.filter_by(id=subject_id).first()
    db.session.delete(sub)
    db.session.commit()
    return redirect(url_for("dashboard"))


# ================
# Add Chapter 
# ================
@app.route("/dashboard/admin/add_chapter/<int:subject_id>", methods=["GET","POST"])
@auth_required
def add_chapter(subject_id):
    user = User.query.get(session["user_id"])
    if request.method=="POST":
        name = request.form.get("name")
        description = request.form.get("description")
        chapter = Chapter(name=name,description=description,subject_id=subject_id)
        db.session.add(chapter)
        db.session.commit()
        return redirect(url_for("dashboard"))
    else:
        return render_template("add_chapter.html",subject_id=subject_id,user=user)
    

# ================
# Edit Chapter 
# ================
@app.route("/dashboard/admin/edit_chapter/<int:chapter_id>", methods=["POST"])
@auth_required
def edit_chapter(chapter_id):
     return render_template("blank.html")


# ================
# Delete Chapter 
# ================
@app.route("/dashboard/admin/delete_chapter/<int:chapter_id>", methods=["POST"])
@auth_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.filter_by(id=chapter_id).first()
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for("dashboard"))


# ================
# Quiz Management 
# ================
@app.route("/dashboard/quiz_management", methods=["GET","POST"])
@auth_required
def quiz_management():
     user=User.query.get(session["user_id"])
     quiz=db.session.query(Quiz).all()
     return render_template("quiz_management.html",user=user,quiz=quiz)


# ================
# Chapterwise Quiz 
# ================
@app.route("/dashboard/quiz/<int:chapter_id>", methods=["GET","POST"])
@auth_required
def quiz(chapter_id):
     user=User.query.get(session["user_id"])
     quiz=Quiz.query.filter_by(chapter_id=chapter_id).all()
     return render_template("quiz_management.html",user=user,quiz=quiz)


# ================
# Add Quiz 
# ================
@app.route("/dashboard/quiz_management/add_quiz", methods=["GET","POST"])
@auth_required
def add_quiz():
    user = User.query.get(session["user_id"])
    if request.method=="POST":
        type = request.form.get("type")
        chapter_id = request.form.get("chapter_id")
        date_of_quiz = request.form.get("date")
        duration = request.form.get("duration")
        remarks = request.form.get("remarks")

        # Validate the form data
        if not chapter_id or not date or not type or not duration:
            flash("All fields are required to create a slot.", "danger")
            return redirect(url_for("add_quiz"))

        # Validate duration input
        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError("Duration must be positive.")
        except ValueError:
            flash(
                "Invalid duration. Please enter a valid number greater than zero.",
                "danger",
            )
            return redirect(url_for("add_quiz"))

        # Parse date and time to proper formats
        try:
            date_of_quiz = datetime.strptime(date_of_quiz, "%Y-%m-%d").date()
        except ValueError:
            flash(
                "Invalid date format. Use YYYY-MM-DD for date and HH:MM for time.",
                "danger",
            )
            return redirect(url_for("add_quiz"))
        
        quiz = Quiz(type=type,chapter_id=chapter_id,date_of_quiz=date_of_quiz,time_duration=duration,remarks=remarks)
        db.session.add(quiz)
        db.session.commit()
        return redirect(request.referrer)
    else:
        chapter=db.session.query(Chapter).all()
        return render_template("add_quiz.html",user=user,chapter=chapter)


# ================
# Delete Quiz 
# ================
@app.route("/dashboard/delete_quiz/<int:quiz_id>", methods=["POST"])
@auth_required
def delete_quiz(quiz_id):
    quiz=Quiz.query.filter_by(id=quiz_id).first()
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully.")
    return redirect(request.referrer)


# ================
# Add Question 
# ================
@app.route("/dashboard/quiz_management/add_question/<int:quiz_id>", methods=["GET","POST"])
@auth_required
def add_question(quiz_id):
    if request.method == 'POST':
        statement = request.form.get('question_statement')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correct_option')

        # Validation (Ensure all fields are filled)
        if not all([statement, option1, option2, option3, option4, correct_option]):
            flash('All fields are required!', 'danger')
            return redirect(url_for('add_question', quiz_id=quiz_id))

        # Create new question instance
        new_question = Question(
            quiz_id=quiz_id,
            question_statement=statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=int(correct_option)
        )

        # Add to database
        db.session.add(new_question)
        db.session.commit()

        flash('Question added successfully!', 'success')

        # Redirect back to the same quiz page after adding
        return redirect(url_for('add_question', quiz_id=quiz_id),code=303)
    
    else:
        user = User.query.get(session["user_id"])
        quiz=Quiz.query.filter_by(id=quiz_id).first()
        question_count = Question.query.filter_by(quiz_id=quiz_id).count()
        return render_template("add_question.html",user=user,quiz=quiz,count=question_count+1)
    

# ================
# Edit Question 
# ================
@app.route("/dashboard/quiz_management/edit_question/<int:question_id>", methods=["POST"])
@auth_required
def edit_question(question_id):
     return render_template("blank.html")


# ================
# Delete Question 
# ================
@app.route("/dashboard/quiz_management/delete_question/<int:question_id>", methods=["POST"])
@auth_required
def delete_question(question_id):
    question=Question.query.filter_by(id=question_id).first()
    db.session.delete(question)
    db.session.commit()
    return redirect(request.referrer)
   