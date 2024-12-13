import sqlite3

db_path = 'celebrities.db'

def create_tables(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the celebrities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS celebrities (
        person_id TEXT PRIMARY KEY,
        name TEXT,
        birth_name TEXT,
        birth_date TEXT,
        birth_place TEXT,
        website TEXT
    )
    """)

    # Create the occupations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS occupations (
        person_id TEXT,
        occupation TEXT,
        FOREIGN KEY(person_id) REFERENCES celebrities(person_id)
    )
    """)

    # Create the relationships table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relationships (
        person_id TEXT,
        relation_type TEXT,
        related_name TEXT,
        FOREIGN KEY(person_id) REFERENCES celebrities(person_id)
    )
    """)

    # Create the works table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS works (
        person_id TEXT,
        work_type TEXT,
        work_title TEXT,
        FOREIGN KEY(person_id) REFERENCES celebrities(person_id)
    )
    """)

    # Create the background table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS background (
        person_id TEXT,
        field TEXT,
        value TEXT,
        FOREIGN KEY(person_id) REFERENCES celebrities(person_id)
    )
    """)

    # Create the awards table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS awards (
        person_id TEXT,
        award TEXT,
        FOREIGN KEY(person_id) REFERENCES celebrities(person_id)
    )
    """)

    # Commit changes and close the connection
    conn.commit()
    conn.close()

# Call the create_tables function before saving data
create_tables(db_path)