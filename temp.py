import re
import xml.etree.ElementTree as ET
from typing import Dict, List
import sqlite3
from pathlib import Path

# Function to clean extracted attributes
def clean_text(text: str) -> str:
    if not text:
        return None
    # Remove Wiki links
    text = re.sub(r'\[\[|\]\]', '', text)
    # Remove nested templates
    text = re.sub(r'\{\{.*?\}\}', '', text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Remove category links
    text = re.sub(r'\[[:][^]]*?[:]\]', '', text)
    # Remove HTML entities (e.g., &nbsp;)
    text = re.sub(r'&[a-z]+;', '', text)
    # Replace pipe with comma
    text = re.sub(r'[|]', ', ', text)
    # Remove special characters except alphanumeric and spaces
    text = re.sub(r'[^a-zA-Z0-9\s,]', '', text)
    return text.strip()

# Extract infobox data from Wiki text
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
        "occupation": r"\|\s*occupation\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "years_active": r"\|\s*years_active\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "works": r"\|\s*works\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "spouse": r"\|\s*spouse\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "children": r"\|\s*children\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "relatives": r"\|\s*relatives\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
        "awards": r"\|\s*awards\s*=\s*(.*?)\s*(?=\n\||\n\}\})",
    }

    data = {}
    for key, pattern in attributes.items():
        attr_match = re.search(pattern, infobox_content)
        if attr_match:
            raw_data = attr_match.group(1).strip()
            if key == "birth_date":
                cleaned_data = re.sub(r"(\d{4})\D*(\d{1,2})\D*(\d{1,2})", r"\1-\2-\3", raw_data)
                #parsed_date = clean_birth_date(raw_data)
                #cleaned_data = clean_text(parsed_date)
            else:
                cleaned_data = clean_text(raw_data)
            data[key] = cleaned_data

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
                data[key] = clean_text(module_attr_match.group(1).strip())

    return data

def clean_birth_date(raw_date):
    if not raw_date:
        return None

    # Regex to match date formats within templates like {{birth date|YYYY|MM|DD}} or {{birth date and age|YYYY-MM-DD}}
    match = re.search(r'\{\{(?:birth date(?: and age)?|Birth date(?: and age)?)[^\d]*(\d{4})[|\-](\d{1,2})[|\-](\d{1,2})', raw_date, re.IGNORECASE)
    if match:
        year, month, day = match.groups()
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"

    # Regex to match plain text dates like "4 May 1929" or "25 February 1943"
    match = re.search(r'(\d{1,2})\s([A-Za-z]+)\s(\d{4})', raw_date)
    if match:
        day, month_str, year = match.groups()
        # Convert month name to number
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        month = months.get(month_str.lower())
        if month:
            return f"{year}-{month}-{day.zfill(2)}"

    # Regex to match ISO-like formats like "YYYY-MM-DD"
    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', raw_date)
    if match:
        year, month, day = match.groups()
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"

    # If no match, return None
    return None


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
    """
    Saves the extracted data into the database.
    """
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

        # Insert into occupations table
        occupations = entry.get("occupation") or ""
        for occupation in occupations.split("|"):
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
        awards = entry.get("awards") or ""
        for award in awards.split("|"):
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
    wikipedia_dump_path = "C:/Users/afafs/Documents/simplewiki-20240801-pages-articles-multistream.xml"
    db_path = "celebrities.db"
    process_dump(wikipedia_dump_path, db_path)
