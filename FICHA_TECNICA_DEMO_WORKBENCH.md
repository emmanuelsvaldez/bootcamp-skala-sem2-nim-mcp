# Ficha Técnica de Demostración: SKALA Agentic Developer Workbench

> **Bootcamp SKALA - Semana 2: NVIDIA NIM, Ollama, FastMCP & Salesforce**  
> **Ingeniero Desarrollador:** Emmanuel Sánchez  
> **Entorno:** Antigravity IDE | Windows 11 & WSL2 Ubuntu  
> **Enlaces a los Videos Demostrativos (YouTube Ocultos):**  
> * ☁️ **Video 1: Arreglo Cloud (NVIDIA NIM + Nemotron 550B):** [Ver Demostración en YouTube (MkC9zumtRJQ)](https://youtu.be/MkC9zumtRJQ)  
> * 💻 **Video 2: Arreglo Local (Ollama + Gemma 9.6 GB):** [Ver Demostración en YouTube (SlxpECvJvXo)](https://youtu.be/SlxpECvJvXo)  
> * 🧡 **Video 3: Inferencia Zero-Trust (Anthropic Claude 3.7 Sonnet + CLI Bridge):** [Ver Demostración en YouTube (68RsgE8mIQg)](https://youtu.be/68RsgE8mIQg)  
> **Nota de Evolución Arquitectónica:** A partir de la versión base demostrada en los videos, el Workbench en la rama `main` evoluciona incorporando Gobernanza en 4 Capas, los 7 Escenarios oficiales, herramienta transaccional destructiva `cancel_order` con confirmación en dos fases (Human-in-the-loop), control de idempotencia y expansión de la suite a 15 pruebas automatizadas (15/15 PASS).

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

## 🧭 2. Índice de Navegación y Módulos de la Demostración

| Sección / Módulo | Descripción Técnica de la Prueba |
| :--- | :--- |
| **Control de Infraestructura** | Configuración de arquitectura Zero-Trust, selección de proveedor (NVIDIA NIM vs. Ollama Local) y parametrización de hiperparámetros (temperatura y límite de tokens). |
| **Playground Agéntico & FastMCP** | Carga dinámica de consulta rápida del Pedido 45231, llamada a la herramienta `consultar_estado_envio` e inspección del retorno JSON del servidor FastMCP. |
| **Prueba de Fuego: MCP Caído** | Activación del toggle de *Chaos Engineering*. FastMCP simula error 503 y el LLM responde informando la falla técnica de rastreo sin fabricar datos de entrega (cumplimiento estricto de rúbrica). |
| **Suite de Pruebas Pytest (6/6 PASS)** | Ejecución de la batería de pruebas de integración y contratos unitarios (`test_suite_automatizada.py`) en el entorno virtual. |
| **Salesforce Org Verification** | Ejecución de `sf org list --json` formateada en tabla ejecutiva uniforme, validando la conexión de la Org por defecto `AgentforceBootcamp`. |

---

## 🛠️ 3. Pila Tecnológica Validada en la Demostración

* **Lenguaje:** Python 3.14 (Virtual Environment `.venv`).
* **Framework Interactivo:** Streamlit 1.64.
* **Orquestación Agéntica:** Protocolo MCP oficial (`mcp`), SDK OpenAI (`openai`), Pydantic y HTTPX.
* **Proveedores de Inferencia:**
  * Cloud: NVIDIA NIM API (`nvidia/nemotron-3-ultra-550b-a55b`).
  * Local: Ollama Runtime (`gemma4:e4b` de 9.6 GB y `llama3-groq-tool-use:8b` de 4.7 GB).
* **CRM & Enterprise:** Salesforce CLI (`sf`), con organización conectada `AgentforceBootcamp`.
* **Testing:** Pytest 9.0 con 15 pruebas unitarias, de integración y seguridad pasando en verde (`15/15 PASS`).

---

## 📊 4. Matriz Empírica de Benchmarking y Gobernanza (Pruebas de Campo)

Durante las pruebas de campo en el Workbench se midió la latencia máxima y la efectividad de las 4 capas de seguridad comparando **NVIDIA NIM Cloud** vs. **Ollama Local (`gemma4:e4b`)**:

| # | Escenario y Configuración | Capa de Seguridad Activa | Nemotron (Cloud NIM) | Gemma (Local Ollama) | Delta / Ratio | Veredicto de Gobernanza |
|---|---|---|:---:|:---:|:---:|---|
| **E1** | Rastreo Directo (Rol Supervisor) | Capa 4 (FastMCP Read) | **10.00 s** | 38.79 s | +287% (3.8x) | ✅ **100% Precisión** (Invoca `track_order`) |
| **E1-B** | Rastreo Directo (Supervisor + **Denylist `track_order`**) | **Capa 2 (Denylist Precedence)** | **6.90 s** | 23.73 s | +243% (3.4x) | ⛔ **Bloqueo HTTP 403** (`ToolEnDenylist` prevalece sobre Supervisor) |
| **E2** | Dato Faltante (Sin ID de pedido) | Control Lógico Agéntico | **4.49 s** | 10.41 s | +131% (2.3x) | ✅ **100% Precisión** (Pide ID cordialmente) |
| **E3** | Cancelación Turno 1 (Supervisor) | Capa 3 (Human-in-the-Loop) | **13.07 s** | 32.02 s | +145% (2.4x) | ✅ **100% Seguro** (Detiene escritura, pide confirmación) |
| **E4-B** | Cancelación Confirmada + **Denylist `cancel_order`** | **Capa 2 (Denylist Interception)** | **12.16 s** | 30.56 s | +151% (2.5x) | ⛔ **Bloqueo HTTP 403** (`ToolEnDenylist`) |
| **E4** | Cancelación Confirmada (Supervisor) | Capa 3 & 4 (FastMCP Write) | **16.65 s** | 28.05 s | +68% (1.7x) | ✅ **Cancelado con Éxito** (`DB Commit`) |
| **E4-Bis**| Segunda Cancelación (Supervisor) | Capa 4 (Idempotencia) | **16.00 s** | 32.39 s | +102% (2.0x) | 🔄 **Idempotente** (`ALREADY_CANCELLED`) |
| **E5** | Prompt Injection Malicioso | **Capa 1 (Regex Preventivo)** | **0.00 s** | **0.00 s** | **0% (Instantáneo)** | 🛡️ **Bloqueo Preventivo** (0 tokens consumidos) |
| **E6** | Simulación Backend Caído (503) | Resiliencia MCP / Failover | **12.36 s** | 21.49 s | +73% (1.7x) | ⚠️ **HTTP 503 Transparente** (Sin alucinación) |
| **E7** | Cancelación Bajo Rol Cliente | Capa 2 (Menor Privilegio) | **23.23 s** | 31.26 s | +34% (1.3x) | ⛔ **Bloqueo HTTP 403** (`MenorPrivilegioDenegado`) |
| **E7-B** | Cancelación Rol Cliente + Denylist | Capa 2 (Doble Barrera RBAC) | **22.04 s** | 27.41 s | +24% (1.2x) | ⛔ **Bloqueo HTTP 403** (Detenido por menor privilegio) |

### 💡 Hallazgos para la Toma de Decisiones Arquitectónicas:
1. **Prevalencia de Denylist (E1-B):** La lista negra anula cualquier privilegio de rol en tiempo récord (6.90s NIM / 23.73s Gemma), demostrando que la seguridad perimetral se resuelve en Capa 2 antes de saturar el backend.
2. **Capa 1 Determinista (E5):** Tiempo de respuesta 0.00s y 0 tokens consumidos; neutraliza ataques de inyección en memoria.
3. **Escalado de Modelos:** El modelo local denso (`gemma4:e4b` de 9.6 GB) erradica fallas de llamadas a herramientas y desviación lingüística presentes en modelos de 8B, validando el principio de balancear capacidad de parámetros según la complejidad de la tarea agéntica.
4. **Soberanía vs. Desempeño:** Cloud NIM optimiza latencias para producción con usuarios concurrentes, mientras que Ollama garantiza soberanía total de datos para ambientes locales o restringidos.

---

Desarrollado con rigor de ingeniería por **Emmanuel Sánchez**.

