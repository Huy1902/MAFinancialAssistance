
class DBAgent:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None

    def connect(self):
        # Logic to establish a database connection
        pass

    def close(self):
        # Logic to close the database connection
        pass

    def execute_query(self, query):
        # Logic to execute a database query
        pass

    def fetch_results(self):
        # Logic to fetch results from the executed query
        pass

import psycopg2

conn = psycopg2.connect(
        dbname="finance-tracker",
        user="postgres",
        password="123",
        host="localhost",
        port="5432"
    )
cursor = conn.cursor()