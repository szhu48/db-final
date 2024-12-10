from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

def fetch_celebrity_data():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery("""
    SELECT ?person ?personLabel ?occupationLabel ?birthDate ?awardLabel WHERE {
        ?person wdt:P31 wd:Q5.  # Instance of human
        ?person wdt:P106 ?occupation. # Occupation
        ?person wdt:P569 ?birthDate. # Date of birth
        OPTIONAL { ?person wdt:P166 ?award. } # Awards
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } LIMIT 100
    """)
    sparql.setReturnFormat(JSON)
    #results = sparql.query().convert()
    try: results = sparql.query().convert() 
    except Exception as e: print(f"Error: {e}")

    data = []
    for result in results["results"]["bindings"]:
        data.append({
            "person": result["person"]["value"],
            "name": result["personLabel"]["value"],
            "occupation": result["occupationLabel"]["value"],
            "birth_date": result["birthDate"]["value"],
            "award": result.get("awardLabel", {}).get("value", None)
        })

    df = pd.DataFrame(data)
    return df

celebrity_df = fetch_celebrity_data()
celebrity_df.to_csv("celebrities.csv", index=False)
print(celebrity_df.head())