from flask import Flask, request, jsonify, render_template_string
import sqlite3
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Глобальная переменная для хранения координат пользователя
user_location = {'latitude': None, 'longitude': None}

# Главная страница с трекером геолокации, использующим satellite-определение (enableHighAccuracy)
@app.route('/')
def index():
    return render_template_string('''
<html>
  <head>
    <title>User Location Tracker</title>
  </head>
  <body>
    <h1>Отслеживание местоположения пользователя (с использованием спутниковых данных)</h1>
    <p id="location">Ожидание определения местоположения...</p>
    <script>
      function updateLocation(position) {
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;
        document.getElementById('location').innerHTML = "Широта: " + lat + ", Долгота: " + lon;
        fetch('/update_location', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({latitude: lat, longitude: lon})
        });
      }
      function handleError(error) {
        console.warn('Ошибка (' + error.code + '): ' + error.message);
      }
      // Обновление координат каждую секунду с использованием высокоточной геолокации
      setInterval(function() {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(updateLocation, handleError, {
            enableHighAccuracy: true,
            timeout: 5000,
            maximumAge: 0
          });
        } else {
          document.getElementById('location').innerHTML = "Геолокация не поддерживается вашим браузером.";
        }
      }, 1000);
    </script>
  </body>
</html>
''')

# Эндпоинт для обновления координат пользователя
@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    if latitude is None or longitude is None:
        return jsonify({"error": "Отсутствуют необходимые координаты"}), 400
    global user_location
    user_location['latitude'] = latitude
    user_location['longitude'] = longitude
    return jsonify({"message": "Координаты обновлены успешно"})

# Эндпоинт для получения текущих координат пользователя
@app.route('/get_location', methods=['GET'])
def get_location():
    return jsonify(user_location)


def get_db_connection():
    connection = sqlite3.connect("../taganrog_sights.db")
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
    type = data.get('type')

    if not all([name, address, latitude, longitude]):
        return jsonify({"error": "Missing required fields"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO sights (name, address, latitude, longitude, description, type)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, address, latitude, longitude, description, type)
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
    type = data.get('type')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE sights
        SET name = COALESCE(?, name),
            address = COALESCE(?, address),
            description = COALESCE(?, description)
            type = COALESCE(?, type)
        WHERE id = ?
        """,
        (name, address, description, sight_id, type)
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
