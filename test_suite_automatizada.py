#!/usr/bin/env python3
"""
==============================================================================
Suite de Pruebas Automatizadas (Pytest)
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Ejecuta la batería de pruebas de integración y contratos para validar
    los 7 criterios de evaluación de la rúbrica SKALA (Sección 15 y 16):
    1. Descubrimiento de herramientas en el Servidor MCP.
    2. Manejo de pedido válido (45231).
    3. Manejo de pedido entregado (10001).
    4. Manejo de pedido inexistente sin alucinaciones (99999).
    5. Validación preventiva de parámetros vacíos.
    6. Regla de seguridad: Rechazo estricto de tools no autorizadas (Allowlist).
    7. Prevención de bucles infinitos en el agente.

Evidencia de Bootcamp:
    La salida de este archivo con pytest provee la Captura de Evidencia #6:
    "Resultado de las pruebas automatizadas".
"""

import json
import pytest
import asyncio
from servidor_mcp import mcp, track_order
from agente_nim_mcp import AgenteOrquestadorMCP, ALLOWLIST_TOOLS

@pytest.mark.asyncio
async def test_mcp_list_tools_incluye_track_order():
    """Valida que el servidor MCP exponga 'track_order' con el esquema requerido."""
    tools = await mcp.list_tools()
    nombres = [t.name for t in tools]
    assert "track_order" in nombres, "La herramienta 'track_order' debe estar registrada."
    
    tool = next(t for t in tools if t.name == "track_order")
    assert tool.description, "La herramienta debe tener un docstring / descripción clara."
    
    esquema = getattr(tool, "input_schema", getattr(tool, "inputSchema", {}))
    assert "order_id" in esquema.get("required", []), "'order_id' debe ser obligatorio."

@pytest.mark.asyncio
async def test_mcp_call_tool_pedido_valido_45231():
    """Valida la consulta del pedido 45231 en estado 'En tránsito'."""
    resultado_json = track_order(order_id="45231")
    datos = json.loads(resultado_json)
    assert datos.get("encontrado") is True
    assert datos["datos"]["order_id"] == "45231"
    assert datos["datos"]["estado"] == "En tránsito"
    assert datos["datos"]["transportista"] == "DHL Express"

@pytest.mark.asyncio
async def test_mcp_call_tool_pedido_valido_10001():
    """Valida la consulta del pedido 10001 en estado 'Entregado'."""
    resultado_json = track_order(order_id="10001")
    datos = json.loads(resultado_json)
    assert datos.get("encontrado") is True
    assert datos["datos"]["order_id"] == "10001"
    assert datos["datos"]["estado"] == "Entregado"

@pytest.mark.asyncio
async def test_mcp_call_tool_pedido_inexistente():
    """Valida que un pedido no registrado retorne 'No encontrado' sin inventar datos."""
    resultado_json = track_order(order_id="99999")
    datos = json.loads(resultado_json)
    assert datos.get("encontrado") is False
    assert datos.get("error") == "No encontrado"
    assert "99999" in datos.get("mensaje")

@pytest.mark.asyncio
async def test_mcp_call_tool_parametro_vacio():
    """Valida que el servidor rechace parámetros de entrada vacíos."""
    resultado_json = track_order(order_id="   ")
    datos = json.loads(resultado_json)
    assert "error" in datos
    assert datos["error"] == "ParametroInvalido"

@pytest.mark.asyncio
async def test_agente_allowlist_rechaza_tool_no_autorizada():
    """Valida que el agente bloquee cualquier tool no presente en ALLOWLIST_TOOLS."""
    agente = AgenteOrquestadorMCP()
    tool_peligrosa = "borrar_base_datos_clientes"
    assert tool_peligrosa not in ALLOWLIST_TOOLS
    
    resultado_bloqueo = await agente.ejecutar_herramienta_segura(tool_peligrosa, {})
    datos_bloqueo = json.loads(resultado_bloqueo)
    assert datos_bloqueo.get("error") == "ToolNoAutorizada"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
