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
PEDIDOS_DB_DEFAULT: Dict[str, Dict[str, Any]] = {
    "45231": {
        "order_id": "45231",
        "estado": "En tránsito",
        "monto_total": "$1,250.00 MXN",
        "fecha_estimada": "2026-09-25",
        "transportista": "DHL Express",
        "origen": "Centro de Distribución CDMX",
        "destino": "Guadalajara, JAL",
        "articulos": 2,
        "descripcion": "Cámaras de Seguridad Wi-Fi HD (Pack x2)"
    },
    "10001": {
        "order_id": "10001",
        "estado": "Entregado",
        "monto_total": "$890.00 MXN",
        "fecha_estimada": "2026-09-18",
        "transportista": "FedEx Priority",
        "origen": "Almacén Monterrey",
        "destino": "Monterrey, NL",
        "articulos": 1,
        "descripcion": "Sensor Inteligente de Movimiento Zigbee"
    }
}

PEDIDOS_DB: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in PEDIDOS_DB_DEFAULT.items()}

def reiniciar_db():
    """Restaura la base de datos de pedidos a su estado inicial para pruebas deterministas."""
    global PEDIDOS_DB
    PEDIDOS_DB = {k: dict(v) for k, v in PEDIDOS_DB_DEFAULT.items()}

# 3. Herramienta 1: LECTURA (Riesgo Bajo)
@mcp.tool(name="track_order")
def track_order(order_id: str) -> str:
    """
    Rastrear pedido / Track order status.
    Retrieves real-time shipping status, carrier, and estimated delivery date of a corporate order using its order ID (e.g. '45231', '10001').
    Call this tool whenever the user inquires about an order status, location, or delivery with an order ID.
    
    Args:
        order_id: Identificador único del pedido / Numeric order identifier string (e.g. '45231').
        
    Returns:
        JSON con los detalles del pedido o mensaje de error si no existe.
    """
    # Validación preventiva de entrada
    order_id_limpio = str(order_id).strip()
    if not order_id_limpio:
        return json.dumps({
            "error": "ParametroInvalido",
            "mensaje": "El campo 'order_id' no puede estar vacío."
        }, ensure_ascii=False)

    logger.info(f"[AUDITORÍA LECTURA] Consultando pedido: {order_id_limpio}")

    # Búsqueda en el sistema core
    pedido = PEDIDOS_DB.get(order_id_limpio)
    if pedido:
        return json.dumps({
            "encontrado": True,
            "tipo_operacion": "lectura",
            "datos": pedido
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "encontrado": False,
            "error": "No encontrado",
            "mensaje": f"El pedido '{order_id_limpio}' no existe en los registros del sistema.",
            "order_id": order_id_limpio
        }, ensure_ascii=False)


# 4. Herramienta 2: ESCRITURA (Riesgo Alto - Destructiva con Idempotencia)
@mcp.tool(name="cancel_order")
def cancel_order(order_id: str, motivo: str = "Solicitud de cliente", confirmacion_usuario: bool = False) -> str:
    """
    Cancelar pedido / Cancel order permanently.
    Cancela definitivamente un pedido corporativo e inicia el proceso de reembolso.
    
    Esta herramienta es de ESCRITURA, destructiva e irreversible.
    
    Usar esta herramienta ÚNICAMENTE cuando:
    1. El usuario haya solicitado cancelar un pedido específico y proporcione su ID.
    2. El agente ya haya consultado previamente los detalles con track_order y presentado el impacto al usuario.
    3. El usuario haya otorgado una confirmación explícita y textual en un turno posterior.
    
    NO usar esta herramienta:
    - En el mismo turno en el que el usuario solicita cancelar por primera vez.
    - Si el usuario solo pide informes del proceso de cancelación.
    - Si el pedido ya fue entregado (en cuyo caso procede devolución, no cancelación).
    - Si confirmacion_usuario no es True.
    
    Args:
        order_id: Identificador numérico del pedido a cancelar.
        motivo: Razón o justificación comercial de la cancelación.
        confirmacion_usuario: Certificación booleana de confirmación explícita del usuario.
        
    Returns:
        JSON con el resultado de la cancelación, auditoría y control estricto de idempotencia.
    """
    order_id_limpio = str(order_id).strip()
    if not order_id_limpio:
        return json.dumps({
            "error": "ParametroInvalido",
            "mensaje": "El campo 'order_id' no puede estar vacío para cancelar un pedido."
        }, ensure_ascii=False)

    logger.info(f"[AUDITORÍA ESCRITURA] Intento de cancelación para pedido: {order_id_limpio} | Confirmado: {confirmacion_usuario}")

    # Regla de Seguridad: Confirmación explícita requerida
    if not confirmacion_usuario:
        return json.dumps({
            "error": "RequiereConfirmacionExplicita",
            "mensaje": "Operación de escritura detenida. Se requiere confirmación explícita del usuario antes de ejecutar 'cancel_order'.",
            "order_id": order_id_limpio,
            "requiere_confirmacion": True
        }, ensure_ascii=False)

    # Verificar existencia en el sistema core
    pedido = PEDIDOS_DB.get(order_id_limpio)
    if not pedido:
        return json.dumps({
            "encontrado": False,
            "error": "No encontrado",
            "mensaje": f"No se puede cancelar el pedido '{order_id_limpio}' porque no existe en los registros.",
            "order_id": order_id_limpio
        }, ensure_ascii=False)

    # Regla de Negocio: Pedidos ya entregados no se pueden cancelar
    if pedido.get("estado") == "Entregado":
        return json.dumps({
            "error": "OperacionNoPermitida",
            "mensaje": f"El pedido '{order_id_limpio}' ya fue entregado y no admite cancelación directa. Debe iniciarse un proceso de devolución post-venta.",
            "estado_actual": "Entregado",
            "order_id": order_id_limpio
        }, ensure_ascii=False)

    # Regla de Arquitectura: CONTROL DE IDEMPOTENCIA
    # Si el pedido ya fue cancelado previamente, retornar éxito idempotente sin re-ejecutar efectos secundarios
    if pedido.get("estado") == "Cancelado":
        return json.dumps({
            "status": "ALREADY_CANCELLED",
            "idempotente": True,
            "order_id": order_id_limpio,
            "mensaje": f"El pedido '{order_id_limpio}' ya se encontraba cancelado previamente desde {pedido.get('fecha_cancelacion', 'fecha anterior')}. No se generaron cobros ni cambios adicionales.",
            "datos": pedido
        }, ensure_ascii=False)

    # Ejecución de la cancelación en el sistema
    pedido["estado"] = "Cancelado"
    pedido["fecha_cancelacion"] = "2026-09-27"
    pedido["motivo_cancelacion"] = motivo

    return json.dumps({
        "status": "CANCELLED_SUCCESSFULLY",
        "idempotente": False,
        "tipo_operacion": "escritura",
        "order_id": order_id_limpio,
        "mensaje": f"El pedido '{order_id_limpio}' ha sido cancelado exitosamente. Se ha emitido la orden de reembolso correspondiente al monto {pedido.get('monto_total', '$0.00 MXN')}.",
        "datos": pedido
    }, ensure_ascii=False)


if __name__ == "__main__":
    # Ejecución en modo stdio (comunicación estándar para hosts MCP)
    print("Iniciando 'Servidor de pedidos SKALA' (Desarrollado por Emmanuel Sánchez)...")
    mcp.run(transport="stdio")
