#!/usr/bin/env python3
"""
==============================================================================
SKALA Agentic Developer Workbench & MCP Inspector
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import streamlit as st
import httpx
from dotenv import load_dotenv
import openai

# Asegurar carga de variables locales
load_dotenv(Path(".env"))

# Importar servidor MCP
from servidor_mcp import mcp

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILO ENTERPRISE
# ==============================================================================
st.set_page_config(
    page_title="SKALA Agentic Workbench - Emmanuel Sánchez",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00d26a;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #8892b0;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #111927;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .stCodeBlock {
        border-radius: 8px;
    }
    .badge-cloud {
        background-color: #1e3a8a;
        color: #93c5fd;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-local {
        background-color: #064e3b;
        color: #6ee7b7;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# UTILIDADES ASÍNCRONAS Y DESCUBRIMIENTO DE MODELOS
# ==============================================================================
def run_async_safe(coro, timeout=45):
    """Ejecuta corrutinas de forma segura en un hilo aislado sin bloquear Streamlit."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(coro))
        return future.result(timeout=timeout)


@st.cache_data(ttl=10)
def obtener_modelos_ollama() -> List[Dict[str, Any]]:
    """
    Consulta los modelos locales disponibles en Ollama y EXCLUYE
    modelos mayores a 6 GB (filtrando el modelo de 9.6 GB gemma4:e4b).
    """
    url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").replace("/v1", "") + "/api/tags"
    modelos_filtrados = []
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("models", []):
                    size_gb = m.get("size", 0) / (1024 ** 3)
                    # Filtro solicitado: descartar modelos pesados de ~9 GB
                    if size_gb < 6.0:
                        modelos_filtrados.append({
                            "name": m.get("name"),
                            "size_gb": f"{size_gb:.1f} GB",
                            "modified": m.get("modified_at", "")[:10]
                        })
    except Exception:
        pass
    return modelos_filtrados


MODELOS_NIM_CONOCIDOS = [
    "nvidia/nemotron-3-ultra-550b-a55b",
    "meta/llama-3.1-70b-instruct",
    "mistralai/mixtral-8x7b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct"
]


# ==============================================================================
# MOTOR DEL AGENTE INTERACTIVO
# ==============================================================================
class AgenteWorkbenchEngine:
    def __init__(self, proveedor: str, modelo: str, temperature: float, max_tokens: int):
        self.proveedor = proveedor
        self.modelo = modelo
        self.temperature = temperature
        self.max_tokens = max_tokens

        if proveedor == "ollama":
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
            self.api_key = "ollama"
        else:
            self.base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            self.api_key = os.getenv("NVIDIA_API_KEY", "")

        self.cliente = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=45.0
        )

    async def ejecutar_consulta(self, prompt_usuario: str) -> Dict[str, Any]:
        """Ejecuta el ciclo de vida del agente capturando la traza de auditoría."""
        inicio = time.time()
        trazas = []
        tools_mcp = await mcp.list_tools()
        tools_openai = []

        for tool in tools_mcp:
            esquema = getattr(tool, "input_schema", getattr(tool, "inputSchema", {}))
            tools_openai.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description.strip() if tool.description else "",
                    "parameters": esquema
                }
            })

        mensajes = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente logístico corporativo desarrollado por Emmanuel Sánchez. "
                    "Tienes acceso a la herramienta 'track_order' para consultar información de pedidos. "
                    "Reglas obligatorias:\n"
                    "1. Siempre que el usuario pregunte por el estado de un pedido y proporcione un número o ID (ej. 45231, 99999), DEBES llamar obligatoriamente a la herramienta 'track_order'.\n"
                    "2. Si el usuario NO proporciona un número de pedido, pídeselo cordialmente en español SIN llamar a ninguna herramienta.\n"
                    "3. Cuando la herramienta indique que el pedido no fue encontrado, informa al usuario con la verdad; NUNCA inventes información.\n"
                    "4. Responde siempre en español de manera profesional, clara y concisa."
                )
            },
            {"role": "user", "content": prompt_usuario}
        ]

        iteracion = 0
        total_tokens = 0
        respuesta_final = ""

        while iteracion < 3:
            iteracion += 1
            iter_trace = {"iteracion": iteracion, "tool_calls": []}

            resp = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=mensajes,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=tools_openai,
                tool_choice="auto"
            )

            if hasattr(resp, "usage") and resp.usage:
                total_tokens += resp.usage.total_tokens

            msg_asistente = resp.choices[0].message
            mensajes.append(msg_asistente)

            if msg_asistente.tool_calls:
                for tc in msg_asistente.tool_calls:
                    func_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}

                    # Ejecución protegida en FastMCP
                    if func_name == "track_order":
                        mcp_res = await mcp.call_tool(func_name, args)
                        res_texto = ""
                        if hasattr(mcp_res, "content") and mcp_res.content:
                            for item in mcp_res.content:
                                if hasattr(item, "text"):
                                    res_texto = item.text
                        elif hasattr(mcp_res, "structured_content"):
                            res_texto = json.dumps(mcp_res.structured_content, ensure_ascii=False)
                        else:
                            res_texto = str(mcp_res)
                    else:
                        res_texto = json.dumps({"error": "ToolNoAutorizada", "mensaje": "Herramienta fuera de Allowlist"})

                    iter_trace["tool_calls"].append({
                        "id": tc.id,
                        "herramienta": func_name,
                        "argumentos": args,
                        "retorno_mcp": res_texto
                    })

                    mensajes.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": func_name,
                        "content": res_texto
                    })

                trazas.append(iter_trace)
                continue
            else:
                respuesta_final = msg_asistente.content or ""
                trazas.append(iter_trace)
                break

        latencia = time.time() - inicio
        return {
            "respuesta": respuesta_final,
            "trazas": trazas,
            "latencia": latencia,
            "tokens": total_tokens,
            "iteraciones": iteracion
        }


