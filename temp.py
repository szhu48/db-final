from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import sqlite3

# Database connection
conn = sqlite3.connect('celebrity_database.db')
cursor = conn.cursor()

# Step 1: Create the Tables
def create_tables():
    cursor.executescript("""
    -- Table: Celebrity
    CREATE TABLE IF NOT EXISTS CELEBRITY (
        CelebrityID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Age INTEGER NOT NULL,
        Birthday DATE NOT NULL,
        Sex TEXT NOT NULL,
        Nationality TEXT NOT NULL
    );

    -- Table: Background
    CREATE TABLE IF NOT EXISTS BACKGROUND (
        CelebrityID INTEGER PRIMARY KEY,
        Hometown TEXT,
        Religion TEXT,
        HobbyID INTEGER,
        DietID INTEGER,
        Languages TEXT,
        EducationID INTEGER,
        FOREIGN KEY (CelebrityID) REFERENCES CELEBRITY(CelebrityID),
        FOREIGN KEY (HobbyID) REFERENCES HOBBIES(HobbyID),
        FOREIGN KEY (DietID) REFERENCES DIET(DietID),
        FOREIGN KEY (EducationID) REFERENCES EDUCATION(EducationID)
    );

    -- Table: Education
    CREATE TABLE IF NOT EXISTS EDUCATION (
        EducationID INTEGER PRIMARY KEY AUTOINCREMENT,
        Institute_Name TEXT NOT NULL,
        Highest_Degree TEXT NOT NULL,
        Year_Degree_Earned INTEGER,
        CelebrityID INTEGER,
        FOREIGN KEY (CelebrityID) REFERENCES CELEBRITY(CelebrityID)
    );

    -- Table: Relationship
    CREATE TABLE IF NOT EXISTS RELATIONSHIP (
        RelationshipID INTEGER PRIMARY KEY AUTOINCREMENT,
        Type TEXT NOT NULL,
        SO_Name TEXT,
        Status TEXT,
        CelebrityID INTEGER NOT NULL,
        FOREIGN KEY (CelebrityID) REFERENCES CELEBRITY(CelebrityID)
    );

    -- Table: Projects
    CREATE TABLE IF NOT EXISTS PROJECTS (
        WorkID INTEGER PRIMARY KEY AUTOINCREMENT,
        CelebrityID INTEGER NOT NULL,
        Title TEXT,
        Type TEXT,
        Role TEXT,
        AwardID INTEGER,
        FOREIGN KEY (CelebrityID) REFERENCES CELEBRITY(CelebrityID),
        FOREIGN KEY (AwardID) REFERENCES AWARDS(AwardID)
    );

    -- Table: Awards
    CREATE TABLE IF NOT EXISTS AWARDS(
        AwardID INTEGER PRIMARY KEY AUTOINCREMENT,
        AwardName TEXT,
        Category TEXT,
        Year_Won INTEGER,
        CelebrityID INTEGER,
        Collaborators TEXT,
        FOREIGN KEY (CelebrityID) REFERENCES CELEBRITY(CelebrityID)
    );

    -- Table: Pets
    CREATE TABLE IF NOT EXISTS PETS (
        CelebrityID INTEGER PRIMARY KEY,
        Num_Pets INTEGER,
        Animal_Type TEXT,
        FOREIGN KEY (CelebrityID) REFERENCES CELEBRITY(CelebrityID)
    );

    -- Table: Diet
    CREATE TABLE IF NOT EXISTS DIET (
        DietID INTEGER PRIMARY KEY AUTOINCREMENT,
        Type TEXT NOT NULL,
        Allergy TEXT,
        Favorite_Cuisine TEXT,
        Salty_or_Sweet TEXT
    );

    -- Table: Hobbies
    CREATE TABLE IF NOT EXISTS HOBBIES (
        HobbyID INTEGER PRIMARY KEY AUTOINCREMENT,
        Type TEXT NOT NULL,
        Hobby_Name TEXT,
        Skill_Level TEXT
    );
    """)
    conn.commit()

# Step 2: Extract Data from Wikidata
def execute_sparql_query(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]

def fetch_celebrities():
    query = """
    SELECT DISTINCT ?person ?personLabel ?birthDate ?sexLabel ?nationalityLabel WHERE {
        ?person wdt:P31 wd:Q5;               # Instance of human
                wdt:P569 ?birthDate;         # Birthdate
                wdt:P21 ?sex;                # Sex
                wdt:P27 ?nationality.        # Nationality
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    LIMIT 1000
    """
    results = execute_sparql_query(query)
    data = []
    for result in results:
        data.append({
            "Name": result["personLabel"]["value"],
            "birthDate": result["birthDate"]["value"],
            "Sex": result["sexLabel"]["value"],
            "Nationality": result["nationalityLabel"]["value"]
        })
    return pd.DataFrame(data)

# Step 3: Transform Data
def transform_data(df):
    df['Age'] = pd.Timestamp.now().year - pd.to_datetime(df['birthDate']).dt.year
    return df

# Step 4: Populate the Database
def populate_database(df):
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO CELEBRITY (Name, Age, Birthday, Sex, Nationality)
        VALUES (?, ?, ?, ?, ?)
        """, (row['Name'], row['Age'], row['birthDate'], row['Sex'], row['Nationality']))
    conn.commit()

# Main Execution
if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
   
    print("Fetching celebrity data...")
    celebrities_df = fetch_celebrities()
    print(f"Fetched {len(celebrities_df)} records.")
   
    print("Transforming data...")
    transformed_data = transform_data(celebrities_df)
   
    print("Populating the database...")
    populate_database(transformed_data)
    print("Database populated successfully.")