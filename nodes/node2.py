import requests
from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

NODE_ID = "node2"
PORT = 5002
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")

TRACKER_URL = "http://localhost:5000"

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
    file = request.files.get("file")

    if fragment_id and file:
        file_path = os.path.join(STORAGE_DIR, fragment_id)
        file.save(file_path)

        requests.post(f"{TRACKER_URL}/store_fragment", json={"node_id": NODE_ID, "fragment_id": fragment_id})

        return jsonify({"message": f"Fragmento {fragment_id} almacenado en {NODE_ID}"}), 200

    return jsonify({"error": "Datos incorrectos"}), 400

@app.route('/get_fragment/<fragment_id>', methods=['GET'])
def get_fragment(fragment_id):
    file_path = os.path.join(STORAGE_DIR, fragment_id)

    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/octet-stream')

    return jsonify({"error": "Fragmento no encontrado"}), 404

if __name__ == '__main__':
    register_node()
    app.run(host='0.0.0.0', port=PORT)
