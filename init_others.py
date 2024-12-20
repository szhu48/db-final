import re
import sqlite3
from typing import Dict, List
from mwparserfromhell import parse
import xml.etree.ElementTree as ET
from pathlib import Path
from word2number import w2n

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

def extract_num_children(value: str) -> int:
    """
    Extracts the number of children from the given string.
    If no number is found, returns None.
    """
    if not value:
        return None

    # Try to find a numeric value in the string
    match = re.search(r'\b\d+\b', value)
    if match:
        return int(match.group())

    # Handle cases where numbers are written out in words
    try:
        # Convert the words to a number
        return w2n.word_to_num(value)
    except ValueError:
        return None

# Clean relationship strings
def clean_relationship_value(value: str) -> str:
    if not value:
        return None
    
    # If value is a list, clean each item and join with a comma
    if isinstance(value, list):
        return ", ".join([clean_relationship_value(v) for v in value if v])

    value = re.sub(r"\(.*?\)", "", value)  # Remove parentheses content
    value = re.sub(r"\[\[(.*?)\]\]", r"\1", value)  # Extract names from Wiki links
    value = re.sub(r"\{\{marriage\|([^\|]+)\|.*?\}\}", r"\1", value)  # Extract name from marriage template
    value = re.sub(r"\{\{.*?\}\}", "", value)  # Remove other templates
    return value.strip()

# Extract awards using mwparserfromhell
#def extract_awards(wiki_code) -> str:
 #   awards_list = []
  #  for section in wiki_code.get_sections(matches=r'(Awards|Honors)', flat=True):
   #     lines = section.strip_code().strip().split('\n')
    #    awards_list.extend([clean_text(line) for line in lines if line.strip()])
    #return ', '.join(filter(None, awards_list))

def extract_awards(wiki_code) -> str:
    awards_list = []
    
    # Iterate through sections that match 'Awards' or 'Honors'
    for section in wiki_code.get_sections(matches=r'(Awards|Honors)', flat=True):
        section_text = section.strip_code().strip()
        
        # If the section is not empty, split it by lines
        if section_text:
            lines = section_text.split('\n')
            for line in lines:
                # Clean the line and add it to the awards list if it's not empty
                cleaned_line = clean_text(line)
                if cleaned_line:
                    awards_list.append(cleaned_line)
    
    # Return the awards as a comma-separated string
    return ', '.join(filter(None, awards_list))

def extract_infobox_data(text):
    wiki_code = parse(text)
    infobox = wiki_code.filter_templates()

    data = {}
    for template in infobox:
        infobox_content = {}  # Initialize for each template
        for field in template.params:
            attribute_name = field.name.strip()
            if attribute_name == "years_active":
                continue

            try:
                # Clean and store the field value
                field_value = clean_text(field.value.strip_code())
                if field_value:
                    infobox_content[attribute_name] = field_value
            except ValueError:
                infobox_content[attribute_name] = None
        
        # Update the main data dictionary with the parsed infobox content
        data.update(infobox_content)

    # Extract and process specific fields
    if "num_children" in data:
        data["num_children"] = extract_num_children(data["num_children"])
    # Extract awards
    if "person_id" in data:
        print(f"Debug: awards extracted: {data['awards']}")
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
            extracted_data.append(infobox_data)
            elem.clear()

    print(f"Extracted {len(extracted_data)} entries")  # Debug print
    if len(extracted_data) > 0:
        print(f"First few entries: {extracted_data[:3]}") 
    
    return extracted_data

def save_to_database(db_path: str, data: List[Dict[str, str]]):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for entry in data:
        print(f"Processing entry: {entry}")  # Add this line for debugging

        # Process occupations
        if "occupation" in entry and entry["occupation"]:
            occupations = re.split(r',|\n', entry["occupation"])
            for occupation in occupations:
                occupation = occupation.strip()
                if occupation:
                    cursor.execute(
                        """
                        INSERT INTO occupations (person_id, occupation)
                        VALUES (?, ?)
                        """,
                        (entry.get("person_id"), occupation),
                    )

        # Process relationships
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

        # Process awards
        if "awards" in entry and entry["awards"]:
            awards = re.split(r',|\n', entry["awards"])
            for award in awards:
                award = award.strip()
                if award:
                    print(f"Inserting award: {award}") # debug log
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO awards (person_id, award)
                        VALUES (?, ?)
                        """,
                        (entry.get("person_id"), award),
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