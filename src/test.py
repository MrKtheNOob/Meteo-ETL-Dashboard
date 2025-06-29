import os
from dotenv import load_dotenv
import pymysql
from pymysql.connections import Connection
from pymysql import cursors

load_dotenv()

def connect_mysql() -> Connection:
    timeout = 10
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=cursors.DictCursor,
        db=os.getenv("DB_NAME", ""),
        host=os.getenv("HOST", ""),
        password=os.getenv("PASSWORD", ""),
        read_timeout=timeout,
        port=int(os.getenv("PORT", "")),
        user=os.getenv("DB_USER", ""),
        write_timeout=timeout,
    )
    return connection



mysql_conn: Connection = connect_mysql()
