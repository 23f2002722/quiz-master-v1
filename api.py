from flask_restful import Resource, Api
from app import app

from models import User, Subject, Chapter, Quiz

api = Api(app)

class UserResource(Resource):
    def get(self):
        users = User.query.all()
        return {
            "Users": [
                {
                    "Username (email)": user.username,
                    "Name": user.full_name,
                    "DOB" : user.dob.isoformat(),
                    "Role": user.role,
                    "Qualification" : user.qualification,
                }
                for user in users
            ]
        }
api.add_resource(UserResource, "/api/user")

class SubjectResource(Resource):
    def get(self):
        subjects = Subject.query.all()
        return {
            "Subjects": [
                {
                    "Subject name": subject.name,
                    "Description": subject.description,
                }
                for subject in subjects
            ]
        }
api.add_resource(SubjectResource, "/api/subject")

class ChapterResource(Resource):
    def get(self):
        chapters = Chapter.query.all()
        return {
            "Chapters": [
                {
                    "Chapter name": chapter.name,
                    "Description": chapter.description,
                    "Subject name": chapter.subject.name,
                }
                for chapter in chapters
            ]
        }
api.add_resource(ChapterResource, "/api/chapter")

class QuizResource(Resource):
    def get(self):
        quizzes = Quiz.query.all()
        return {
            "Quizzes": [
                {
                    "Quiz name": quiz.type,
                    "Chapter name": quiz.chapter.name,
                    "Subject name": quiz.chapter.subject.name,
                    "Quiz duration": f"{quiz.time_duration} minutes",   
                    "Date of quiz" : quiz.date_of_quiz.strftime('%d-%m-%Y'),
                    "Remarks": quiz.remarks,
                    "Quiz questions": [
                        {
                            "Question text": question.question_statement,
                        }
                        for question in quiz.questions
                    ]
                }
                for quiz in quizzes
            ]
            }
api.add_resource(QuizResource, "/api/quiz")