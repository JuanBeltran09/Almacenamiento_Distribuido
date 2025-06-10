from flask import Flask, request, jsonify

app = Flask(__name__)

nodes = {}  # { "http://nodo1": cantidad_de_fragmentos }
files_registry = {}  # { "archivo.pdf": { "fragmento1": {"node": "http://nodo1", "index": 0} } }

@app.route('/register_node', methods=['POST'])
def register_node():
    """Registra un nodo de almacenamiento."""
    data = request.json
    node_id = data.get("node_id")
   

    if node_id and node_id not in nodes:
        nodes[node_id] = 0
        return jsonify({"message": f"Nodo {node_id} registrado exitosamente"}), 200
    return jsonify({"error": "Nodo ya existe o datos incorrectos"}), 400

@app.route('/register_fragments', methods=['POST'])
def register_fragments():
    """ Registra los fragmentos de un archivo en el tracker """
    data = request.json
    file_name = data.get("file_name")
    fragments = data.get("fragments")

    if not file_name or not fragments:
        return jsonify({"error": "Datos incorrectos"}), 400

    files_registry[file_name] = fragments

    print(f"[✔] Se registraron {len(fragments)} fragmentos para {file_name}")

    return jsonify({"message": f"Fragmentos de {file_name} registrados"}), 200

@app.route('/get_fragments/<file_name>', methods=['GET'])
def get_fragments(file_name):
    """Devuelve los fragmentos de un archivo."""
    if file_name in files_registry:
        return jsonify(files_registry[file_name]), 200
    return jsonify({"error": "Archivo no encontrado"}), 404

if __name__ == '__main__':
    app.run(host='192.168.43.156', port=5000)