# ==============================================================================
# BARRA LATERAL (SIDEBAR DE CONTROL DE INFRAESTRUCTURA)
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Control de Infraestructura")
    st.caption("Arquitectura Híbrida: Cloud NIM ↔ Local Ollama")

    # 1. Selector de Proveedor
    proveedor_sel = st.radio(
        "Proveedor Activo:",
        ["☁️ NVIDIA NIM (Cloud)", "💻 Ollama (Local)"],
        index=0,
        help="Conmuta en caliente entre inferencia remota en la nube o local a costo $0."
    )
    es_local = "Ollama" in proveedor_sel
    proveedor_id = "ollama" if es_local else "nvidia"

    st.markdown("---")

    # 2. Selector de Modelo Dinámico
    if es_local:
        st.markdown("### 📦 Modelos Locales (< 6 GB)")
        modelos_locales = obtener_modelos_ollama()
        if modelos_locales:
            nombres = [m["name"] for m in modelos_locales]
            idx_def = nombres.index("llama3-groq-tool-use:8b") if "llama3-groq-tool-use:8b" in nombres else 0
            modelo_elegido = st.selectbox("Selecciona Modelo:", nombres, index=idx_def)
            st.caption("💡 Se excluyó automáticamente el modelo de 9.6 GB para proteger la VRAM.")
        else:
            st.warning("⚠️ No se detectó Ollama corriendo en `http://127.0.0.1:11434`.")
            modelo_elegido = st.text_input("Nombre del Modelo:", value="llama3-groq-tool-use:8b")
    else:
        st.markdown("### ☁️ Modelo Cloud Autorizado")
        modelo_elegido = st.selectbox(
            "Selecciona Modelo NIM:",
            MODELOS_NIM_CONOCIDOS,
            index=0,
            help="Modelo verificado con soporte de Tool Calling para la rúbrica SKALA."
        )

    # 3. Afinación de Hiperparámetros
    st.markdown("---")
    st.markdown("### 🎛️ Hiperparámetros")
    temperatura = st.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
    max_tokens = st.slider("Max Tokens:", min_value=50, max_value=500, value=250, step=25)

    # 4. Estado de Salud FastMCP
    st.markdown("---")
    st.markdown("### 🔌 Estado del Servidor MCP")
    try:
        tools = run_async_safe(mcp.list_tools(), timeout=3)
        st.success(f"🟢 FastMCP Activo ({len(tools)} herramienta)")
        with st.expander("Ver herramientas registradas"):
            for t in tools:
                st.write(f"• **`{t.name}`**")
                st.caption(t.description)
    except Exception as e:
        st.error(f"🔴 FastMCP No Disponible: {e}")

    # 5. Badges de Seguridad Zero-Trust
    st.markdown("---")
    st.markdown("### 🛡️ Políticas Zero-Trust")
    st.markdown("✅ **Allowlist Activa:** `track_order`")
    st.markdown("✅ **Secretos:** `.env` en `.gitignore`")
    st.markdown("✅ **Límite:** Máx 3 iteraciones")
    st.caption("Desarrollado por Emmanuel Sánchez")


