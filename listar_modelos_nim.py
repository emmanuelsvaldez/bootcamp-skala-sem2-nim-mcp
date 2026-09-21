#!/usr/bin/env python3
"""
==============================================================================
Explorador del Catálogo de Modelos Oficiales de NVIDIA NIM
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Consulta el endpoint /v1/models de NVIDIA NIM utilizando la API Key
    almacenada en .env para listar y clasificar los modelos disponibles
    en la nube de NVIDIA en tiempo real.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import openai

# Forzar codificación UTF-8 en salida estándar para compatibilidad con Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Cargar variables de entorno
load_dotenv(Path(".env"))

def main():
    print("=" * 75)
    print("  CATALOGO DE MODELOS EN TIEMPO REAL: NVIDIA NIM (Cloud)")
    print("  Desarrollado por: Emmanuel Sanchez")
    print("=" * 75)

    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    if not api_key or api_key.startswith("nvapi-TU_API_KEY"):
        print("\n[ERROR] NVIDIA_API_KEY no configurada en el archivo .env")
        sys.exit(1)

    print(f"\nConsultando endpoint: {base_url}/models ...")
    
    try:
        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        respuesta_modelos = client.models.list()
        todos_los_modelos = [m.id for m in respuesta_modelos.data]
        
        print(f"Total de modelos registrados en la plataforma: {len(todos_los_modelos)}\n")

        # Clasificación por familias de arquitectura
        nemotron = [m for m in todos_los_modelos if "nemotron" in m.lower()]
        llama = [m for m in todos_los_modelos if "llama" in m.lower() and "nemotron" not in m.lower()]
        mistral = [m for m in todos_los_modelos if "mistral" in m.lower()]

        print("-" * 75)
        print(f"[+] Familia NVIDIA NEMOTRON (Enfoque Oficial Clase 3) [{len(nemotron)} modelos]:")
        print("-" * 75)
        for m in nemotron:
            print(f"  - {m}")

        print("\n" + "-" * 75)
        print(f"[+] Familia META LLAMA [{len(llama)} modelos]:")
        print("-" * 75)
        for m in llama[:10]:
            print(f"  - {m}")
        if len(llama) > 10:
            print(f"  ... y {len(llama) - 10} modelos Llama adicionales.")

        print("\n" + "-" * 75)
        print(f"[+] Familia MISTRAL AI [{len(mistral)} modelos]:")
        print("-" * 75)
        for m in mistral:
            print(f"  - {m}")

        print("\n" + "=" * 75)
        print(f"Modelo actualmente fijado en tu .env: {os.getenv('NVIDIA_MODEL', 'No definido')}")
        print("=" * 75)
        print("\nPara cambiar de modelo, copia cualquiera de los identificadores anteriores")
        print("y pegalo en la linea 'NVIDIA_MODEL=...' de tu archivo .env.\n")

    except openai.AuthenticationError:
        print("[ERROR 401] Tu API Key no es valida para consultar el catalogo.")
    except Exception as e:
        print(f"[ERROR]: {type(e).__name__} - {e}")

if __name__ == "__main__":
    main()
