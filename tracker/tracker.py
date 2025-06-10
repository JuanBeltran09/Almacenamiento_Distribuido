from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)

REGISTRY_FILE = "registry.json"
files_registry = {}  
nodes = {}

# Cargar registro al iniciar
if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, "r") as f:
        files_registry = json.load(f)
        print("[✔] Registro de archivos cargado.")

@app.route('/register_node', methods=['POST'])
def register_node():
    data = request.json
    node_id = data.get("node_id")

    if node_id and node_id not in nodes:
        nodes[node_id] = 0
        return jsonify({"message": f"Nodo {node_id} registrado exitosamente"}), 200
    return jsonify({"error": "Nodo ya existe o datos incorrectos"}), 400

@app.route('/register_fragments', methods=['POST'])
def register_fragments():
    data = request.json
    file_name = data.get("file_name")
    fragments = data.get("fragments")

    if not file_name or not fragments:
        return jsonify({"error": "Datos incorrectos"}), 400

    files_registry[file_name] = fragments

    # Guardar en disco
    with open(REGISTRY_FILE, "w") as f:
        json.dump(files_registry, f)

    print(f"[✔] Se registraron {len(fragments)} fragmentos para {file_name}")
    return jsonify({"message": f"Fragmentos de {file_name} registrados"}), 200

@app.route('/get_fragments/<file_name>', methods=['GET'])
def get_fragments(file_name):
    if file_name in files_registry:
        return jsonify(files_registry[file_name]), 200
    return jsonify({"error": "Archivo no encontrado"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
