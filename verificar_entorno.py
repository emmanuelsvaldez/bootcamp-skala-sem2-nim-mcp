#!/usr/bin/env python3
"""
==============================================================================
Script de Diagnóstico y Validación de Entorno Enterprise
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Valida de manera integral que las herramientas, dependencias de Python,
    entornos virtuales y variables de configuración cumplan con los estándares
    de producción requeridos por el Bootcamp SKALA.

Regla de Seguridad:
    Este script NUNCA imprime secretos, tokens ni valores de API keys en consola.
"""

import sys
import os
from pathlib import Path

# Intentar importar librerías estándar o de diagnóstico inicial
try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None

def imprimir_banner():
    print("=" * 70)
    print("  BOOTCAMP SKALA - SEMANA 2: NIM, OLLAMA, MCP & SALESFORCE")
    print("  Diagnóstico del Entorno de Desarrollo (Enterprise Grade)")
    print("  Desarrollado por: Emmanuel Sánchez")
    print("=" * 70)

def verificar_python():
    print("\n[1] Verificando Versión de Python:")
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v.major == 3 and v.minor >= 10:
        print(f"  [OK] Versión instalada: Python {version_str} (Cumple requisito >= 3.10)")
        return True
    else:
        print(f"  [ERROR] Se requiere Python >= 3.10. Detectado: Python {version_str}")
        return False

def verificar_entorno_virtual():
    print("\n[2] Verificando Entorno Virtual Activo:")
    en_venv = (sys.prefix != sys.base_prefix) or ("VIRTUAL_ENV" in os.environ)
    if en_venv:
        venv_path = os.environ.get("VIRTUAL_ENV", sys.prefix)
        print(f"  [OK] Entorno virtual activo detectado en: {venv_path}")
        return True
    else:
        print("  [ADVERTENCIA] No estás dentro de un entorno virtual (.venv).")
        print("    Recomendación Enterprise: activa tu venv con 'source .venv/bin/activate' o '.venv\\Scripts\\Activate.ps1'.")
        return False

def verificar_paquetes():
    print("\n[3] Verificando Dependencias Críticas:")
    paquetes_requeridos = [
        ("openai", "openai"),
        ("python-dotenv", "dotenv"),
        ("mcp", "mcp"),
        ("httpx", "httpx"),
        ("pydantic", "pydantic"),
        ("rich", "rich"),
    ]
    todos_ok = True
    for nombre_pkg, modulo in paquetes_requeridos:
        try:
            __import__(modulo)
            print(f"  [OK] {nombre_pkg}: Disponible y operativo")
        except ImportError:
            print(f"  [FALTA] {nombre_pkg}: No instalado. Ejecuta 'pip install -r requirements.txt'")
            todos_ok = False
    return todos_ok

def verificar_configuracion_env():
    print("\n[4] Verificando Configuración de Variables de Entorno (.env):")
    env_file = Path(".env")
    if not env_file.exists():
        print("  [INFO] Archivo '.env' no encontrado todavía en el directorio de trabajo.")
        print("    Acción: Copia '.env.example' a '.env' y completa tus valores.")
        return False

    if dotenv_values is None:
        print("  [ADVERTENCIA] python-dotenv no está disponible para inspeccionar .env")
        return False

    config = dotenv_values(env_file)
    api_key = config.get("NVIDIA_API_KEY", "")
    base_url = config.get("NVIDIA_BASE_URL", "")
    model = config.get("NVIDIA_MODEL", "")
    provider = config.get("LLM_PROVIDER", "nvidia")

    print(f"  - Proveedor activo (LLM_PROVIDER): {provider}")

    # Verificación segura de API Key (sin imprimirla jamás)
    if api_key and api_key != "nvapi-TU_API_KEY_AQUI_PROPORCIONADA_POR_EL_INSTRUCTOR":
        prefijo = api_key[:6] + "..." if len(api_key) > 6 else "CONFIGURADA"
        print(f"  - NVIDIA_API_KEY: CONFIGURADA (Muestra segura: {prefijo})")
        api_ok = True
    else:
        print("  - NVIDIA_API_KEY: [FALTA o VALOR POR DEFECTO]")
        api_ok = False

    print(f"  - NVIDIA_BASE_URL: {base_url if base_url else '[FALTA]'}")
    print(f"  - NVIDIA_MODEL: {model if model else '[FALTA]'}")

    return api_ok and bool(base_url) and bool(model)

def verificar_seguridad_git():
    print("\n[5] Verificación de Seguridad Zero-Trust (.gitignore):")
    gitignore = Path(".gitignore")
    if gitignore.exists():
        contenido = gitignore.read_text(encoding="utf-8")
        if ".env" in contenido:
            print("  [OK] '.env' está correctamente registrado y protegido en .gitignore.")
            return True
        else:
            print("  [CRÍTICO] '.env' NO está en .gitignore. ¡Existe riesgo de fuga de credenciales!")
            return False
    else:
        print("  [ADVERTENCIA] No existe archivo .gitignore en este directorio.")
        return False

def main():
    imprimir_banner()
    ok_py = verificar_python()
    ok_venv = verificar_entorno_virtual()
    ok_pkg = verificar_paquetes()
    ok_env = verificar_configuracion_env()
    ok_git = verificar_seguridad_git()

    print("\n" + "=" * 70)
    print("RESUMEN DEL DIAGNÓSTICO:")
    print(f"  Python Base:       {'APROBADO' if ok_py else 'REQUIERE ATENCIÓN'}")
    print(f"  Entorno Virtual:   {'ACTIVO' if ok_venv else 'NO ACTIVO'}")
    print(f"  Dependencias:      {'COMPLETAS' if ok_pkg else 'PENDIENTES DE INSTALACIÓN'}")
    print(f"  Configuración ENV: {'LISTA' if ok_env else 'PENDIENTE'}")
    print(f"  Seguridad Git:     {'PROTEGIDO' if ok_git else 'VULNERABLE'}")
    print("=" * 70)

    if ok_py and ok_pkg and ok_git:
        print("Estado general del entorno: LISTO PARA LA PRÁCTICA.\n")
        return 0
    else:
        print("Estado general del entorno: ACCIONES REQUERIDAS ANTES DE CONTINUAR.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
