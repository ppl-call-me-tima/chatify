from functools import wraps
from flask import flash, redirect, session, url_for
from os import environ
from datetime import datetime
from pytz import timezone

from database import execute, execute_retrieve

import requests  # render.com inactivity prevention

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MY_ID = 60001
DEFAULT_MESSAGE = "Hello, welcome to Chatify! This is an automatic message, and all messages after this will be real time - with me! Leave a message and I'll respond as soon as I can. Explore around, hope you like the site :)."
IST = timezone("Asia/Kolkata")

def add_friend_automatically(rows):
    timestamp = datetime.now(tz=IST).strftime(r"%Y%m%d%H%M%S%f")
        
    low, high = sorted([rows[0]["id"], MY_ID])
    execute("INSERT INTO friendships (low_friend_id, high_friend_id) VALUES (:low, :high)", {"low": low, "high": high})
    execute("""
        INSERT INTO messages (
            msg_from, 
            msg_to, 
            msg, 
            timestamp
        ) VALUES (
            :MY_ID, 
            :id, 
            :msg, 
            :timestamp)
    """, {
        "MY_ID": MY_ID, 
        "id": session.get("user_id"), 
        "msg": DEFAULT_MESSAGE,
        "timestamp": timestamp
    })


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def flash_and_redirect(msg: str, func: str, **kwargs):
    flash(msg)
    return redirect(url_for(func, **kwargs))


def is_profane(msg, profanity):
    msg_words = msg.lower().split()
    
    for word in msg_words:
        if word in profanity:
            return True
    
    return False


def is_profanity_enabled():
    return bool(execute_retrieve("SELECT isProfanityEnabled FROM user WHERE id = :id", {"id": session.get("user_id")})[0]["isProfanityEnabled"])


def load_profanity_checking():
    rows = execute_retrieve("SELECT word FROM profanity")
    words = set()
    
    for row in rows:
        words.add(row["word"])
    
    return words


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def log_user_in(user_id: int, username: str):
    session.permanent = True  # For making a session permanent - so that it exists even after the browser is closed
    session["user_id"] = user_id
    session["username"] = username


def new_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "new_user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def send_get():
    requests.get("https://chatify-i0dd.onrender.com/")


def url_for_pfp(filename):
    return f"https://{environ['AWS_BUCKET_NAME']}.s3.us-east-1.amazonaws.com/{filename}"

def user_count():
    return execute_retrieve("SELECT COUNT(*) AS count FROM user")[0]["count"]