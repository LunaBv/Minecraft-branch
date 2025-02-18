import subprocess
import sys
import re
import os
import requests
import zipfile
import shutil

# Funciones del primer archivo (Branch)
def run_command(command):
    """Ejecutar un comando en el sistema y verificar si fue exitoso."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[Error] {e}\n{e.stderr}")
        sys.exit(1)

def gradient_text(text, colors):
    length = len(text)
    num_colors = len(colors)
    result = ""
    for i, char in enumerate(text):
        color_index = (i * (num_colors - 1)) // length
        t = (i * (num_colors - 1)) / length - color_index
        color1 = colors[color_index]
        color2 = colors[color_index + 1] if color_index + 1 < num_colors else colors[color_index]
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        result += f'\033[38;2;{r};{g};{b}m{char}'
    return result + '\033[0m'

def get_remote_info():
    remote_info = run_command(["git", "remote", "-v"])
    match = re.search(r'origin\s+([^\s]+)\s+\(fetch\)', remote_info)
    if match:
        return match.group(1)
    else:
        raise ValueError("No se encontró la URL del repositorio remoto.")

def clean_branch():
    """Eliminar todos los archivos y carpetas del índice de Git excepto los especificados."""
    keep_files = ["servidor_minecraft", "configuracion.json"]
    for item in run_command(["git", "ls-files"]).split("\n"):
        if item and item not in keep_files:  # Asegurarse de que el item no esté vacío
            run_command(["git", "rm", "--cached", item])

def branch():
    new_branch_name = "Minecraft_branch"
    commit_message = "Branch para guardar tu server_minecraft"

    # Obtener la URL del repositorio
    repo_url = get_remote_info()

    # Verificar si el branch actual es 'main'
    current_branch = run_command(["git", "branch", "--show-current"])
    print(f"Current branch: {current_branch}")
    if current_branch != "main":
        print("Changing to 'main' branch...")
        # Cambiar al branch 'main'
        run_command(["git", "checkout", "main"])

        # Copiar archivos al branch 'main'
        run_command(["git", "checkout", current_branch, "--", "servidor_minecraft", "configuracion.json"])
        run_command(["git", "add", "--force", "servidor_minecraft", "configuracion.json"])
        run_command(["git", "commit", "-m", "Copiando archivos al main"])

    # Verificar si el branch ya existe localmente
    existing_branches = run_command(["git", "branch", "--list", new_branch_name])
    print(f"Existing branches: {existing_branches}")
    if existing_branches:
        print(f"Deleting existing branch {new_branch_name}")
        run_command(["git", "branch", "-D", new_branch_name])  # Eliminar el branch local existente

    # Crear el nuevo branch (sin cambiar a él)
    print(f"Creating new branch {new_branch_name}")
    run_command(["git", "branch", new_branch_name])

    # Limpiar el branch actual
    print("Cleaning branch...")
    clean_branch()

    # Agregar los archivos al área de staging
    print("Adding files to staging area...")
    run_command(["git", "add", "--force", "servidor_minecraft", "configuracion.json"])

    # Intentar commitar
    try:
        print("Committing changes...")
        run_command(["git", "commit", "-m", commit_message])
    except subprocess.CalledProcessError as e:
        if "nothing to commit" not in e.stderr.lower():
            print(gradient_text(f"No se pudo hacer commit: {e.stderr}", [(255, 0, 0), (255, 128, 0)]))
            input("Press any key to exit...")
            sys.exit(1)

    # Push del nuevo branch al repositorio remoto
    print("Pushing new branch to remote...")
    try:
        run_command(["git", "push", "-u", "origin", new_branch_name, "--force"])
    except subprocess.CalledProcessError as e:
        print(gradient_text(f"No se pudo hacer push: {e.stderr}", [(255, 0, 0), (255, 128, 0)]))
        input("Press any key to exit...")
        sys.exit(1)

    # Generar la URL de descarga del ZIP
    user_name, repo_name = repo_url.split('/')[-2], repo_url.split('/')[-1].replace('.git', '')
    zip_url = f"https://codeload.github.com/{user_name}/{repo_name}/zip/refs/heads/{new_branch_name}"
    print(gradient_text(f"\nBranch creado/actualizado localmente: {new_branch_name}\nEnlace al branch para descargar en ZIP: {zip_url}", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))

    input(gradient_text("\nPresiona cualquier tecla para continuar...", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    
    sys.exit(0)




def download_and_extract_zip(url, extract_to='.'):
    local_zip_file = "repo.zip"
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_zip_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        with zipfile.ZipFile(local_zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    finally:
        if os.path.exists(local_zip_file):
            os.remove(local_zip_file)

def link():
    zip_url2 = input(gradient_text("Introduce el enlace directo del archivo ZIP: ", [(0, 255, 0), (0, 128, 255)])).strip()

    # Descargar y extraer el archivo zip
    download_and_extract_zip(zip_url2, os.getcwd())

    # Obtener el nombre del repositorio y el branch del enlace
    repo_name2 = zip_url2.split('/')[-5]
    branch_name2 = zip_url2.split('/')[-1]

    # Formatear el nombre esperado del directorio extraído
    expected_dir_name = f"{repo_name2}-{branch_name2}"

    # Verificar si la carpeta existe
    if not os.path.isdir(expected_dir_name):
        print(gradient_text("Error: No se pudo encontrar la carpeta extraída correctamente.", [(255, 0, 0), (255, 128, 0)]))
        sys.exit(1)

    # Mover archivos del directorio extraído al directorio principal
    extracted_dir = os.path.join(os.getcwd(), expected_dir_name)
    for item in os.listdir(extracted_dir):
        source_path = os.path.join(extracted_dir, item)
        target_path = os.path.join(os.getcwd(), item)
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
        shutil.move(source_path, target_path)
    
    shutil.rmtree(extracted_dir)

    print(gradient_text("\n¡Repositorio descargado y extraído exitosamente!", [(0, 255, 0), (0, 128, 255)]))
    print(gradient_text("\nDirectorio actualizado con el contenido del archivo ZIP.", [(0, 255, 0), (0, 128, 255)]))