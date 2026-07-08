import psycopg2
import psycopg2.extras
import os
import time

DATABASE_URL = os.environ.get("DATABASE_URL")

print("Attempting to connect to PostgreSQL...")
start = time.time()

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor, connect_timeout=10)
    elapsed = time.time() - start
    print(f"Connected successfully in {elapsed:.2f} seconds")

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    result = cursor.fetchone()
    print(f"PostgreSQL version: {result['version']}")

    cursor.close()
    conn.close()
    print("Connection closed cleanly. Everything works.")

except Exception as e:
    elapsed = time.time() - start
    print(f"Connection failed after {elapsed:.2f} seconds")
    print(f"Error: {e}")
