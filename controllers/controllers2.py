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
             return render_template("admin.html",user=user,subject=subject)
        
@app.route("/dashboard/add_subject", methods=["GET", "POST"])
@auth_required
def add_subject():
        user = User.query.get(session["user_id"])
        if request.method=="POST":
             name = request.form["name"]
             description = request.form["description"]
             subject = Subject(name=name,description=description)
             db.session.add(subject)
             db.session.commit()
             return redirect(url_for("dashboard"))
             
        else:
             return render_template("add_subject.html",user=user)
        
@app.route("/dashboard/admin/delete_subject/<int:subject_id>", methods=["POST"])
@auth_required
def delete_subject(subject_id):
    sub = Subject.query.filter_by(id=subject_id).first()
    db.session.delete(sub)
    db.session.commit()
    return redirect(url_for("dashboard"))
   