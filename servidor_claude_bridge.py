#!/usr/bin/env python3
"""
==============================================================================
Servidor Puente Claude CLI (OpenAI-Compatible Bridge)
Proyecto: Bootcamp SKALA - Semana 2 (Inferencia Híbrida & MCP)
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Expone un servidor HTTP local en el puerto 8000 compatible con la API de OpenAI
    (/v1/chat/completions) que traduce las peticiones agénticas y esquemas MCP
    hacia el cliente de terminal 'claude' (Claude Code CLI v2.1.229) autenticado.
    
    Permite utilizar Claude en el Workbench sin requerir ANTHROPIC_API_KEY directa.
"""

import sys
import io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import re
import subprocess
import time
from typing import Dict, Any, List, Optional
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
import uvicorn

PUERTO = 8000
HOST = "127.0.0.1"


def ejecutar_claude_cli(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Invoca la CLI local de Claude en modo headless (-p) con stdin=DEVNULL y strict-mcp-config."""
    cmd = [
        "claude", "-p", prompt,
        "--tools", "",
        "--strict-mcp-config",
        "--no-session-persistence"
    ]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    try:
        t0 = time.time()
        proceso = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60.0
        )
        latencia = time.time() - t0
        salida = proceso.stdout.strip()
        print(f"  [CLAUDE BRIDGE] Salida recibida en {latencia:.2f}s ({len(salida)} chars)")
        return salida
    except subprocess.TimeoutExpired:
        print("  [CLAUDE BRIDGE ERROR] Timeout ejecutando Claude CLI")
        return "Error: Timeout de ejecución en Claude CLI."
    except Exception as e:
        print(f"  [CLAUDE BRIDGE ERROR] Fallo invocando Claude CLI: {e}")
        return f"Error interno en bridge: {e}"


def formatear_contexto_y_tools(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> tuple[str, str]:
    """Construye el prompt consolidado e instrucciones de Tool Calling para Claude."""
    system_parts = []
    conversacion_parts = []

    for msg in messages:
        rol = msg.get("role", "user")
        contenido = msg.get("content", "")

        if rol == "system":
            system_parts.append(str(contenido))
        elif rol == "user":
            conversacion_parts.append(f"Usuario: {contenido}")
        elif rol == "assistant":
            # Si el asistente había propuesto una tool en el turno anterior
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    conversacion_parts.append(f"Asistente (Llamada a Herramienta ejecutada): {fn.get('name')}({fn.get('arguments')})")
            elif contenido:
                conversacion_parts.append(f"Asistente: {contenido}")
        elif rol == "tool":
            conversacion_parts.append(f"Resultado de Herramienta [{msg.get('name')}]: {contenido}")

    # Instrucciones de Tool Calling si hay herramientas disponibles
    tools_prompt = ""
    if tools:
        lineas_tools = []
        for t in tools:
            fn = t.get("function", {})
            nombre = fn.get("name", "")
            desc = fn.get("description", "").strip()
            props = fn.get("parameters", {}).get("properties", {})
            reqs = fn.get("parameters", {}).get("required", [])
            params_desc = []
            for p_name, p_info in props.items():
                req_flag = " (requerido)" if p_name in reqs else " (opcional)"
                params_desc.append(f"{p_name}: {p_info.get('type', 'any')}{req_flag} - {p_info.get('description', '')}")
            params_str = ", ".join(props.keys())
            lineas_tools.append(f"- {nombre}({params_str}): {desc}")
            if params_desc:
                for pd in params_desc:
                    lineas_tools.append(f"    * {pd}")

        tools_str = "\n".join(lineas_tools)
        tools_prompt = (
            f"\n\nHERRAMIENTAS CORPORATIVAS DISPONIBLES (FastMCP):\n"
            f"{tools_str}\n\n"
            f"REGLA DE INVOCACIÓN DE HERRAMIENTAS (Anthropic Messages API - Slide 8 y 9):\n"
            "Si determinas que debes invocar una herramienta para atender la consulta, responde ÚNICAMENTE con un bloque JSON en formato tool_use:\n"
            '{"type": "tool_use", "name": "<nombre_tool>", "input": {<argumentos>}}\n'
            "Ejemplo exacto:\n"
            '{"type": "tool_use", "name": "track_order", "input": {"order_id": "45231"}}\n\n'
            "IMPORTANTE:\n"
            "- NO agregues saludos ni explicaciones antes o después del bloque JSON al invocar herramientas.\n"
            "- Si NO requieres herramientas (o ya recibiste el resultado de una herramienta ejecutada previamente), redacta tu respuesta final directamente en español natural."
        )

    system_final = "\n\n".join(system_parts) + tools_prompt
    prompt_usuario_final = "\n\n".join(conversacion_parts)

    return prompt_usuario_final, system_final


def extraer_tool_call(texto: str) -> Optional[Dict[str, Any]]:
    """Extrae un tool call estructurado en formato bloque tool_use, XML <tool_call> o JSON."""
    texto_limpio = texto.strip()

    # 1. Remover posible envoltura markdown ```json ... ```
    if "```" in texto_limpio:
        match_code = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
        if match_code:
            try:
                data = json.loads(match_code.group(1))
                if data.get("type") == "tool_use" or "name" in data:
                    return {
                        "name": data.get("name"),
                        "arguments": data.get("input", data.get("arguments", {}))
                    }
            except Exception:
                pass

    # 2. Búsqueda de bloque tool_use nativo Anthropic (Slide 8)
    match_anthropic = re.search(r'\{\s*"type"\s*:\s*"tool_use"\s*,\s*"name"\s*:\s*"([^"]+)"\s*,\s*"input"\s*:\s*(\{.*?\})\s*\}', texto, re.DOTALL)
    if match_anthropic:
        try:
            return {
                "name": match_anthropic.group(1),
                "arguments": json.loads(match_anthropic.group(2))
            }
        except Exception:
            pass

    # 3. Búsqueda recursiva/incremental de JSON válido con type: tool_use o name + input
    for m in re.finditer(r"\{", texto):
        sub = texto[m.start():]
        for end_idx in range(len(sub), 2, -1):
            chunk = sub[:end_idx]
            if chunk.endswith("}"):
                try:
                    d = json.loads(chunk)
                    if isinstance(d, dict):
                        if d.get("type") == "tool_use" and "name" in d:
                            return {
                                "name": d.get("name"),
                                "arguments": d.get("input", d.get("arguments", {}))
                            }
                        elif "name" in d and ("input" in d or "arguments" in d):
                            return {
                                "name": d.get("name"),
                                "arguments": d.get("input", d.get("arguments", {}))
                            }
                    break
                except Exception:
                    continue

    # 4. Formato XML <tool_call>{...}</tool_call>
    match_xml = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", texto, re.DOTALL)
    if match_xml:
        try:
            d = json.loads(match_xml.group(1))
            name = d.get("name")
            args = d.get("arguments", d.get("input", {}))
            if name:
                return {"name": name, "arguments": args}
        except Exception:
            pass

    return None


async def endpoint_chat_completions(request: Request) -> JSONResponse:
    """Endpoint principal compatible con OpenAI POST /v1/chat/completions."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    messages = body.get("messages", [])
    tools = body.get("tools", [])
    modelo = body.get("model", "claude-code-cli")

    print(f"\n[CLAUDE BRIDGE] Petición recibida ({len(messages)} mensajes, {len(tools)} tools)")

    prompt_texto, system_prompt = formatear_contexto_y_tools(messages, tools)

    # Invocación a Claude CLI
    salida_claude = ejecutar_claude_cli(prompt_texto, system_prompt)

    # Detección de Tool Calling
    tool_call_data = extraer_tool_call(salida_claude)

    call_id = f"call_claude_{int(time.time()*1000)}"

    if tool_call_data and "name" in tool_call_data:
        nombre_tool = tool_call_data["name"]
        args = tool_call_data.get("arguments", {})
        args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else str(args)

        print(f"  [CLAUDE BRIDGE] Tool Call Detectada: {nombre_tool}({args_str})")

        mensaje_respuesta = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": nombre_tool,
                        "arguments": args_str
                    }
                }
            ]
        }
        finish_reason = "tool_calls"
    else:
        # Respuesta conversacional final
        mensaje_respuesta = {
            "role": "assistant",
            "content": salida_claude,
            "tool_calls": None
        }
        finish_reason = "stop"

    respuesta_openai = {
        "id": f"chatcmpl-claude-bridge-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": modelo,
        "choices": [
            {
                "index": 0,
                "message": mensaje_respuesta,
                "finish_reason": finish_reason
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt_texto) // 4,
            "completion_tokens": len(salida_claude) // 4,
            "total_tokens": (len(prompt_texto) + len(salida_claude)) // 4
        }
    }

    return JSONResponse(respuesta_openai)


