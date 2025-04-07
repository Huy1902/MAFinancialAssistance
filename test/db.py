import psycopg2

conn = psycopg2.connect(
   dbname="finance-tracker",
   user="postgres",
   password="123",
   host="localhost",
   port="5432"
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM transaction")
result = cursor.fetchall()
print(result)
