import re
import xml.etree.ElementTree as ET
from typing import Dict, List
import sqlite3
from pathlib import Path

def extract_infobox_data(text: str) -> Dict[str, str]:
    """
    Extracts data from the Infobox of the article text.
    """
    infobox_pattern = r'\{\{Infobox person(.*?)\n\}\}'
    match = re.search(infobox_pattern, text, re.DOTALL)
    if not match:
        return {}
    
    infobox_content = match.group(1)
    attributes = {
        "name": r"\|\s*name\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "birth_name": r"\|\s*birth_name\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "birth_date": r"\|\s*birth_date\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "birth_place": r"\|\s*birth_place\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "occupation": r"\|\s*occupation\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "years_active": r"\|\s*years_active\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "works": r"\|\s*works\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "spouse": r"\|\s*spouse\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "children": r"\|\s*children\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "relatives": r"\|\s*relatives\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "awards": r"\|\s*awards\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "website": r"\|\s*website\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
    }

    data = {}
    for key, pattern in attributes.items():
        attr_match = re.search(pattern, infobox_content)
        if attr_match:
            data[key] = attr_match.group(1).strip()

    # Handle additional modules (e.g., musical artist)
    module_match = re.search(r'\|\s*module\s*=\s*\{\{Infobox musical artist.*?\|(.*)', text, re.DOTALL)
    if module_match:
        module_content = module_match.group(1)
        module_attributes = {
            "genre": r"\|\s*genre\s*=\s*(.*)",
            "instrument": r"\|\s*instrument\s*=\s*(.*)",
            "label": r"\|\s*label\s*=\s*(.*)",
        }
        for key, pattern in module_attributes.items():
            module_attr_match = re.search(pattern, module_content)
            if module_attr_match:
                data[key] = module_attr_match.group(1).strip()

    return data


def parse_dump(dump_path: str) -> List[Dict[str, str]]:
    """
    Parses the XML dump and extracts relevant information.
    """
    extracted_data = []
    for event, elem in ET.iterparse(dump_path, events=("start", "end")):
        if event == "end" and elem.tag.endswith("page"):
            title = elem.find("./{*}title").text
            revision = elem.find("./{*}revision/{*}text")
            text = revision.text if revision is not None else ""
            if not text:
                continue
            
            infobox_data = extract_infobox_data(text)
            if infobox_data:
                # Add person_id
                infobox_data["person_id"] = title
                extracted_data.append(infobox_data)
            
            elem.clear()
    return extracted_data

def save_to_database(db_path: str, data: List[Dict[str, str]]):
    """
    Saves the extracted data into the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for entry in data:
        # Insert into celebrities table
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

        # Insert into occupations table
        for occupation in entry.get("occupation", "").split("|"):
            cursor.execute("""
                INSERT INTO occupations (person_id, occupation) VALUES (?, ?)
            """, (entry["person_id"], occupation.strip()))

        # Insert into relationships table
        for relation_type, related_names in entry.get("relationships", {}).items():
            for related_name in related_names:
                cursor.execute("""
                    INSERT INTO relationships (person_id, relation_type, related_name) VALUES (?, ?, ?)
                """, (entry["person_id"], relation_type, related_name.strip()))

        # Insert into works table
        for work in entry.get("works", "").split("|"):
            cursor.execute("""
                INSERT INTO works (person_id, work_type, work_title) VALUES (?, ?, ?)
            """, (entry["person_id"], "general", work.strip()))

        # Insert into background table (genres, instruments, labels)
        for field, values in entry.get("background", {}).items():
            for value in values:
                cursor.execute("""
                    INSERT INTO background (person_id, field, value) VALUES (?, ?, ?)
                """, (entry["person_id"], field, value.strip()))

        # Insert into awards table
        for award in entry.get("awards", "").split("|"):
            cursor.execute("""
                INSERT INTO awards (person_id, award) VALUES (?, ?)
            """, (entry["person_id"], award.strip()))

    conn.commit()
    conn.close()

def process_dump(dump_path: str, db_path: str):
    """
    Main function to process the dump and extract data.
    """
    data = parse_dump(dump_path)
    print(f"Extracted {len(data)} entries.")
    # Save or process the data (e.g., save to database)
    save_to_database(db_path, data)


if __name__ == "__main__":
    wikipedia_dump_path = Path(r"C:\Users\afafs\AppData\Local\Temp\Rar$DIa8764.21523\enwiki-latest-pages-articles-multistream.xml")
    db_path = "celebrities.db"
    process_dump(wikipedia_dump_path, db_path)