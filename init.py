import sqlite3
from temp import process_dump

db_path = 'celebrities.db'

def save_normalized_data(db_path: str, data: list):
    """
    Saves the extracted data into the normalized SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for entry in data:
        # Insert into celebrities table (only insert if person_id is not already in the table)
        cursor.execute("""
            INSERT OR REPLACE INTO celebrities (
                person_id, name, birth_name, birth_date, birth_place, website
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry.get("person_id"),
            entry.get("name"),
            entry.get("birth_name"),
            entry.get("birth_date"),
            entry.get("birth_place"),
            entry.get("website")
        ))

        # Insert into occupations table (only if occupation exists)
        occupations = entry.get("occupation")
        if occupations:
            for occupation in occupations.split("|"):
                cursor.execute("""
                    INSERT INTO occupations (person_id, occupation) VALUES (?, ?)
                """, (entry["person_id"], occupation.strip()))

        # Insert into relationships table (only if relationships exist)
        relationships = entry.get("relationships", {})
        if relationships:
            for relation_type, related_names in relationships.items():
                for related_name in related_names:
                    cursor.execute("""
                        INSERT INTO relationships (person_id, relation_type, related_name) VALUES (?, ?, ?)
                    """, (entry["person_id"], relation_type, related_name.strip()))

        # Insert into works table (only if works exist)
        works = entry.get("works")
        if works:
            for work in works.split("|"):
                cursor.execute("""
                    INSERT INTO works (person_id, work_type, work_title) VALUES (?, ?, ?)
                """, (entry["person_id"], "general", work.strip()))

        # Insert into background table (only if background fields exist)
        background = entry.get("background", {})
        if background:
            for field, values in background.items():
                for value in values:
                    cursor.execute("""
                        INSERT INTO background (person_id, field, value) VALUES (?, ?, ?)
                    """, (entry["person_id"], field, value.strip()))

        # Insert into awards table (only if awards exist)
        awards = entry.get("awards")
        if awards:
            for award in awards.split("|"):
                cursor.execute("""
                    INSERT INTO awards (person_id, award) VALUES (?, ?)
                """, (entry["person_id"], award.strip()))

    # Commit changes and close connection
    conn.commit()
    conn.close()

def populate_database(): 
    # Extract data from XML dump
    wikipedia_dump_path = "path_to_your_wikipedia_dump.xml"
    extracted_data = process_dump(wikipedia_dump_path)
    
    # Populate the database with the extracted data
    save_normalized_data(db_path, extracted_data)

if __name__ == "__main__":
    populate_database()