async def endpoint_models(request: Request) -> JSONResponse:
    """Endpoint GET /v1/models para descubrimiento de modelos compatibles."""
    return JSONResponse({
        "object": "list",
        "data": [
            {"id": "claude-3-7-sonnet", "object": "model", "owned_by": "anthropic-cli-bridge"},
            {"id": "claude-code-cli", "object": "model", "owned_by": "anthropic-cli-bridge"}
        ]
    })


async def endpoint_health(request: Request) -> JSONResponse:
    """Endpoint GET /health para verificación de disponibilidad."""
    return JSONResponse({
        "status": "online",
        "service": "Claude Code CLI Bridge Server",
        "port": PUERTO,
        "version": "2.1.229"
    })


app = Starlette(
    debug=True,
    routes=[
        Route("/v1/chat/completions", endpoint_chat_completions, methods=["POST"]),
        Route("/v1/models", endpoint_models, methods=["GET"]),
        Route("/health", endpoint_health, methods=["GET"]),
        Route("/", endpoint_health, methods=["GET"]),
    ]
)

if __name__ == "__main__":
    print(f"==================================================================")
    print(f"🚀 Iniciando Servidor Puente Claude CLI en http://{HOST}:{PUERTO}")
    print(f"Compatible con OpenAI API (/v1/chat/completions y /v1/models)")
    print(f"Conectado a: Claude Code CLI (v2.1.229) [Sesión de Terminal Activa]")
    print(f"==================================================================")
    uvicorn.run(app, host=HOST, port=PUERTO, log_level="info")
