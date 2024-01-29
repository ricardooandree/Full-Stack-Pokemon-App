import os

#from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

# Application configuration
app = Flask(__name__)


# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'site.db')
db = SQLAlchemy(app)


# Define user class-model (table)
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods = ["GET", "POST"])
def login():
    """Log user in"""
    
    # Forget any user_id
    session.clear()
    
    # User reached route via POST
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Input validation
        if not username:
            flash("Username is empty", "error")
            return render_template("homepage.html")
        
        elif not password:
            flash("Password is empty", "error")
            return render_template("homepage.html")
        
        # Query database for user
        existing_user = Users.query.filter_by(username=username).first()
        
        # Ensure username exists and password is correct
        if not existing_user:
            flash("User doesn't exist", "error")
            return render_template("homepage.html")
        
        if not check_password_hash(existing_user.password, password):
            flash("Incorrect password", "error")
            return render_template("homepage.html")
        
        # Remember which user has logged in
        session["user_id"] = existing_user.id
        
        # Redirect user to home page
        flash("User has logged in", "success")
        return redirect("/")
    
    # User reacher route via GET
    else:
        return render_template("homepage.html")


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()
    
    return redirect("/")


@app.route("/register", methods = ["GET", "POST"])
def register():
    """Register a new user"""
    
    # User reached route via POST
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Input validation
        if not username:
            flash("Username is empty", "error")
            return render_template("register.html")
        
        elif not password:
            flash("Password is empty", "error")
            return render_template("register.html")
        
        elif not confirmation:
            flash("Password confirmation is empty", "error")
            return render_template("register.html")
        
        elif confirmation != password:
            flash("Passwords do not match", "error")
            return render_template("register.html")
        
        # Ensure username is available 
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            flash("Username is taken", "error")
            return render_template("register.html")
        
        # Insert user into database
        new_user = Users(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user
        session["user_id"] = new_user.id
        
        # Redirect user to home page 
        flash("Registration successful", "success")
        return redirect("/")
    
    # User reacher route via GET
    else:
        return render_template("register.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/profile", methods = ["GET", "POST"])
@login_required
def profile():
    return render_template("profile.html")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables before running the app
    app.run(debug=True)