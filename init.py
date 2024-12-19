import re
import sqlite3
from typing import Dict, List
from mwparserfromhell import parse
import xml.etree.ElementTree as ET
from pathlib import Path

# Function to clean extracted attributes
def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return None
    text = re.sub(r'\[\[|\]\]', '', text) # Remove Wiki links
    text = re.sub(r'\{\{.*?\}\}', '', text) # Remove nested templates
    text = re.sub(r'<.*?>', '', text) # Remove HTML tags
    text = re.sub(r'\[[:][^]]*?[:]\]', '', text) # Remove category links
    text = re.sub(r'&[a-z]+;', '', text) # Remove HTML entities (e.g., &nbsp;)
    text = re.sub(r'[|]', ', ', text) # Replace pipe with comma
    # Remove special characters except alphanumeric, spaces, and hyphens
    text = re.sub(r'[^\w\s,\'\-().]', '', text)
    return text.strip()

# Function to format birth date into YYYY-MM-DD format
def clean_birth_date(raw_date):
    if not raw_date:
        return None

    # Regex to match date formats within templates like {{birth date|YYYY|MM|DD}} or {{birth date and age|YYYY-MM-DD}}
    match = re.search(r'\{\{(?:birth date(?: and age)?|Birth date(?: and age)?)[^\d]*(\d{4})[|\-](\d{1,2})[|\-](\d{1,2})', raw_date, re.IGNORECASE)
    if match:
        year, month, day = match.groups()
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"

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

# Clean relationship strings
def clean_relationship_value(value: str) -> str:
    if not value:
        return None
    value = re.sub(r"\(.*?\)", "", value)  # Remove parentheses content
    value = re.sub(r"\[\[(.*?)\]\]", r"\1", value)  # Extract names from Wiki links
    value = re.sub(r"\{\{marriage\|([^\|]+)\|.*?\}\}", r"\1", value)  # Extract name from marriage template
    value = re.sub(r"\{\{.*?\}\}", "", value)  # Remove other templates
    return value.strip()

# Extract awards using mwparserfromhell
def extract_awards(wiki_code) -> str:
    awards_list = []
    for section in wiki_code.get_sections(matches=r'(Awards|Honors)', flat=True):
        lines = section.strip_code().strip().split('\n')
        awards_list.extend([clean_text(line) for line in lines if line.strip()])
    return ', '.join(filter(None, awards_list))

# Extract works using mwparserfromhell
def extract_works(wiki_code) -> str:
    works_list = []
    for section in wiki_code.get_sections(matches=r'(Works|Selected works)', flat=True):
        lines = section.strip_code().strip().split('\n')
        works_list.extend([clean_text(line) for line in lines if line.strip()])
    return ', '.join(filter(None, works_list))

# Extract infobox data using mwparserfromhell
def extract_infobox_data(text):
    wiki_code = parse(text)
    infobox = wiki_code.filter_templates()

    data = {}
    for template in infobox:
        infobox_content = {}
        for field in template.params:
            attribute_name = field.name.strip()
            if attribute_name == "years_active":
                continue
            try:
                field_value = clean_text(field.value.strip_code())
                if field_value:
                    infobox_content[attribute_name] = field_value
            except ValueError:
                infobox_content[attribute_name] = None
        data.update(infobox_content)

    # Extract awards and works
    data["works"] = extract_works(wiki_code)
    data["awards"] = extract_awards(wiki_code)

    return data

# Parse the XML dump and extract relevant information
def parse_dump(dump_path: str) -> List[Dict[str, str]]:
    extracted_data = []

    for event, elem in ET.iterparse(dump_path, events=("start", "end")):
        if event == "end" and elem.tag.endswith("page"):
            title = elem.find("./{*}title").text
            revision = elem.find("./{*}revision/{*}text")
            text = revision.text if revision is not None else ""
            if not text:
                continue

            infobox_data = extract_infobox_data(text)
            infobox_data["person_id"] = title
            infobox_data["name"] = infobox_data.get("name") or title
            infobox_data["birth_date"] = clean_birth_date(infobox_data.get("birth_date"))
            extracted_data.append(infobox_data)
            elem.clear()

    return extracted_data

# Saves the extracted data into the database
def save_to_database(db_path: str, data: List[Dict[str, str]]):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for entry in data:
        cursor.execute(
            """
            INSERT OR REPLACE INTO celebrities (
                person_id, name, birth_name, birth_date, birth_place
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.get("person_id"),
                entry.get("name"),
                entry.get("birth_name"),
                entry.get("birth_date"),
                entry.get("birth_place"),
            ),
        )

        if "occupation" in entry and entry["occupation"]:
            for occupation in entry["occupation"].split(","):
                cursor.execute(
                    """
                    INSERT INTO occupations (person_id, occupation)
                    VALUES (?, ?)
                    """,
                    (entry.get("person_id"), occupation.strip()),
                )

        if "spouse" in entry or "partner" in entry or "num_children" in entry:
            cursor.execute(
                """
                INSERT INTO relationships (person_id, spouse, partner, num_children)
                VALUES (?, ?, ?, ?)
                """,
                (
                    entry.get("person_id"),
                    clean_relationship_value(entry.get("spouse")),
                    clean_relationship_value(entry.get("partner")),
                    entry.get("num_children"),
                ),
            )

        if "works" in entry and entry["works"]:
            for work in entry["works"].split(","):
                cursor.execute(
                    """
                    INSERT INTO works (person_id, work_type, work_title)
                    VALUES (?, ?, ?)
                    """,
                    (entry.get("person_id"), None, work.strip()),
                )

        if "awards" in entry and entry["awards"]:
            for award in entry["awards"].split(","):
                cursor.execute(
                    """
                    INSERT INTO awards (person_id, award)
                    VALUES (?, ?)
                    """,
                    (entry.get("person_id"), award.strip()),
                )
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    dump_path = "C:/Users/afafs/Documents/simplewiki-20240801-pages-articles-multistream.xml"
    db_path = "celebrities.db"
    
    # Parse the Wikipedia dump and extract relevant information, then save to db
    extracted_data = parse_dump(dump_path)
    save_to_database(db_path, extracted_data)
    print(f"Data successfully extracted and saved to {db_path}")