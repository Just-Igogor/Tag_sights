from flask import Flask, request, jsonify
import sqlite3
import json

app = Flask(__name__)

def get_db_connection():
    connection = sqlite3.connect("C:/Users/igogo/Desktop/Sol/taganrog_sights.db")
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/sights', methods=['GET'])
def get_all_sights():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM sights")
    sights = cursor.fetchall()
    connection.close()
    return app.response_class(
        response=json.dumps([dict(row) for row in sights], ensure_ascii=False),
        mimetype='application/json'
    )

@app.route('/sights/<int:sight_id>', methods=['GET'])
def get_sight(sight_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM sights WHERE id = ?", (sight_id,))
    sight = cursor.fetchone()
    connection.close()
    if sight is None:
        return jsonify({"error": "Sight not found"}), 404
    return jsonify(dict(sight))

@app.route('/sights', methods=['POST'])
def add_sight():
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    description = data.get('description')

    if not all([name, address, latitude, longitude]):
        return jsonify({"error": "Missing required fields"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO sights (name, address, latitude, longitude, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, address, latitude, longitude, description)
    )
    connection.commit()
    connection.close()
    return jsonify({"message": "Sight added successfully"}), 201

@app.route('/sights/<int:sight_id>', methods=['PUT'])
def update_sight(sight_id):
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    description = data.get('description')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE sights
        SET name = COALESCE(?, name),
            address = COALESCE(?, address),
            description = COALESCE(?, description)
        WHERE id = ?
        """,
        (name, address, description, sight_id)
    )
    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Sight not found"}), 404

    return jsonify({"message": "Sight updated successfully"})

@app.route('/sights/<int:sight_id>', methods=['DELETE'])
def delete_sight(sight_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM sights WHERE id = ?", (sight_id,))
    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Sight not found"}), 404

    return jsonify({"message": "Sight deleted successfully"})

if __name__ == '__main__':
    app.run(debug=True)