# ==============================================================================
# ÁREA PRINCIPAL: ENCABEZADO Y TABS
# ==============================================================================
st.markdown('<div class="main-title">⚡ SKALA Agentic Developer Workbench</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Plataforma de Diagnóstico, Inspección de Protocolo MCP e Inferencia Híbrida | Desarrollado por <b>Emmanuel Sánchez</b></div>', unsafe_allow_html=True)

# Pestañas de trabajo
tab_playground, tab_inspector, tab_diagnostico = st.tabs([
    "💬 Playground Agéntico",
    "🔍 Inspector de Protocolo MCP",
    "🧪 Suite de Pruebas & Diagnóstico"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: PLAYGROUND AGÉNTICO
# ------------------------------------------------------------------------------
with tab_playground:
    st.markdown("### 🧪 Laboratorio de Consultas Agénticas")
    st.write("Prueba cómo el agente procesa lenguaje natural, decide invocar FastMCP y sintetiza respuestas.")

    # Botones de prueba rápida preconfigurados
    st.markdown("**Consultas de Prueba Rápida:**")
    col1, col2, col3, col4 = st.columns(4)

    prompt_sugerido = ""
    if col1.button("📦 Pedido 45231 (En tránsito)"):
        prompt_sugerido = "Hola, ¿podrías informarme cuál es el estado de mi pedido 45231?"
    if col2.button("🚚 Pedido 10001 (Entregado)"):
        prompt_sugerido = "Por favor revisa el estatus de entrega del pedido 10001."
    if col3.button("❓ Pregunta sin ID"):
        prompt_sugerido = "Hola, quiero saber cuándo llega mi paquete que pedí la semana pasada."
    if col4.button("❌ Pedido Inexistente (99999)"):
        prompt_sugerido = "Por favor revisa el estatus del pedido 99999."

    # Campo de entrada
    prompt_usuario = st.text_input(
        "Ingresa la consulta para el agente:",
        value=prompt_sugerido if prompt_sugerido else "Hola, ¿podrías informarme cuál es el estado de mi pedido 45231?",
        key="input_prompt"
    )

    btn_ejecutar = st.button("🚀 Ejecutar Ciclo Agéntico", type="primary")

    if btn_ejecutar and prompt_usuario.strip():
        with st.spinner(f"Ejecutando inferencia con {modelo_elegido} vía {proveedor_sel}..."):
            try:
                engine = AgenteWorkbenchEngine(
                    proveedor=proveedor_id,
                    modelo=modelo_elegido,
                    temperature=temperatura,
                    max_tokens=max_tokens
                )
                resultado = run_async_safe(engine.ejecutar_consulta(prompt_usuario.strip()), timeout=50)

                # 1. Métricas de Rendimiento
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Proveedor", "NVIDIA Cloud" if proveedor_id == "nvidia" else "Ollama Local")
                m2.metric("Modelo", modelo_elegido.split("/")[-1])
                m3.metric("Latencia", f"{resultado['latencia']:.2f} s")
                m4.metric("Tokens Usados", resultado["tokens"] if resultado["tokens"] else "N/A")
                m5.metric("Costo Est.", "$0.00" if proveedor_id == "ollama" else "Cloud Credits")

                # 2. Respuesta Final del Agente
                st.markdown("#### 🤖 Respuesta del Agente:")
                st.info(resultado["respuesta"])

                # 3. Trazabilidad del Protocolo MCP
                st.markdown("#### 🔍 Trazabilidad del Ciclo MCP (Auditoría de Ejecución):")
                hubo_tools = False
                for t in resultado["trazas"]:
                    if t["tool_calls"]:
                        hubo_tools = True
                        for tc in t["tool_calls"]:
                            with st.expander(f"🛠️ [MCP Tool Call] {tc['herramienta']}", expanded=True):
                                c_arg, c_ret = st.columns(2)
                                with c_arg:
                                    st.markdown("**Argumentos JSON generados por el LLM:**")
                                    st.json(tc["argumentos"])
                                with c_ret:
                                    st.markdown("**Respuesta cruda del Servidor MCP:**")
                                    try:
                                        st.json(json.loads(tc["retorno_mcp"]))
                                    except Exception:
                                        st.code(tc["retorno_mcp"])

                if not hubo_tools:
                    st.caption("ℹ️ El agente no detectó necesidad de invocar herramientas para este mensaje (respuesta directa).")

            except Exception as e:
                st.error(f"Error durante la ejecución del agente: {str(e)}")

# ------------------------------------------------------------------------------
# PESTAÑA 2: INSPECTOR DE PROTOCOLO MCP
# ------------------------------------------------------------------------------
with tab_inspector:
    st.markdown("### 🔍 Inspección Directa de FastMCP (Sin LLM)")
    st.write("Valida los contratos de software y la ejecución determinista de las herramientas directamente en el servidor MCP.")

    col_info, col_call = st.columns([1, 1])

    with col_info:
        st.markdown("#### 📋 Contrato de Herramienta (`list_tools`)")
        try:
            tools_list = run_async_safe(mcp.list_tools(), timeout=3)
            for t in tools_list:
                st.code(f"Tool Name: {t.name}", language="text")
                st.markdown(f"**Descripción:**\n{t.description}")
                esquema = getattr(t, "input_schema", getattr(t, "inputSchema", {}))
                st.markdown("**Input Schema Oficial:**")
                st.json(esquema)
        except Exception as e:
            st.error(f"Error consultando list_tools: {e}")

    with col_call:
        st.markdown("#### ⚡ Invocar Herramienta (`call_tool`)")
        order_input = st.text_input("Ingresa 'order_id' para probar:", value="45231")
        if st.button("Ejecutar `track_order` en FastMCP"):
            try:
                res_mcp = run_async_safe(mcp.call_tool("track_order", {"order_id": order_input.strip()}), timeout=3)
                st.success("Ejecución completada en Servidor MCP:")
                texto_salida = ""
                if hasattr(res_mcp, "content") and res_mcp.content:
                    for item in res_mcp.content:
                        if hasattr(item, "text"):
                            texto_salida = item.text
                elif hasattr(res_mcp, "structured_content"):
                    texto_salida = json.dumps(res_mcp.structured_content, ensure_ascii=False)
                else:
                    texto_salida = str(res_mcp)

                try:
                    st.json(json.loads(texto_salida))
                except Exception:
                    st.code(texto_salida)
            except Exception as e:
                st.error(f"Fallo en call_tool: {e}")

# ------------------------------------------------------------------------------
# PESTAÑA 3: SUITE DE PRUEBAS & DIAGNÓSTICO
# ------------------------------------------------------------------------------
with tab_diagnostico:
    st.markdown("### 🧪 Consola de Ejecución de Pruebas Automatizadas")
    st.write("Dispara la suite oficial de pytest, el script de verificación y la conexión con Salesforce con un solo clic.")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    if col_btn1.button("▶️ Ejecutar Pytest Suite (6 Tests)", type="secondary"):
        with st.spinner("Ejecutando pytest en el entorno virtual..."):
            cmd = [sys.executable, "-m", "pytest", "-v", "test_suite_automatizada.py"]
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(".")))
            if res.returncode == 0:
                st.success("✅ 6/6 Pruebas de Integración Aprobadas (PASS)")
            else:
                st.error("❌ Se detectaron fallas en las pruebas")
            st.code(res.stdout if res.stdout else res.stderr, language="text")

    if col_btn2.button("🩺 Diagnóstico de Entorno", type="secondary"):
        with st.spinner("Verificando librerías y configuración de seguridad..."):
            cmd = [sys.executable, "verificar_entorno.py"]
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(".")))
            st.code(res.stdout, language="text")

    if col_btn3.button("🍁 Verificar Salesforce Org", type="secondary"):
        with st.spinner("Consultando estado de organización con Salesforce CLI..."):
            try:
                cmd = ["powershell.exe", "-NoProfile", "-Command", "sf org list"]
                res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(".")))
                st.code(res.stdout if res.stdout else res.stderr, language="text")
            except Exception as e:
                st.error(f"Error consultando sf org list: {e}")
