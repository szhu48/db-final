from sqlalchemy import create_engine

# Replace with your database connection details
DB_URL = "postgresql://username:password@localhost/celebrity_db"

def load_data_to_db(df):
    engine = create_engine(DB_URL)
    with engine.connect() as connection:
        # Load Person Table
        person_df = df[['person', 'name', 'birth_date']].drop_duplicates()
        person_df.columns = ['wikidata_id', 'name', 'birth_date']
        person_df.to_sql('Person', con=connection, if_exists='append', index=False)

        # Load Occupation Table
        occupation_df = df[['person', 'occupation']].drop_duplicates()
        occupation_df.columns = ['wikidata_id', 'occupation']
        occupation_df.to_sql('Occupation', con=connection, if_exists='append', index=False)

        # Load Award Table
        award_df = df[['person', 'award']].dropna().drop_duplicates()
        award_df.columns = ['wikidata_id', 'award']
        award_df.to_sql('Award', con=connection, if_exists='append', index=False)

load_data_to_db(celebrity_df)