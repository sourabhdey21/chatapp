import time
import os
import MySQLdb

MYSQL_HOST = os.getenv('MYSQL_HOST', 'db')
MYSQL_USER = os.getenv('MYSQL_USER', 'chat_user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'chat_password')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'chat_db')

while True:
    try:
        conn = MySQLdb.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
            db=MYSQL_DATABASE
        )
        conn.close()
        print('Database is ready!')
        break
    except Exception as e:
        print('Waiting for database to be ready...')
        time.sleep(2) 