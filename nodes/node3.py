import requests
from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

NODE_ID = "node3"
PORT = 5003
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")

TRACKER_URL = "http://192.168.1.51:5000" #colocar id sebastian

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def register_node():
    response = requests.post(f"{TRACKER_URL}/register_node", json={"node_id": NODE_ID})
    if response.status_code == 200:
        print(f"[✔] Nodo {NODE_ID} registrado exitosamente en el Tracker")
    else:
        print(f"[✖] Error al registrar el nodo: {response.json()}")

@app.route('/store_fragment', methods=['POST'])
def store_fragment():
    fragment_id = request.form.get("fragment_id")
    user = request.form.get("user")  
    file = request.files.get("file")

    if fragment_id and file and user:
        # Crear la subcarpeta del usuario si no existe
        user_dir = os.path.join(STORAGE_DIR, user)
        os.makedirs(user_dir, exist_ok=True)

        file_path = os.path.join(user_dir, fragment_id)
        file.save(file_path)

        requests.post(f"{TRACKER_URL}/store_fragment", json={"node_id": NODE_ID, "fragment_id": fragment_id})

        return jsonify({"message": f"Fragmento {fragment_id} almacenado en {NODE_ID} para el usuario {user}"}), 200

    return jsonify({"error": "Datos incorrectos"}), 400

@app.route('/get_fragment/<user>/<fragment_id>', methods=['GET'])
def get_fragment(user, fragment_id):
    file_path = os.path.join(STORAGE_DIR, user, fragment_id)

    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/octet-stream')

    return jsonify({"error": "Fragmento no encontrado"}), 404

if __name__ == '__main__':
    register_node()
    app.run(host='0.0.0.0', port=PORT)
