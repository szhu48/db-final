import re
import xml.etree.ElementTree as ET
import sqlite3
from typing import Dict, List

def clean_text(text: str) -> str:
    if not text:
        return None
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)  # Extract text within brackets
    text = re.sub(r'<ref.*?>.*?</ref>', '', text)  # Remove inline references
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'&[a-z]+;', '', text)  # Remove HTML entities
    text = re.sub(r'[|]', ', ', text)  # Replace pipe with comma
    return text.strip()

def clean_birth_date(raw_date):
    if not raw_date:
        return None

    match = re.search(r'\{\{(?:birth date(?: and age)?|Birth date(?: and age)?)\D*(\d{4})[|-](\d{1,2})[|-](\d{1,2})', raw_date, re.IGNORECASE)
    if match:
        year, month, day = match.groups()
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"

    match = re.search(r'(\d{1,2})\s([A-Za-z]+)\s(\d{4})', raw_date)
    if match:
        day, month_str, year = match.groups()
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        month = months.get(month_str.lower())
        if month:
            return f"{year}-{month}-{day.zfill(2)}"

    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', raw_date)
    if match:
        year, month, day = match.groups()
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"

    return None

def extract_infobox_data(text: str) -> Dict[str, str]:
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
    }

    data = {}
    for key, pattern in attributes.items():
        attr_match = re.search(pattern, infobox_content)
        if attr_match:
            raw_data = attr_match.group(1).strip()

            # Specific cleaning for `birth_name`
            if key == "birth_name":
                raw_data = re.sub(r'\{\{nowrap, *(.*?)\}\}', r'\1', raw_data)  # Handle nowrap
                raw_data = re.sub(r',?\s*birth_date\s*=\s*.*', '', raw_data)  # Remove unrelated text
                data[key] = clean_text(raw_data)
            elif key == "birth_date":
                data[key] = clean_birth_date(raw_data)
            else:
                data[key] = clean_text(raw_data)
        else:
            data[key] = None  # Ensure missing fields are explicitly set to None

    return data

def parse_dump(dump_path: str) -> List[Dict[str, str]]:
    """
    Parses the XML dump and extracts relevant information.
    """
    extracted_data = []
    for event, elem in ET.iterparse(dump_path, events=("start", "end")):
        if event == "end" and elem.tag.endswith("page"):
            title = elem.find("./{*}title").text  # Unique Wikipedia title
            revision = elem.find("./{*}revision/{*}text")
            text = revision.text if revision is not None else ""
            if not text:
                continue
            
            infobox_data = extract_infobox_data(text)
            if infobox_data:
                # Add person_id from the unique Wikipedia title
                infobox_data["person_id"] = title
                infobox_data["name"] = infobox_data.get("name") or title
                extracted_data.append(infobox_data)
            # Clean birth_date field
            infobox_data["birth_date"] = clean_birth_date(infobox_data.get("birth_date"))
                
            # Release memory for processed elements
            elem.clear()
    return extracted_data

def save_to_database(db_path: str, data: List[Dict[str, str]]):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for entry in data:
        # Insert into celebrities table
        cursor.execute(""" 
            INSERT OR REPLACE INTO celebrities (
                person_id, name, birth_name, birth_date, birth_place
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            entry.get("person_id"),
            entry.get("name"),
            entry.get("birth_name"),
            entry.get("birth_date"),
            entry.get("birth_place"),
        ))

    conn.commit()
    conn.close()

def process_dump(dump_path: str, db_path: str):
    """
    Processes the Wikipedia dump file and updates the database with extracted data.
    
    Parameters:
    - dump_path: Path to the Wikipedia XML dump file.
    - db_path: Path to the SQLite database file.
    """
    # Step 1: Parse the dump file
    print("Parsing dump file...")
    data = parse_dump(dump_path)
    print(f"Extracted {len(data)} records from the dump file.")

    # Step 2: Save the parsed data to the database
    print("Saving data to the database...")
    save_to_database(db_path, data)
    print("Database update complete.")

if __name__ == "__main__":
    wikipedia_dump_path = "C:/Users/afafs/Documents/simplewiki-20240801-pages-articles-multistream.xml"
    db_path = "celebrities.db"
    process_dump(wikipedia_dump_path, db_path)