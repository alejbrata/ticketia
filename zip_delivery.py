"""
Generador del paquete de entrega TFM — Ticketia.

Genera un ZIP limpio con todo lo necesario para:
  - Revisar el codigo fuente
  - Desplegar con Docker (docker compose up --build)
  - Defender el proyecto ante el tribunal

Uso:
    python zip_delivery.py

El fichero resultante se llama: Ticketia_Entrega_TFM.zip
"""

import os
import zipfile
from datetime import datetime

# ── Configuracion ─────────────────────────────────────────────────────────────
OUTPUT_ZIP = "Ticketia_Entrega_TFM.zip"
ROOT = os.path.dirname(os.path.abspath(__file__))

# Ficheros y carpetas a incluir (rutas relativas desde la raiz del repo)
INCLUDE = [
    # Codigo fuente principal
    "TICKETIA_PRO",
    # Scheduler (esta en la raiz, no dentro de TICKETIA_PRO)
    "run_scheduler.py",
    # Infraestructura Docker
    "Dockerfile",
    "docker-compose.yml",
    ".dockerignore",
    # Dependencias
    "requirements.txt",
    # Variables de entorno (plantilla, nunca el .env real)
    ".env.example",
    # Documentacion tecnica y academica
    "ARCHITECTURE_DEFENSE.md",
    "PROPUESTA_TFM_TICKETIA.md",
    # PDF de analisis para el tribunal (si existe)
    "TICKETIA_Analisis_Defensa_Academica.pdf",
]

# Directorios que se omiten al hacer walk recursivo
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.pytest_cache',
    'venv', 'env', '.venv',
    'backups', 'node_modules',
    # La BD local y uploads no se incluyen (son datos, no codigo)
    'instance', 'uploads', 'generated_docs',
    # Carpeta de test de Docker, ya cubierta por las instrucciones
    'test_docker',
}

# Extensiones y ficheros individuales que se omiten
EXCLUDE_FILES = {
    # Compilados Python
    '.pyc', '.pyo', '.pyd',
    # Logs
    '.log',
    # Bases de datos locales
    '.db', '.sqlite3',
    # Secretos — NUNCA en el ZIP
    '.env',
    # Credenciales OAuth/GCP que pueden estar en el repo local
    'client_secrets.json', 'token.json',
    # El propio ZIP anterior y scripts de empaquetado
    'Ticketia_Entrega_TFM.zip',
}

# Nombres de fichero exactos a excluir (independientemente de extension)
EXCLUDE_FILENAMES = {
    'zip_delivery.py',          # Este mismo script
    'generar_pdf_defensa.py',   # Script auxiliar para generar el PDF
    'ticketia-bot-3b7799d18ac9.json',  # Credencial GCP
    'client_secrets.json',
    'token.json',
    '.DS_Store',
    'Thumbs.db',
    # Scripts de debug/utilidad que no son parte de la entrega
    'fix_routes.py',
    'fix_template_urls.py',
    'refactor.py',
    'check_db_paths.py',
    'debug_db.py',
    'verify_exchange.py',
    'reset_db_full.py',
}


def should_exclude(path: str, name: str, is_dir: bool) -> bool:
    """Devuelve True si el fichero/directorio debe omitirse del ZIP."""
    if is_dir and name in EXCLUDE_DIRS:
        return True
    if not is_dir:
        if name in EXCLUDE_FILENAMES:
            return True
        _, ext = os.path.splitext(name)
        if ext in EXCLUDE_FILES:
            return True
        if name in EXCLUDE_FILES:
            return True
    return False


def add_to_zip(zipf: zipfile.ZipFile, path: str, arcname: str):
    """Anade un fichero o directorio (recursivo) al ZIP."""
    abs_path = os.path.join(ROOT, path)

    if not os.path.exists(abs_path):
        print(f"  [OMITIDO] {path} — no existe en este equipo")
        return

    if os.path.isfile(abs_path):
        if should_exclude(abs_path, os.path.basename(abs_path), False):
            return
        zipf.write(abs_path, arcname)
        size_kb = os.path.getsize(abs_path) / 1024
        print(f"  [+] {arcname:<60} ({size_kb:6.1f} KB)")
        return

    # Directorio: walk recursivo
    for dirpath, dirnames, filenames in os.walk(abs_path):
        # Filtrar subdirectorios en el walk (modifica en-lugar para que os.walk no entre)
        dirnames[:] = [
            d for d in dirnames
            if not should_exclude(dirpath, d, True)
        ]

        for filename in sorted(filenames):
            if should_exclude(dirpath, filename, False):
                continue

            full_file_path = os.path.join(dirpath, filename)
            # Ruta dentro del ZIP relativa a la raiz del repo
            relative_path = os.path.relpath(full_file_path, ROOT)
            # Normalizar separadores a /
            arc_path = relative_path.replace(os.sep, '/')

            size_kb = os.path.getsize(full_file_path) / 1024
            zipf.write(full_file_path, arc_path)
            print(f"  [+] {arc_path:<60} ({size_kb:6.1f} KB)")


def main():
    output_path = os.path.join(ROOT, OUTPUT_ZIP)

    print("=" * 70)
    print("  Ticketia — Generador de Paquete de Entrega TFM")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    print()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for item in INCLUDE:
            arcname = item.replace(os.sep, '/')
            add_to_zip(zipf, item, arcname)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)

    print()
    print("=" * 70)
    print(f"  ZIP generado: {OUTPUT_ZIP}")
    print(f"  Tamano:       {size_mb:.2f} MB")
    print()
    print("  Contenido del paquete:")
    print("   - Codigo fuente completo (TICKETIA_PRO/)")
    print("   - Infraestructura Docker (Dockerfile, docker-compose.yml)")
    print("   - Plantilla de variables de entorno (.env.example)")
    print("   - Documentacion tecnica (ARCHITECTURE_DEFENSE.md)")
    print("   - Propuesta TFM (PROPUESTA_TFM_TICKETIA.md)")
    print("   - PDF de analisis para defensa (si existe)")
    print()
    print("  Para ejecutar el paquete:")
    print("   1. Copiar .env.example a .env y rellenar las claves")
    print("   2. docker compose up --build")
    print("   3. Abrir http://localhost:5000")
    print("=" * 70)


if __name__ == "__main__":
    main()
