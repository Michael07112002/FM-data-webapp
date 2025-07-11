
# Import libraries
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import data_functions
import pandas as pd 
import sqlite3

# Configure Application 
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False 
app.config["SESSION_TYPE"] = "filesystem"
Session(app) 

# Connect to SQLite database and create the tables for it 
db = SQL("sqlite:///FM.db") 

# Create users table 

db.execute("""CREATE TABLE IF NOT EXISTS users (
           user_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
           username TEXT NOT NULL, 
           hash TEXT NOT NULL
           )
           """)


@app.after_request
def after_request(response): 
    """Ensure repsonses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must revalidate"
    response.headers["Expires"] = 0 
    response.headers["Progma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("homepage.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""
    if request.method == "POST": 
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirmation = request.form.get("password_confirmation")

        # Validate user input 
        if username and password and password_confirmation: 

            # Check username is unique
            check = db.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = ?) AS taken", username)
            if check[0]["taken"] == 1: 
                return redirect("/register") # Find way to also let user know the username is taken 
            
            # Check password and confirmation match 
            if password == password_confirmation: 
                
                # Add user details to db 
                db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

                # Remember the user has logged in
                session["user_id"] = db.execute("SELECT user_id FROM users WHERE username = ?", username)

                # Redirect to homepage
                return redirect("/")
            
            # User's password and confirmation do not match 
            return redirect("/register") # Find way to let user know reason why 
        
        # User has failed to input fully 
        return redirect("/register") # Find way to let user know reason why 
    
    # Request method is GET so allow user to enter page 
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login(): 
    """Log user in"""

    # Forget any user_id 
    session.clear()

    # User reached route via POST 
    if request.method == "POST": 

        print("POST request received")

        # Ensure username and password was submitted 
        if not request.form.get("username"): 
            return redirect("/login") # Find way to let user know why 
        if not request.form.get("password"): 
            return redirect("/login") 
        
        # Query DB for username 
        row = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exist and password is correct 
        if len(row) != 1 or not check_password_hash(row[0]["hash"], request.form.get("password")): 
            return redirect("/login") # Find way to let user know why 

        # Remember which user has logged in 
        session["user_id"] = row[0]["user_id"]

        # Redirect user to homepage 
        return redirect("/")
    
    # If request is GET allow user to access page
    return render_template("login.html")
    

@app.route("/logout") 
def logout(): 
    """Log user out"""

    # Forget user id 
    session.clear() 

    # Redirect user to login form 
    return redirect("/") 


@app.route("/create", methods=["GET", "POST"])
@login_required
def create(): 
    if request.method == "POST":
        # Take the csv files from the form submitted by the user
        players_csv = request.files["players_csv"]
        possession_csv = request.files["possession_csv"]

        # Put the files in to dataframe and then clean and manipulate data within so it is ready to be used
        df = data_functions.csv_file_cleaner_and_manipulator(players_csv, possession_csv)

        # Add the data frame to the database and create user_id column to identify whose data is whose
        df["user_id"] = session["user_id"]
        conn = sqlite3.connect("FM.db")
        df.to_sql("fm_data", conn, if_exists="replace", index=False)

        return redirect("/player_search")

    return render_template("create_data_set.html")

@app.route("/player_search", methods=["GET", "POST"])
@login_required 
def player_search():
    if request.method == "POST": 
        conn = sqlite3.connect("FM.db")
        df = pd.read_sql("SELECT * FROM fm_data", conn)

        uid = request.form.get("uid")
        wage_input = request.form.get("wage")
        wage = int(wage_input) if wage_input else None

        transfer_value_input = request.form.get("transfer_value")
        transfer_value = int(transfer_value_input) if transfer_value_input else None

        age_input = request.form.get("age")
        age = int(age_input) if age_input else None

        matches_input = request.form.get("matches")
        matches = int(matches_input) if matches_input else None

        percentage_input = request.form.get("percentage") 
        percentage = int(percentage_input) if percentage_input else None

        df = data_functions.player_search(uid, df, wage, transfer_value, age, matches, percentage)
        html_table = df.to_html(classes="table table-striped", index=False)

        return render_template("player_search_results.html", table=html_table)
    
    return render_template("player_search.html")



