import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Creating engine
# username = "root"
# password = "rescueforce"
# host = "127.0.0.1"
# dbname = "chatter"
# option = "charset=utf8mb4"

# connect_string = f"mysql+pymysql://{username}:{password}@{host}/{dbname}?{option}"

# SQLAlchemy + PyMySQL Connection from TiDB 
load_dotenv()
password = str(os.getenv("password"))
CA_PATH = r"/etc/secrets/isrgrootx1.pem"

connect_string = f"mysql+pymysql://39HVxerRsFMaxdU.root:{password}@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/chatify?ssl_ca={CA_PATH}&ssl_verify_cert=true&ssl_verify_identity=true"

engine = create_engine(connect_string)


# Funtions to execute SQL queries from app.py
def execute(query, parameters = None):
    with engine.connect() as conn:
        conn.execute(text(query), parameters or {})
        conn.commit()


def execute_retrieve(query, parameters = None):
    """Returns a list of dicts with keys as the attribute name of the table
    
    Converts list of <class sqlalchemy.engine.row.Row> objects to list of dicts
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query), parameters or {})
        fetched = result.all() #list of row objects
        keys = result.keys()
        rows = [dict(zip(keys, row_object)) for row_object in fetched]
    
    return rows