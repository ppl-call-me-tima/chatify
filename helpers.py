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
    timestamp = datetime.now(tz=IST).strftime(r"%Y%m%d%H%M")
    execute("UPDATE user SET lastOnline = :timestamp WHERE id = :id", {"timestamp": timestamp, "id": user_id})


def new_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "new_user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def send_get():
    requests.get("https://chatify-i0dd.onrender.com/")


def time_difference(time1, time2):
    if not time1 or not time2:
        return ""
    
    Y1, Y2 = map(int, [time1[:4], time2[:4]])
    m1, m2 = map(int, [time1[4:6], time2[4:6]])
    d1, d2 = map(int, [time1[6:8], time2[6:8]])
    H1, H2 = map(int, [time1[8:10], time2[8:10]])
    M1, M2 = map(int, [time1[10:12], time2[10:12]])
    
    t1 = (Y1 * 365 * 24 * 60) + (m1 * 30 * 24 * 60) + (d1 * 24 * 60) + (H1 * 60) + M1
    t2 = (Y2 * 365 * 24 * 60) + (m2 * 30 * 24 * 60) + (d2 * 24 * 60) + (H2 * 60) + M2
    
    delta = t2 - t1
    time_difference_string = ""
    
    minutes_in_year = 355 * 24 * 60
    minutes_in_month = 30 * 24 * 60
    minutes_in_day = 24 * 60
    
    if delta >= minutes_in_year:
        time_difference_string += f"{delta // minutes_in_year} Year" + ("s" if delta // minutes_in_year > 1 else "") + " "
    delta %= minutes_in_year
    
    if delta >= minutes_in_month:
        time_difference_string += f"{delta // minutes_in_month} Month" + ("s" if delta // minutes_in_month > 1 else "") + " "
    delta %= minutes_in_month
    
    if delta >= minutes_in_day:
        time_difference_string += f"{delta // minutes_in_day} Day" + ("s" if delta // minutes_in_day > 1 else "") + " "
    delta %= minutes_in_day
    
    if delta >= 60:
        time_difference_string += f"{delta // 60} Hour" + ("s" if delta // 60 > 1 else "") + " "
    delta %= 60
    
    if delta >= 0:
        time_difference_string += f"{delta} Minute" + ("s" if delta > 1 else "") + " "         
    
    return time_difference_string
    

def url_for_pfp(filename):
    return f"https://{environ['AWS_BUCKET_NAME']}.s3.us-east-1.amazonaws.com/{filename}"

def user_count():
    return execute_retrieve("SELECT COUNT(*) AS count FROM user")[0]["count"]