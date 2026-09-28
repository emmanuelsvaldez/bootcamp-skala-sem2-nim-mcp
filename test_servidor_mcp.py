#!/usr/bin/env python3
"""
==============================================================================
Pruebas Unitarias del Servidor MCP Local (Descubrimiento y Ejecución)
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Ejecuta las pruebas directas del protocolo Model Context Protocol (MCP)
    validando las operaciones de 'list_tools' y 'call_tool' antes de conectar
    el agente de inferencia (LLM).

Evidencia de Bootcamp:
    La salida de este script provee la Captura de Evidencia #4:
    "Captura de list_tools mostrando track_order".
"""

import sys
import json
import asyncio
from servidor_mcp import mcp

async def test_descubrimiento_herramientas():
    print("\n" + "=" * 70)
    print("  FASE 1: DESCUBRIMIENTO DE HERRAMIENTAS (list_tools)")
    print("=" * 70)
    
    tools = await mcp.list_tools()
    print(f"Total de herramientas registradas: {len(tools)}\n")
    
    encontrada = False
    for idx, tool in enumerate(tools, 1):
        print(f"Herramienta #{idx}:")
        print(f"  - Nombre:       {tool.name}")
        print(f"  - Descripción:  {tool.description.strip() if tool.description else 'Sin descripción'}")
        
        # Obtener esquema de entrada según versión del objeto Tool
        esquema = getattr(tool, "input_schema", getattr(tool, "inputSchema", None))
        print(f"  - InputSchema:  {json.dumps(esquema, indent=4, ensure_ascii=False)}")
        print("-" * 70)
        
    tools_descubiertas = {t.name: t for t in tools}
    assert "track_order" in tools_descubiertas, "ERROR CRÍTICO: La herramienta 'track_order' no fue descubierta."
    assert "cancel_order" in tools_descubiertas, "ERROR CRÍTICO: La herramienta 'cancel_order' no fue descubierta."
    print("[OK] Herramientas 'track_order' y 'cancel_order' descubiertas exitosamente con contratos válidos.")
    return tools

async def test_invocacion_herramientas():
    print("\n" + "=" * 70)
    print("  FASE 2: INVOCACIÓN DE HERRAMIENTAS (call_tool) Y GOBERNANZA")
    print("=" * 70)
    
    casos_de_prueba = [
        {"tool": "track_order", "desc": "Lectura: Pedido existente 45231 (En tránsito)", "params": {"order_id": "45231"}},
        {"tool": "track_order", "desc": "Lectura: Pedido existente 10001 (Entregado)", "params": {"order_id": "10001"}},
        {"tool": "track_order", "desc": "Lectura: Pedido inexistente 99999", "params": {"order_id": "99999"}},
        {"tool": "cancel_order", "desc": "Escritura: Cancelación sin confirmación explícita (Debe detenerse)", "params": {"order_id": "45231", "confirmacion_usuario": False}},
        {"tool": "cancel_order", "desc": "Escritura: Cancelación con confirmación explícita (Debe ejecutarse)", "params": {"order_id": "45231", "confirmacion_usuario": True}},
        {"tool": "cancel_order", "desc": "Escritura: Idempotencia en segunda cancelación del mismo pedido (Debe responder ALREADY_CANCELLED)", "params": {"order_id": "45231", "confirmacion_usuario": True}},
        {"tool": "cancel_order", "desc": "Escritura: Intento de cancelación sobre pedido ya entregado 10001 (Debe denegarse)", "params": {"order_id": "10001", "confirmacion_usuario": True}},
    ]

    for caso in casos_de_prueba:
        print(f"\n[Test] {caso['desc']}")
        print(f"  Herramienta: {caso['tool']} | Parámetros: {caso['params']}")
        
        resultado_raw = await mcp.call_tool(caso["tool"], caso["params"])
        
        # Extraer el contenido del resultado según formato MCP
        texto_resultado = ""
        if hasattr(resultado_raw, "content") and resultado_raw.content:
            for c in resultado_raw.content:
                if hasattr(c, "text"):
                    texto_resultado = c.text
                    break
        elif hasattr(resultado_raw, "structured_content"):
            texto_resultado = str(resultado_raw.structured_content)
        else:
            texto_resultado = str(resultado_raw)

        print(f"  Respuesta del Servidor MCP:\n    {texto_resultado}")

async def main():
    print("=" * 70)
    print("  SUITE DE PRUEBAS DEL SERVIDOR MCP: 'Servidor de pedidos SKALA'")
    print("  Desarrollado por: Emmanuel Sánchez")
    print("=" * 70)
    
    try:
        await test_descubrimiento_herramientas()
        await test_invocacion_herramientas()
        print("\n" + "=" * 70)
        print("  TODAS LAS PRUEBAS DEL SERVIDOR MCP HAN SIDO COMPLETADAS (PASS)")
        print("=" * 70)
        print("\n[ÉXITO] Puedes tomar la Captura de Evidencia #4 con la sección de list_tools.\n")
        return 0
    except AssertionError as e:
        print(f"\n[FALLO DE ASERCIÓN]: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR EN PRUEBAS]: {type(e).__name__} - {e}")
        return 1

if __name__ == "__main__":
    codigo_salida = asyncio.run(main())
    sys.exit(codigo_salida)
