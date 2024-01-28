import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import datetime
from functools import wraps

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods = ["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/logout")
def logout():
    return redirect("/")


@app.route("/register", methods = ["GET", "POST"])
def register():
    return render_template("register.html")


@app.route("/profile", methods = ["GET", "POST"])
@login_required
def profile():
    return render_template("profile.html")


if __name__ == '__main__':
    app.run(debug=True)