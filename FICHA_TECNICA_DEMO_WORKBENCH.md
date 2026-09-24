# Ficha Técnica de Demostración: SKALA Agentic Developer Workbench

> **Bootcamp SKALA - Semana 2: NVIDIA NIM, Ollama, FastMCP & Salesforce**  
> **Ingeniero Desarrollador:** Emmanuel Sánchez  
> **Entorno:** Antigravity IDE | Windows 11 & WSL2 Ubuntu  
> **Enlace al Video Demostrativo (YouTube Oculto):** [Ver Demostración en YouTube (vZjdnarJyvs)](https://youtu.be/vZjdnarJyvs)  

---

## 🎯 1. Resumen Ejecutivo de la Demostración

Esta demostración en video presenta el **SKALA Agentic Developer Workbench**, una interfaz interactiva construida con Streamlit diseñada para diagnosticar, orquestar y auditar en tiempo real agentes inteligentes con inferencia desacoplada y servidores MCP (Model Context Protocol).

La sesión en video valida de forma práctica el 100% de los criterios de la rúbrica oficial de la Semana 2:
1. **Inferencia Híbrida Desacoplada:** Conmutación en caliente entre NVIDIA NIM (Cloud API) y Ollama (Local Runtime).
2. **Ciclo Agéntico y Trazabilidad MCP:** Procesamiento en lenguaje natural, invocación de herramientas (`track_order`) e inspección del payload JSON de ida y vuelta.
3. **Prueba Oficial de Rúbrica (Servidor MCP Caído):** Simulación de falla HTTP 503 mediante interruptor de Ingeniería del Caos, verificando que el agente reporte la contingencia con transparencia sin alucinar datos falsos.
4. **Suite Automatizada de Pruebas:** Ejecución integrada de `pytest` (6/6 PASS).
5. **Conectividad Empresarial Salesforce:** Inspección estructurada y uniforme de organizaciones mediante `sf org list --json`, validando la organización activa `AgentforceBootcamp`.

---

## ⏱️ 2. Índice de Navegación y Marcas de Tiempo (Timestamps)

| Tiempo | Sección / Módulo | Descripción Técnica de la Prueba |
| :--- | :--- | :--- |
| **00:00 - 00:35** | **Control de Infraestructura** | Configuración de arquitectura Zero-Trust, selección de proveedor (NVIDIA NIM vs. Ollama Local) y parametrización de hiperparámetros (temperatura y límite de tokens). |
| **00:35 - 01:20** | **Playground Agéntico & FastMCP** | Carga dinámica de consulta rápida del Pedido 45231, llamada a la herramienta `consultar_estado_envio` e inspección del retorno JSON del servidor FastMCP. |
| **01:20 - 02:05** | **Prueba de Fuego: MCP Caído** | Activación del toggle de *Chaos Engineering*. FastMCP simula error 503 y el LLM responde informando la falla técnica de rastreo sin fabricar datos de entrega (cumplimiento estricto de rúbrica). |
| **02:05 - 02:35** | **Suite de Pruebas Pytest (6/6 PASS)** | Ejecución de la batería de pruebas de integración y contratos unitarios (`test_suite_automatizada.py`) en el entorno virtual. |
| **02:35 - Fin** | **Salesforce Org Verification** | Ejecución de `sf org list --json` formateada en tabla ejecutiva uniforme, validando la conexión de la Org por defecto `AgentforceBootcamp`. |

---

## 🛠️ 3. Pila Tecnológica Validada en la Demostración

* **Lenguaje:** Python 3.14 (Virtual Environment `.venv`).
* **Framework Interactivo:** Streamlit 1.64.
* **Orquestación Agéntica:** Protocolo MCP oficial (`mcp`), SDK OpenAI (`openai`), Pydantic y HTTPX.
* **Proveedores de Inferencia:**
  * Cloud: NVIDIA NIM API (`nvidia/nemotron-3-ultra-550b-a55b` y `meta/llama-3.1-70b-instruct`).
  * Local: Ollama Runtime (`qwen2.5:1.5b` y `llama3-groq-tool-use:8b`).
* **CRM & Enterprise:** Salesforce CLI (`sf`), con organización conectada `AgentforceBootcamp`.
* **Testing:** Pytest 9.0 con mocks deterministas y pruebas de integración asíncrona.

---

Desarrollado con rigor de ingeniería por **Emmanuel Sánchez**.
