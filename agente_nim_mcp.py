#!/usr/bin/env python3
"""
==============================================================================
Agente Orquestador Enterprise: Inferencia (NIM / Ollama) + Protocolo MCP
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Implementa el ciclo de vida completo de un agente inteligente desacoplado:
    1. Descubre herramientas en el servidor MCP local.
    2. Convierte contratos MCP al estándar OpenAPI / OpenAI Tools.
    3. Envía la conversación al LLM (NVIDIA NIM u Ollama según configuración).
    4. Detecta 'tool_calls' y valida contra una Allowlist estricta.
    5. Ejecuta la herramienta en el servidor MCP y reinyecta el resultado.
    6. Retorna la respuesta final al usuario, acotado a 3 iteraciones como máximo.

Controles de Seguridad Obligatorios (Rúbrica SKALA):
    - Allowlist de herramientas autorizadas (Zero-Trust).
    - Prevención de bucles infinitos (Límite estricto de 3 iteraciones).
    - Protección contra alucinaciones cuando la herramienta no encuentra datos.
    - Ocultación total de tokens y variables de credenciales.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import openai

# Importar el servidor MCP local para ejecución en proceso
from servidor_mcp import mcp

# Cargar variables de entorno
load_dotenv(Path(".env"))

# ==============================================================================
# 1. POLÍTICAS DE SEGURIDAD Y CONFIGURACIÓN ENTERPRISE
# ==============================================================================
ALLOWLIST_TOOLS = {"track_order"}
MAX_ITERACIONES = 3
TIMEOUT_SEGUNDOS = 45.0

class LLMProviderFactory:
    """Fábrica para desacoplar el proveedor de inferencia (NVIDIA NIM vs Ollama)."""
    @staticmethod
    def crear_cliente():
        proveedor = os.getenv("LLM_PROVIDER", "nvidia").lower().strip()

        if proveedor == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
            api_key = "ollama"  # Ollama no requiere clave real
            modelo = os.getenv("OLLAMA_MODEL", "llama3-groq-tool-use:8b")
            nombre_display = "Ollama Local (Offline Runtime)"
        else:
            base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            api_key = os.getenv("NVIDIA_API_KEY", "")
            modelo = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
            nombre_display = "NVIDIA NIM Cloud API"

        if proveedor == "nvidia" and (not api_key or api_key.startswith("nvapi-TU_API_KEY")):
            raise ValueError("NVIDIA_API_KEY no configurada válidamente en el archivo .env")

        cliente = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=TIMEOUT_SEGUNDOS)
        return cliente, modelo, proveedor, nombre_display


class AgenteOrquestadorMCP:
    """Orquestador agéntico con control de bucle y gobernanza de herramientas."""

    def __init__(self):
        self.cliente, self.modelo, self.proveedor, self.nombre_display = LLMProviderFactory.crear_cliente()
        self.herramientas_mcp: List[Any] = []
        self.herramientas_openai: List[Dict[str, Any]] = []

    async def inicializar_mcp(self):
        """Descubre las herramientas del servidor MCP y las adapta al formato OpenAI."""
        self.herramientas_mcp = await mcp.list_tools()
        self.herramientas_openai = []

        for tool in self.herramientas_mcp:
            esquema = getattr(tool, "input_schema", getattr(tool, "inputSchema", {}))
            self.herramientas_openai.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description.strip() if tool.description else "",
                    "parameters": esquema
                }
            })

    async def ejecutar_herramienta_segura(self, nombre_tool: str, argumentos: Dict[str, Any]) -> str:
        """Aplica la Allowlist y ejecuta la tool en el servidor MCP."""
        # 1. Control de seguridad: Allowlist
        if nombre_tool not in ALLOWLIST_TOOLS:
            error_msg = f"ACCESO DENEGADO: La herramienta '{nombre_tool}' no está en la Allowlist autorizada."
            print(f"  [SEGURIDAD] {error_msg}")
            return json.dumps({"error": "ToolNoAutorizada", "mensaje": error_msg}, ensure_ascii=False)

        print(f"  [MCP EXEC] Invocando '{nombre_tool}' en Servidor MCP con: {argumentos}")

        try:
            resultado_raw = await mcp.call_tool(nombre_tool, argumentos)
            
            # Formatear el contenido devuelto por MCP
            if hasattr(resultado_raw, "content") and resultado_raw.content:
                for item in resultado_raw.content:
                    if hasattr(item, "text"):
                        return item.text
            elif hasattr(resultado_raw, "structured_content"):
                return json.dumps(resultado_raw.structured_content, ensure_ascii=False)
            
            return str(resultado_raw)
        except Exception as e:
            error_msg = f"Error durante la ejecución en el Servidor MCP: {str(e)}"
            print(f"  [MCP ERROR] {error_msg}")
            return json.dumps({"error": "FalloServidorMCP", "detalle": error_msg}, ensure_ascii=False)

    async def consultar(self, pregunta_usuario: str) -> str:
        """
        Ejecuta el ciclo de vida del agente:
        Prompt -> LLM -> Tool Call Proposal -> MCP Validation -> Tool Execution -> Final Response
        """
        mensajes: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Eres un agente empresarial de atención logística desarrollado por Emmanuel Sánchez. "
                    "Tienes acceso a herramientas corporativas a través de Model Context Protocol (MCP). "
                    "Reglas estrictas:\n"
                    "1. Para consultar pedidos, invoca la herramienta 'track_order' pasando 'order_id'.\n"
                    "2. Si el usuario no proporciona el número de pedido, SOLICITA el número amablemente sin inventar ninguno ni llamar herramientas.\n"
                    "3. Si la herramienta indica que el pedido no fue encontrado, comunica la verdad; NUNCA inventes información de entrega ni transportistas.\n"
                    "4. Responde siempre en español con tono profesional y ejecutivo."
                )
            },
            {"role": "user", "content": pregunta_usuario}
        ]

        iteracion = 0
        while iteracion < MAX_ITERACIONES:
            iteracion += 1
            print(f"\n---> Iteración del Agente #{iteracion}/{MAX_ITERACIONES} [{self.nombre_display}]")

            try:
                # Invocación al LLM con las definiciones de herramientas
                kwargs = {
                    "model": self.modelo,
                    "messages": mensajes,
                    "temperature": 0.1
                }
                if self.herramientas_openai:
                    kwargs["tools"] = self.herramientas_openai
                    kwargs["tool_choice"] = "auto"

                respuesta = self.cliente.chat.completions.create(**kwargs)
                mensaje_asistente = respuesta.choices[0].message
                mensajes.append(mensaje_asistente)

                # Verificar si el modelo solicitó una llamada a herramienta
                if mensaje_asistente.tool_calls:
                    for tool_call in mensaje_asistente.tool_calls:
                        func_name = tool_call.function.name
                        print(f"  [LLM PROPUESTA] Herramienta: '{func_name}'")
                        
                        try:
                            args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            args = {}

                        # Ejecución en el servidor MCP
                        resultado_tool = await self.ejecutar_herramienta_segura(func_name, args)
                        print(f"  [MCP RETORNO] Resultado: {resultado_tool}")

                        # Inyectar el resultado de la herramienta a la conversación
                        mensajes.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": resultado_tool
                        })
                    
                    # Continúa el ciclo para que el modelo redacte la respuesta final
                    continue
                else:
                    # El modelo ha producido la respuesta en lenguaje natural
                    contenido_final = mensaje_asistente.content or ""
                    return contenido_final

            except Exception as e:
                return f"[ERROR DEL AGENTE]: {type(e).__name__} - {str(e)}"

        return "[AVISO]: Se alcanzó el límite máximo de iteraciones de seguridad (3) sin concluir."


async def ejecutar_suite_demostracion():
    """Ejecuta los escenarios obligatorios de la rúbrica SKALA."""
    print("=" * 80)
    print("  EJECUCIÓN DE SUITE DE PRUEBAS DEL AGENTE (NIM/OLLAMA + MCP)")
    print("  Desarrollado por: Emmanuel Sánchez")
    print("=" * 80)

    agente = AgenteOrquestadorMCP()
    await agente.inicializar_mcp()

    escenarios = [
        {
            "id": "1",
            "titulo": "Escenario: Pedido Válido (45231)",
            "prompt": "Hola, ¿podrías informarme cuál es el estado de mi pedido 45231?"
        },
        {
            "id": "2",
            "titulo": "Escenario: Pedido Faltante (Sin identificador)",
            "prompt": "Hola, quiero saber cuándo llega mi paquete que pedí la semana pasada."
        },
        {
            "id": "3",
            "titulo": "Escenario: Pedido Inexistente (99999)",
            "prompt": "Por favor revisa el estatus del pedido 99999."
        }
    ]

    for esc in escenarios:
        print("\n" + "=" * 80)
        print(f"  {esc['titulo']}")
        print("=" * 80)
        print(f"Usuario: \"{esc['prompt']}\"")
        respuesta = await agente.consultar(esc["prompt"])
        print("\nRespuesta Final del Agente:")
        print(f"  {respuesta.strip()}")


if __name__ == "__main__":
    asyncio.run(ejecutar_suite_demostracion())
