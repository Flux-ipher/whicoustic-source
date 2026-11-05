import sqlite3
import json

db_path = "vcaas_dev2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

db_stats = {}
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    cursor.execute(f"PRAGMA table_info({table})")
    schema = [{"cid": row[0], "name": row[1], "type": row[2], "notnull": row[3], "dflt_value": row[4], "pk": row[5]} for row in cursor.fetchall()]
    db_stats[table] = {"row_count": count, "schema": schema}

print(json.dumps(db_stats, indent=2))
conn.close()
