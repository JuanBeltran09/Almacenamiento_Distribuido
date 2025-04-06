import requests
import os
import hashlib
from encryption.crypto import encrypt_chunk, decrypt_chunk

# Configuración
TRACKER_URL = "http://localhost:5000"
NODES = [
    "http://localhost:5001",
    "http://localhost:5002",
    "http://localhost:5003"
]
CHUNK_SIZE = 1024  # Tamaño de los fragmentos en bytes

CLIENT_DIR = os.path.dirname(__file__)  # Asegura que se use la carpeta client/

def split_and_store_file(file_path):
    """ Divide un archivo en fragmentos, los cifra y los envía a los nodos """
    if not os.path.exists(file_path):
        print("[✖] Archivo no encontrado.")
        return
    
    file_name = os.path.basename(file_path)
    fragments = {}

    with open(file_path, "rb") as f:
        index = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break  # Salir cuando ya no haya datos
            
            encrypted_chunk = encrypt_chunk(chunk)
            fragment_id = hashlib.sha256(encrypted_chunk).hexdigest()
            node = NODES[index % len(NODES)]  # Distribuir entre los nodos

            files = {"file": (fragment_id, encrypted_chunk)}
            data = {"fragment_id": fragment_id, "index": index, "node_id": node}  

            try:
                response = requests.post(f"{node}/store_fragment", files=files, data=data)
                if response.status_code == 200:
                    fragments[fragment_id] = {"node": node, "index": index}
                    print(f"[✔] Fragmento {index} ({fragment_id}) almacenado en {node}")
                else:
                    print(f"[✖] Error al almacenar fragmento en {node}: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"[✖] Error de conexión con {node}: {e}")

            index += 1

    if not fragments:
        print("[✖] Error: No se almacenaron fragmentos.")
        return

    # Registrar los fragmentos en el Tracker
    tracker_data = {"file_name": file_name, "fragments": fragments}
    try:
        tracker_response = requests.post(f"{TRACKER_URL}/register_fragments", json=tracker_data)
        if tracker_response.status_code == 200:
            print(f"[✔] Archivo {file_name} registrado en el Tracker.")
        else:
            print(f"[✖] Error al registrar los fragmentos en el Tracker: {tracker_response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[✖] Error de conexión con el Tracker: {e}")

def download_and_reconstruct_file(file_name):
    """ Descarga fragmentos de los nodos y reconstruye el archivo original """
    try:
        response = requests.get(f"{TRACKER_URL}/get_fragments/{file_name}")
        if response.status_code != 200:
            print("[✖] No se encontraron fragmentos para este archivo.")
            return
    except requests.exceptions.RequestException as e:
        print(f"[✖] Error de conexión con el Tracker: {e}")
        return

    fragments_info = response.json()
    ordered_fragments = sorted(fragments_info.items(), key=lambda x: x[1]["index"])
    reconstructed_data = bytearray()

    for fragment_id, frag_info in ordered_fragments:
        node_url = frag_info["node"]
        try:
            fragment_response = requests.get(f"{node_url}/get_fragment/{fragment_id}")
            if fragment_response.status_code == 200:
                decrypted_chunk = decrypt_chunk(fragment_response.content)
                if decrypted_chunk is None:
                    print(f"[✖] No se pudo descifrar el fragmento {fragment_id}.")
                    return
                reconstructed_data.extend(decrypted_chunk)
                print(f"[✔] Fragmento {fragment_id} descargado y descifrado.")
            else:
                print(f"[✖] No se pudo descargar el fragmento {fragment_id} desde {node_url}")
                return
        except requests.exceptions.RequestException as e:
            print(f"[✖] Error de conexión con {node_url}: {e}")
            return

    reconstructed_path = os.path.join(CLIENT_DIR, f"reconstructed_{file_name}")
    with open(reconstructed_path, "wb") as f:
        f.write(reconstructed_data)

    print(f"[✔] Archivo reconstruido en: {reconstructed_path}")

if __name__ == "__main__":
    action = input("¿Qué desea hacer? (1: Subir archivo, 2: Recuperar archivo): ")

    if action == "1":
        file_path = input("Ingrese la ruta del archivo a subir: ")
        split_and_store_file(file_path)
    elif action == "2":
        file_name = input("Ingrese el nombre del archivo a recuperar: ")
        download_and_reconstruct_file(file_name)
    else:
        print("Opción inválida.")
