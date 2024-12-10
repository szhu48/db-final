from flask import Flask, request, jsonify
from sqlalchemy import create_engine

app = Flask(__name__)
engine = create_engine(DB_URL)

@app.route('/add_person', methods=['POST'])
def add_person():
    data = request.json
    try:
        with engine.connect() as connection:
            connection.execute(
                "INSERT INTO Person (wikidata_id, name, birth_date) VALUES (%s, %s, %s)",
                (data['wikidata_id'], data['name'], data['birth_date'])
            )
        return jsonify({"message": "Person added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)