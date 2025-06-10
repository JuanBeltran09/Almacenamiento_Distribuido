from flask import Flask, render_template, request, send_file, session, redirect, url_for
import os, hashlib, requests
from crypto import encrypt_chunk, decrypt_chunk
from werkzeug.utils import secure_filename
from io import BytesIO
from pymongo import MongoClient


client = MongoClient("mongodb+srv://juan:1234@cluster0.k7xgbyp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['distributed_storage']
users_collection = db['users']
files_collection = db['files']

app = Flask(__name__)

TRACKER_URL = "http://192.168.43.156:5000"
NODES = [
    "http://192.168.43.37:5001", #Camilo
    "http://192.168.43.156:5002", # Yo
    "http://192.168.43.35:5003" #Daniel
]
CHUNK_SIZE = 1024

def upload_file(file_name, file_bytes):
    if "username" not in session:
        return "❌ Debes iniciar sesión para subir archivos."

    username = session["username"]
    user_folder = username  # puedes usar os.makedirs si guardas localmente

    fragments = {}

    try:
        index = 0
        while index * CHUNK_SIZE < len(file_bytes):
            chunk = file_bytes[index * CHUNK_SIZE : (index + 1) * CHUNK_SIZE]
            encrypted_chunk = encrypt_chunk(chunk)
            fragment_id = hashlib.sha256(encrypted_chunk).hexdigest()
            node = NODES[index % len(NODES)]

            files = {"file": (fragment_id, encrypted_chunk)}
            data = {
                "fragment_id": fragment_id,
                "index": index,
                "node_id": node,
                "user": username
            }

            response = requests.post(f"{node}/store_fragment", files=files, data=data)
            if response.status_code == 200:
                fragments[fragment_id] = {"node": node, "index": index}
            else:
                return f"❌ Error al almacenar fragmento en {node}: {response.text}"
            index += 1

    except Exception as e:
        return f"❌ Error al procesar el archivo: {e}"

    tracker_data = {"file_name": file_name, "fragments": fragments, "user": username}
    requests.post(f"{TRACKER_URL}/register_fragments", json=tracker_data)

    # Guardar nombre en la base de datos
    files_collection.insert_one({"username": username, "file_name": file_name})
    return f"✔ Archivo '{file_name}' subido y registrado exitosamente."


def recover_file(file_name):
    try:
        response = requests.get(f"{TRACKER_URL}/get_fragments/{file_name}")
        if response.status_code != 200:
            return None, "❌ Archivo no encontrado en el tracker."

        fragments_info = response.json()
        ordered = sorted(fragments_info.items(), key=lambda x: x[1]['index'])
        data = bytearray()

        for frag_id, frag_data in ordered:
            node = frag_data["node"]
            resp = requests.get(f"{node}/get_fragment/{frag_id}")
            if resp.status_code == 200:
                chunk = decrypt_chunk(resp.content)
                if chunk is None:
                    return None, f"❌ Error al descifrar fragmento {frag_id}"
                data.extend(chunk)
            else:
                return None, f"❌ No se pudo descargar fragmento {frag_id} desde {node}"

        return data, f"✔ Archivo '{file_name}' recuperado con éxito."
    except Exception as e:
        return None, f"❌ Error al conectar con el tracker: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    if request.method == 'POST':
        if 'upload' in request.form:
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                file_bytes = file.read()  # Leemos directamente el contenido en memoria
                message = upload_file(filename, file_bytes)
                return render_template("index.html", message=message)

        if 'recover' in request.form:
            filename = request.form.get("recover_filename")
            content, message = recover_file(filename)
            if content:
                return send_file(BytesIO(content), as_attachment=True, download_name=f"reconstructed_{filename}")
            return render_template("index.html", message=message)
    
    username = session.get("username")
    user_files = []
    if username:
        user_files = [f["file_name"] for f in files_collection.find({"username": username})]

    return render_template("index.html", message=message, user_files=user_files, username=username)

app.secret_key = "clave_secreta"  # necesaria para usar sesiones

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if users_collection.find_one({"username": username}):
            return render_template("register.html", message="❌ Usuario ya existe.")
        users_collection.insert_one({"username": username, "password": password})
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = users_collection.find_one({"username": username, "password": password})
        if user:
            session["username"] = username
            return redirect(url_for('index'))
        return render_template("login.html", message="❌ Usuario o contraseña incorrectos.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True, port=5004)
