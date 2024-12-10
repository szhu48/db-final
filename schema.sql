CREATE TABLE Person (
    id SERIAL PRIMARY KEY,
    wikidata_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    birth_date DATE
);

CREATE TABLE Occupation (
    id SERIAL PRIMARY KEY,
    person_id INT REFERENCES Person(id),
    occupation VARCHAR(255)
);

CREATE TABLE Award (
    id SERIAL PRIMARY KEY,
    person_id INT REFERENCES Person(id),
    award VARCHAR(255)
);
