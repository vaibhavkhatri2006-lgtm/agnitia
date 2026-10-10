import psycopg2
from app.config import settings

conn = psycopg2.connect(settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"))
cur = conn.cursor()
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'users'")
print("Users table locations:", cur.fetchall())

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
print("Public tables:", [r[0] for r in cur.fetchall()])

cur.execute("SHOW search_path")
print("Search path:", cur.fetchone())

conn.close()
