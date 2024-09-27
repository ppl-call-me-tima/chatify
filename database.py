from sqlalchemy import create_engine, exc,text


def execute(query):
    conn.execute(text(query))
    conn.commit()


def execute_retrieve(query):
    """Returns a list of dicts with keys as the attribute name of the table
    
    Converts list of <class sqlalchemy.engine.row.Row> objects to list of dicts
    """
    
    result = conn.execute(text(query))
    fetched = result.all() #list of row objects
    keys = result.keys()
    rows = [dict(zip(keys, row_object)) for row_object in fetched]
    
    return rows


username = "root"
password = "rescueforce"
host = "127.0.0.1"
dbname = "chatter"
option = "charset=utf8mb4"

connect_string = f"mysql+pymysql://{username}:{password}@{host}/{dbname}?{option}"
engine = create_engine(connect_string)

with engine.connect() as conn: 
    pass