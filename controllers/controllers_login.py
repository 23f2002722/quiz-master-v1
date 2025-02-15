from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *
from controllers.controllers_admin import *
from controllers.controllers_users import *
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("home"))

    return inner

#Login/home page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")

        if not username or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("index"))
        
        user = User.query.filter_by(username=username).first()

        if not user:
            flash("User not found.")
            return redirect(url_for("index"))
        
        if not check_password_hash(user.password_hash, password):
            flash("Incorrect password.")    
            return redirect(url_for("index"))
        
        session["user_id"]=user.id
        flash("Login successfully")
        return redirect(url_for("dashboard"))
    
    else:
        if "user_id" in session:
            session.pop("user_id")

        return render_template("index.html")

@app.route("/register_user", methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        username = request.form.get("username")
        full_name = request.form.get("name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        dob = request.form.get("dob")
        qualification = request.form.get("qualification")

        if not username or not full_name or not password or not confirm_password or not dob or not qualification:
            flash("Please fill in all fields.")
            return redirect(url_for("register_user"))
        
        elif password != confirm_password:
            flash("Password do not match")
            return redirect(url_for("register_user"))
        
        user = User.query.filter_by(username=username).first()

        if user:
            flash("User already exists.")
            return redirect(url_for("index"))

        password_hash = generate_password_hash(password)
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        new_user = User(username=username, full_name=full_name, password_hash=password_hash, qualification=qualification, dob=dob_date)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("index"))
    
    else:
        if "user_id" in session:
            session.pop("user_id")

        return render_template("register_user.html")
    

# Logout
@app.route("/logout")
@auth_required
def logout():
    session.pop("user_id")
    flash("Logged out successfully")

    return redirect(url_for("index"))


# Profile
@app.route("/profile", methods=["GET", "POST"])
@auth_required
def profile():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        name = request.form.get("name")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")

        if not current_password or not new_password or not confirm_password:
            flash("Please fill out all the required fields")
            return redirect(url_for("profile"))

        if not check_password_hash(user.password_hash, current_password):
            flash("Incorrect password")
            return redirect(url_for("profile"))

        if new_password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("profile"))

        new_password_hash = generate_password_hash(new_password)
        user.full_name = name
        user.password_hash = new_password_hash
        user.username = email

        db.session.commit()

        flash("Profile updated successfully")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)



@app.route('/search', methods=['GET'])
@auth_required
def search():
    current_user = User.query.get(session["user_id"])
    category = request.args.get('category')
    query = request.args.get('query', '').strip()

    if current_user.role == "admin":
        # Admin search logic
        if category == "users":
            # Search users by name, username (email), or DOB
            users = User.query.filter(
                (User.full_name.ilike(f"%{query}%")) | 
                (User.username.ilike(f"%{query}%")) | 
                (User.dob.ilike(f"%{query}%")) , (User.role != "admin")
            ).all()
            
            return render_template('search.html', category=category, users=users, user=current_user)

        elif category == "quiz":
            # Search quiz by type, chapter name, or subject name
            quiz = Quiz.query.join(Chapter).join(Subject).filter(
                (Quiz.type.ilike(f"%{query}%")) | 
                (Chapter.name.ilike(f"%{query}%")) | 
                (Subject.name.ilike(f"%{query}%"))
            ).all()
            quiz_questions_count = {
    quiz.id: db.session.query(Question).filter(Question.quiz_id == quiz.id).count()
    for quiz in quiz
}
            return render_template('search.html', category=category, quiz=quiz, user=current_user,  quiz_questions_count=quiz_questions_count)

        elif category == "chapters":
            # Search chapters by name
            chapters = Chapter.query.filter(
                Chapter.name.ilike(f"%{query}%")
            ).all()
            chapter_questions_count = {chapter.id: db.session.query(Question).join(Quiz).filter(Quiz.chapter_id == chapter.id).count()
             for chapter in chapters}
            return render_template('search.html', category=category, chapters=chapters, user=current_user,chapter_questions_count=chapter_questions_count)

        elif category == "subjects":
            # Search subjects by name
            subjects = Subject.query.filter(
                Subject.name.ilike(f"%{query}%")
            ).all()
            return render_template('search.html', category=category, subjects=subjects, user=current_user)

    else:
        # User search logic
        if category == "quiz":
            # Search quiz by type, chapter name, or subject name
            quiz = Quiz.query.join(Chapter).join(Subject).filter(
                (Quiz.type.ilike(f"%{query}%")) | 
                (Chapter.name.ilike(f"%{query}%")) | 
                (Subject.name.ilike(f"%{query}%"))
            ).all()
            return render_template('search.html', category=category, quiz=quiz, user=current_user)

        elif category == "scores":
            # Search scores by date of attempt, score, chapter name, type, or subject name
            scores = db.session.query(Score, Quiz).join(Quiz).join(Chapter).join(Subject).filter(
                (Score.user_id == current_user.id) & 
                (
                    (Score.timestamp.ilike(f"%{query}%")) | 
                    (Score.total_score.ilike(f"%{query}%")) | 
                    (Chapter.name.ilike(f"%{query}%")) | 
                    (Quiz.type.ilike(f"%{query}%")) | 
                    (Subject.name.ilike(f"%{query}%"))
                )
            ).all()
            return render_template('search.html', category=category, scores=scores, user=current_user)

    # Default return if no category matches
    return render_template('search.html', category=None, user=current_user)