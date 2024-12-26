from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *

@app.route("/")
def index():
    return render_template("index.html")