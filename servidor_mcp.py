#!/usr/bin/env python3
"""
==============================================================================
Servidor MCP Local: Servidor de pedidos SKALA
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Implementa un servidor local bajo el estándar Model Context Protocol (MCP)
    utilizando el SDK oficial de MCP para Python. Expone herramientas de negocio
    gobernadas y fuertemente tipadas para ser consumidas por agentes inteligentes.

Arquitectura:
    El servidor no conoce qué modelo de lenguaje lo invocará (NIM, Ollama o Agentforce).
    Únicamente expone contratos de herramientas y ejecuta la lógica de negocio
    autorizada bajo el principio de mínimo privilegio (operaciones de solo lectura).
"""

import json
import logging
from typing import Dict, Any

# Compatibilidad transparente entre versiones del SDK oficial de MCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server import MCPServer as FastMCP

# Configuración de logging institucional
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("servidor_mcp_skala")

# 1. Inicialización del servidor con nombre descriptivo según la rúbrica
mcp = FastMCP("Servidor de pedidos SKALA")

# 2. Base de datos simulada en memoria (Mock empresarial para pruebas)
PEDIDOS_DB: Dict[str, Dict[str, Any]] = {
    "45231": {
        "order_id": "45231",
        "estado": "En tránsito",
        "fecha_estimada": "2026-09-25",
        "transportista": "DHL Express",
        "origen": "Centro de Distribución CDMX",
        "destino": "Guadalajara, JAL",
        "articulos": 2
    },
    "10001": {
        "order_id": "10001",
        "estado": "Entregado",
        "fecha_estimada": "2026-09-18",
        "transportista": "FedEx Priority",
        "origen": "Almacén Monterrey",
        "destino": "Monterrey, NL",
        "articulos": 1
    }
}

# 3. Publicación de herramienta de solo lectura con validación estricta
@mcp.tool(name="track_order")
def track_order(order_id: str) -> str:
    """
    Consulta el estado y fecha estimada de un pedido corporativo a partir de su número.
    
    Usar esta herramienta ÚNICAMENTE cuando el usuario proporcione un identificador o número
    específico de pedido (por ejemplo '45231' o '10001'). No inventes números de pedido.
    
    Args:
        order_id: Identificador único del pedido (cadena numérica o alfanumérica).
        
    Returns:
        JSON serializable con los detalles del pedido o un mensaje de error si no existe.
    """
    # Validación preventiva de entrada
    order_id_limpio = str(order_id).strip()
    if not order_id_limpio:
        return json.dumps({
            "error": "ParametroInvalido",
            "mensaje": "El campo 'order_id' no puede estar vacío."
        }, ensure_ascii=False)

    logger.info(f"Procesando consulta para el pedido: {order_id_limpio}")

    # Búsqueda en el sistema core
    pedido = PEDIDOS_DB.get(order_id_limpio)
    if pedido:
        return json.dumps({
            "encontrado": True,
            "datos": pedido
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "encontrado": False,
            "error": "No encontrado",
            "mensaje": f"El pedido '{order_id_limpio}' no existe en los registros del sistema.",
            "order_id": order_id_limpio
        }, ensure_ascii=False)

if __name__ == "__main__":
    # Ejecución en modo stdio (comunicación estándar para hosts MCP)
    print("Iniciando 'Servidor de pedidos SKALA' (Desarrollado por Emmanuel Sánchez)...")
    mcp.run(transport="stdio")
