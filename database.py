import os
from sqlalchemy import create_engine, text

# Creating engine

## Using a local MySQL connection
# username = "root"
# password = str(os.environ["DB_PASSWORD"])
# host = "127.0.0.1"
# dbname = "chatter"
# option = "charset=utf8mb4"

# connection_string = f"mysql+pymysql://{username}:{password}@{host}/{dbname}?{option}"

# SQLAlchemy + PyMySQL Connection from TiDB 
password = str(os.environ["DB_PASSWORD"])
CA_PATH = r"/etc/secrets/isrgrootx1.pem"
connection_string = f"mysql+pymysql://39HVxerRsFMaxdU.root:{password}@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/chatify?ssl_ca={CA_PATH}&ssl_verify_cert=true&ssl_verify_identity=true"


engine = create_engine(connection_string)

def execute(query, parameters = None):
    """In case of error during query execution, nothing is happened."""
    
    with engine.connect() as conn:
        
        try:
            conn.execute(text(query), parameters or {})
            conn.commit()
        except Exception as error:
            print("Some error occurred during SQL execution:", error)


def execute_retrieve(query, parameters = None):
    """Returns a list of dicts with keys as the attribute name of the table
    Converts list of <class sqlalchemy.engine.row.Row> objects to list of dicts
    
    In case or error during query execution, returns an Empty List.
    """
    
    with engine.connect() as conn:

        rows = []
        
        try:
            result = conn.execute(text(query), parameters or {})
            fetched = result.all() #list of row objects
            keys = result.keys()
            rows = [dict(zip(keys, row_object)) for row_object in fetched]
        except Exception as error:
            print("Some error occured during SQL execution and retrieval:", error)
    
    return rows