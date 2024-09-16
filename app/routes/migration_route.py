import os
import sqlite3
from flask import jsonify, request, send_file
from app import app, db


# Assuming you're using SQLite for this example

@app.route("/api/export_sql", methods=["GET"])
def export_sql():
  try:
    # Path to your SQLite database file
    db_path = os.path.join(app.root_path, "your_database.db")  # Adjust the path
    # Export the database to an SQL dump file
    sql_dump_path = os.path.join(app.root_path, "database_dump.sql")

    # Use sqlite3 to dump the entire database to a SQL file
    con = sqlite3.connect(db_path)
    with open(sql_dump_path, 'w') as f:
      for line in con.iterdump():
        f.write('%s\n' % line)
    con.close()

    # Send the SQL file as a downloadable response
    return send_file(sql_dump_path, as_attachment=True, download_name="database_dump.sql")

  except Exception as e:
    return jsonify({"error": str(e)}), 500
