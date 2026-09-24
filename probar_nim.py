#!/usr/bin/env python3
"""
==============================================================================
Prueba Unitaria de Conectividad con NVIDIA NIM (Inferencia Directa sin Agente)
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Valida la comunicación HTTPS y la inferencia directa contra la API de
    NVIDIA NIM (https://integrate.api.nvidia.com/v1) antes de introducir MCP
    o lógica de agentes.

Reglas de Seguridad y Rúbrica:
    - NUNCA imprime la API key en consola.
    - Maneja explícitamente códigos HTTP: 401, 403, 404, 429 y Timeouts.
    - Lee de forma desacoplada la configuración desde el archivo .env.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import openai

# Cargar variables de entorno desde .env
load_dotenv(Path(".env"))

def main():
    print("=" * 70)
    print("  PRUEBA DE CONECTIVIDAD E INFERENCIA DIRECTA: NVIDIA NIM")
    print("  Desarrollado por: Emmanuel Sánchez")
    print("=" * 70)

    # 1. Extracción desacoplada de configuración
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("NVIDIA_MODEL")

    # Validación preventiva de variables requeridas
    if not api_key or api_key.startswith("nvapi-TU_API_KEY"):
        print("\n[ERROR DE CONFIGURACIÓN]")
        print("  La variable 'NVIDIA_API_KEY' no está configurada correctamente en el archivo .env.")
        print("  Acción: Edita .env y añade tu clave autorizada proporcionada por el instructor.")
        sys.exit(1)

    if not model:
        print("\n[ERROR DE CONFIGURACIÓN]")
        print("  La variable 'NVIDIA_MODEL' está vacía en el archivo .env.")
        sys.exit(1)

    print("\n[1] Parámetros de la Prueba:")
    print(f"  - Endpoint Base: {base_url}")
    print(f"  - Modelo Solicitado: {model}")
    print(f"  - API Key: CONFIGURADA (Longitud: {len(api_key)} caracteres, oculta por seguridad)")
    print(f"  - Temperature: 0.2 | Max Tokens: 150")

    # 2. Inicialización del cliente oficial de OpenAI adaptado a NVIDIA NIM
    client = openai.OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=30.0  # Timeout preventivo de red de 30 segundos
    )

    # 3. Preparación de los mensajes (Prueba sin herramientas)
    mensajes = [
        {
            "role": "system",
            "content": "Eres un asistente de arquitectura de software técnico, conciso y preciso."
        },
        {
            "role": "user",
            "content": "¿Qué es Model Context Protocol (MCP) y cuál es su principal ventaja en una oración?"
        }
    ]

    print("\n[2] Enviando solicitud a NVIDIA NIM...")
    inicio = time.perf_counter()

    try:
        respuesta = client.chat.completions.create(
            model=model,
            messages=mensajes,
            temperature=0.2,
            max_tokens=150
        )
        fin = time.perf_counter()
        latencia = fin - inicio

        contenido = respuesta.choices[0].message.content.strip()
        tokens_usados = respuesta.usage.total_tokens if respuesta.usage else "N/A"

        print("\n" + "=" * 70)
        print("  RESULTADO DE LA INFERENCIA EXITOSA (NVIDIA NIM)")
        print("=" * 70)
        print(f"Respuesta del Modelo:\n\n{contenido}\n")
        print("-" * 70)
        print(f"Métricas de Ejecución:")
        print(f"  - Tiempo de Respuesta (Latencia): {latencia:.2f} segundos")
        print(f"  - Total de Tokens Procesados:     {tokens_usados}")
        print(f"  - Estado de Conexión:             200 OK")
        print("=" * 70)
        print("\n[ÉXITO] NVIDIA NIM responde con el modelo autorizado.")
        print("Puedes tomar la Captura de Evidencia correspondiente a la Prueba NIM.\n")
        return 0

    except openai.AuthenticationError as e:
        print("\n[ERROR 401 - AUTENTICACIÓN FALLIDA]")
        print("  Causa: La API key de NVIDIA es inválida, expiró o fue revocada.")
        print("  Acción: Genera o copia nuevamente tu clave desde https://build.nvidia.com y actualiza .env.")
        print(f"  Detalle técnico: {e.message if hasattr(e, 'message') else str(e)}")
        return 1

    except openai.PermissionDeniedError as e:
        print("\n[ERROR 403 - PERMISO DENEGADO]")
        print("  Causa: Tu cuenta no tiene permisos para utilizar el modelo configurado.")
        print("  Acción: Revisa en build.nvidia.com si el modelo requiere aceptar términos específicos.")
        print(f"  Detalle técnico: {e.message if hasattr(e, 'message') else str(e)}")
        return 1

    except openai.NotFoundError as e:
        print("\n[ERROR 404 - RECURSO O MODELO NO ENCONTRADO]")
        print(f"  Causa: El modelo '{model}' o el endpoint '{base_url}' no existen.")
        print("  Acción: Copia el identificador exacto del modelo desde https://build.nvidia.com y colócalo en .env.")
        print(f"  Detalle técnico: {e.message if hasattr(e, 'message') else str(e)}")
        return 1

    except openai.RateLimitError as e:
        print("\n[ERROR 429 - LÍMITE DE CUOTA EXCEDIDO]")
        print("  Causa: Se ha alcanzado el límite de llamadas por minuto o cuota de la cuenta.")
        print("  Acción: Espera un momento antes de volver a solicitar o reduce la frecuencia de peticiones.")
        return 1

    except openai.APITimeoutError:
        print("\n[ERROR DE TIMEOUT - TIEMPO DE ESPERA AGOTADO]")
        print("  Causa: El servidor de NVIDIA tardó más de 30 segundos en responder.")
        print("  Acción: Verifica la calidad de tu conexión a internet o reintenta la solicitud.")
        return 1

    except openai.APIConnectionError as e:
        print("\n[ERROR DE CONEXIÓN]")
        print("  Causa: No fue posible establecer comunicación con el host de NVIDIA.")
        print("  Acción: Verifica tu acceso a internet, firewall o proxies de red.")
        print(f"  Detalle técnico: {str(e)}")
        return 1

    except Exception as e:
        print(f"\n[ERROR INESPERADO]: {type(e).__name__} - {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
