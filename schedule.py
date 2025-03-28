from sqlalchemy import create_engine
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from flask_apscheduler import APScheduler
from helpers import send_get

from datetime import datetime

"""
The scheduler object from Flask-APScheduler - `APScheduler()` doesn't contain jobstore
functionality, namely the `add_store()` method and `jobstore` parameter inside the `add_job()` method.

Modifications required to `flask_apscheduler/scheduler.py`:

class APScheduler(object):
    def add_store(self, store, alias):
        self._scheduler.add_jobstore(store, alias)

    def add_job(self, id, func, jobstore, **kwargs):
        ...
        job_def["jobstore"] = jobstore
        ...
"""

# TODO: replace with `from database import engine` for connection with deployed DB service
engine = create_engine("mysql+pymysql://root:rescueforce123@localhost/apscheduler?charset=utf8mb4")
data_store = SQLAlchemyJobStore(engine=engine)

def init_scheduler(app):
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.add_store(store=data_store, alias="mysql_jobstore")
    scheduler.start()
    
    if not scheduler.get_job("send_GET"):
        scheduler.add_job(id="send_GET", func=send_get, jobstore="mysql_jobstore", trigger="interval", seconds=600)  # render.com inactivity prevention

    return scheduler


def add_schedule_message(scheduler, msg, msg_from, msg_to, date):
    kwargs = {
        "msg": msg,
        "msg_from": msg_from,
        "msg_to": msg_to
    }
    
    job_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    # NOTE: if debug=True the server restarts multiple times, so the add_job() errors due to `ConflictingIdError`
    scheduler.add_job(
        id=job_id, 
        func=send_scheduled_msg, 
        jobstore="mysql_jobstore", 
        next_run_time=date, 
        kwargs=kwargs
    )


def send_scheduled_msg(msg, msg_from, msg_to):
    print(f"{msg_from}: @{msg_to} {msg}")
