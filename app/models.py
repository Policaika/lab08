import os
import mysql.connector

class Database:
    def __init__(self):
        self.params = {
            'host': os.getenv('DB_HOST', 'database'),
            'port': 3306,
            'user': os.getenv('DB_USER', 'admin'),
            'password': os.getenv('DB_PASSWORD', 'secret'),
            'database': os.getenv('DB_NAME', 'library'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_general_ci'
        }

    def fetch_books(self):
        try:
            connection = mysql.connector.connect(**self.params)
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT title, author FROM books ORDER BY id')
            result = cursor.fetchall()
            cursor.close()
            connection.close()
            return result
        except mysql.connector.Error as err:
            print(f"DB error: {err}")
            return []
