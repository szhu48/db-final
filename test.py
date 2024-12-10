from SPARQLWrapper import SPARQLWrapper, JSON

def test_sparql_query():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery("""
    SELECT ?person ?personLabel ?occupationLabel ?birthDate ?awardLabel WHERE {
        ?person wdt:P31 wd:Q5.  # Instance of human
        ?person wdt:P106 ?occupation. # Occupation
        ?person wdt:P569 ?birthDate. # Date of birth
        OPTIONAL { ?person wdt:P166 ?award. } # Awards
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } LIMIT 10
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print({
            "person": result["person"]["value"],
            "name": result["personLabel"]["value"],
            "occupation": result["occupationLabel"]["value"],
            "birth_date": result["birthDate"]["value"],
            "award": result.get("awardLabel", {}).get("value", None)
        })

test_sparql_query()