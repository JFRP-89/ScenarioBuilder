import psycopg2
from sqlalchemy import create_engine, text

c = psycopg2.connect(
    host="localhost",
    port=5434,
    user="postgres",
    password="postgres",
    dbname="postgres",
    client_encoding="utf8",
)
cur = c.cursor()

# Check databases
cur.execute("SELECT datname, pg_encoding_to_char(encoding) FROM pg_database WHERE datname LIKE 'scenario%%'")
print("Databases:", cur.fetchall())

# Check lc_messages
cur.execute("SHOW lc_messages")
print("lc_messages:", cur.fetchone())
c.close()

# Ensure scenario_test exists
c2 = psycopg2.connect(
    host="localhost",
    port=5434,
    user="postgres",
    password="postgres",
    dbname="postgres",
    client_encoding="utf8",
)
c2.autocommit = True
cur2 = c2.cursor()
cur2.execute("SELECT 1 FROM pg_database WHERE datname = 'scenario_test'")
if not cur2.fetchone():
    cur2.execute("CREATE DATABASE scenario_test ENCODING 'UTF8'")
    print("Created scenario_test")
c2.close()

# Try direct psycopg2 to scenario_test
print("\nDirect psycopg2 to scenario_test...")
try:
    c3 = psycopg2.connect(
        host="localhost",
        port=5434,
        user="postgres",
        password="postgres",
        dbname="scenario_test",
        client_encoding="utf8",
    )
    print("OK via psycopg2 direct")
    c3.close()
except Exception as ex:
    print(f"FAILED: {type(ex).__name__}: {ex}")

# Try direct psycopg2 DSN to scenario_test
print("\nDirect psycopg2 DSN to scenario_test...")
try:
    c4 = psycopg2.connect("postgresql://postgres:postgres@localhost:5434/scenario_test?client_encoding=utf8")
    print("OK via psycopg2 DSN")
    c4.close()
except Exception as ex:
    print(f"FAILED: {type(ex).__name__}: {ex}")

# Try SQLAlchemy to scenario_test
print("\nSQLAlchemy to scenario_test...")
try:
    e = create_engine("postgresql://postgres:postgres@localhost:5434/scenario_test?client_encoding=utf8")
    conn = e.connect()
    print("Connected! SELECT 1 =", conn.execute(text("SELECT 1")).scalar())
    conn.close()
    e.dispose()
except Exception as ex:
    print(f"FAILED: {type(ex).__name__}: {ex}")

# Try SQLAlchemy with creator
print("\nSQLAlchemy with creator...")
try:
    def get_conn():
        return psycopg2.connect(
            host="localhost",
            port=5434,
            user="postgres",
            password="postgres",
            dbname="scenario_test",
            client_encoding="utf8",
        )
    e2 = create_engine("postgresql://", creator=get_conn)
    conn2 = e2.connect()
    print("Connected via creator! SELECT 1 =", conn2.execute(text("SELECT 1")).scalar())
    conn2.close()
    e2.dispose()
except Exception as ex:
    print(f"FAILED: {type(ex).__name__}: {ex}")
