import MySQLdb
import MySQLdb.cursors
from flask import current_app


def get_db():
    cfg = current_app.config
    return MySQLdb.connect(
        host=cfg['DB_HOST'],
        user=cfg['DB_USER'],
        passwd=cfg['DB_PASSWORD'],
        db=cfg['DB_NAME'],
        charset='utf8mb4',
    )


def dict_cursor(conn):
    return conn.cursor(MySQLdb.cursors.DictCursor)
