from app import app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

from werkzeug.security import generate_password_hash
from datetime import date, datetime, timezone

db=SQLAlchemy(app)
migrate = Migrate(app, db)

# Users Table - Stores user data
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    dob = db.Column(db.Date)
    role = db.Column(db.Enum("user", "admin", name="user_roles"), default="user",)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    scores = db.relationship('Score', backref='user', lazy=True, cascade="all, delete-orphan")


# Quizzes Table - Stores quiz data
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type=db.Column(db.String(50))
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_duration = db.Column(db.Integer)  # format: HH:MM
    remarks = db.Column(db.String(255))

    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    scores = db.relationship('Score', backref='quiz', lazy=True, cascade="all, delete-orphan")


# Chapters Table - Stores chapter data
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))

    quizzes = db.relationship('Quiz', backref='chapter', lazy=True, cascade="all, delete-orphan")


# Subjects Table - Stores subject data
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))

    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")


# Questions Table - Stores quiz questions
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.String(255), nullable=False, unique=True)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    option4 = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String(100), nullable=False)


# Scores Table - Stores user's quiz attempt results
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_score = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint('quiz_id', 'user_id', name='unique_user_quiz_attempt'),)



with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        password_hash = generate_password_hash("987")
        admin = User(
            username="admin@gmail.com",
            full_name="admin",
            qualification="Graduation",
            dob=date(2004,12,16),
            password_hash=password_hash,
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()