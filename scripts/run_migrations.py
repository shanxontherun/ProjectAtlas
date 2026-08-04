"""
Atlas Migration Runner

Executes every SQL migration in the sql/ directory
in filename order.
"""

from pathlib import Path
import sqlite3

DATABASE = Path("database/atlas.db")
SQL_DIR = Path("sql")

conn = sqlite3.connect(DATABASE)

for migration in sorted(SQL_DIR.glob("*.sql")):
    print(f"Applying {migration.name}...")

    sql = migration.read_text(encoding="utf-8")
    conn.executescript(sql)

conn.commit()
conn.close()

print("\n✅ All migrations completed successfully!")