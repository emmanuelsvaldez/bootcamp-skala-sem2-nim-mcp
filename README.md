# Práctica Enterprise: NVIDIA NIM, Ollama, MCP y Salesforce

> **Bootcamp SKALA - Semana 2**  
> **Instructor:** M.C. Fernando Morquecho  
> **Desarrollado por:** Emmanuel Sánchez  
> **Entorno:** Antigravity IDE (Extensión Pack Salesforce) | Windows 11 & WSL2 Ubuntu  

---

## 1. Propósito de la Solución

El objetivo de esta solución es construir una arquitectura de agente inteligente de nivel **Enterprise** que:
1. **Desacopla la inferencia del modelo:** Conecta de manera intercambiable con **NVIDIA NIM** (nube corporativa optimizada) y **Ollama** (ejecución local offline).
2. **Estandariza la integración de herramientas mediante MCP (Model Context Protocol):** El modelo no interactúa con bases de datos ni con Salesforce directamente; descubre y ejecuta herramientas a través de contratos tipados JSON-RPC expuestos por un servidor MCP.
3. **Prepara el terreno para Salesforce & Agentforce:** Define los patrones de integración empresarial donde Agentforce puede actuar como cliente consumidor de MCP o donde Salesforce/MuleSoft exponen capacidades del CRM mediante servidores MCP gobernados.

---

## 2. Claridad Conceptual Crítica (Fundamentos Arquitectónicos)

Para evitar errores conceptuales en diseño de software y auditorías de seguridad:

| Concepto | Qué es y qué hace | Qué NO es / Qué NO hace |
| :--- | :--- | :--- |
| **LLM** (Large Language Model) | Red neuronal que procesa tokens, interpreta lenguaje natural y propone llamadas a herramientas (`tool_calls`). | **No es una base de datos ni ejecuta código** por sí mismo. No consulta Salesforce directamente. |
| **NVIDIA NIM** | Plataforma de microservicios e inferencia acelerada optimizada por NVIDIA que expone modelos mediante APIs estándar seguras. | **No es el LLM en sí** (es el runtime que lo sirve) ni es un servidor MCP. |
| **Ollama** | Runtime ligero para descargar y ejecutar modelos de lenguaje en hardware local. | **No sustituye a NIM** ni es un entorno de producción masiva empresarial. |
| **MCP** (Model Context Protocol) | Protocolo abierto estandarizado (JSON-RPC) para descubrimiento de herramientas, recursos y prompts entre agentes y sistemas externos. | **No ejecuta la inferencia** del modelo ni reemplaza los modelos de lenguaje. |
| **Agente Orquestador** | Aplicación que coordina el ciclo de vida: invoca inferencia, valida esquemas con allowlists, ejecuta herramientas y retorna resultados al LLM. | **No debe delegar decisiones de seguridad críticas** únicamente al prompt del modelo. |
| **Agentforce** | Plataforma de agentes autónomos integrada en Salesforce para automatizar procesos de negocio sobre Data Cloud. | **No sustituye a MuleSoft** ni a los sistemas de integración de la empresa. |
| **MuleSoft** | Capa de integración empresarial (Anypoint Platform) para gobernanza, seguridad, transformación de APIs y políticas de acceso. | **No es un modelo de lenguaje**. |

---

## 3. Patrón de Inferencia Híbrida Desacoplada (Factory / Adapter Pattern)

Uno de los pilares arquitectónicos más relevantes de esta implementación para **evaluaciones técnicas y reclutadores de ingeniería** es la eliminación absoluta del *Vendor Lock-in* mediante el desacoplamiento de la capa de inferencia:

```mermaid
flowchart TD
    Factory["🏭 LLMProviderFactory\n(Patrón Creacional / Adapter)"]
    Decision{"¿LLM_PROVIDER en .env?"}
    
    subgraph Cloud ["☁️ Nube: Producción & Escalabilidad"]
        direction TB
        NIM["🚀 NVIDIA NIM (Cloud API)"]
        NIM_Det["• Endpoint: integrate.api.nvidia.com\n• Modelo: Nemotron / Llama 70B\n• Cómputo: Tensor Core GPUs (Cloud)\n• Autenticación: NVIDIA_API_KEY"]
        NIM --- NIM_Det
    end

    subgraph Local ["💻 Local: Desarrollo & Privacidad"]
        direction TB
        Ollama["⚡ Ollama (Local Runtime)"]
        OLL_Det["• Endpoint: localhost:11434\n• Modelo: llama3-groq-tool-use:8b\n• Cómputo: Híbrido GPU + 32GB RAM\n• Costo: $0 / 100% Offline"]
        Ollama --- OLL_Det
    end

    Factory --> Decision
    Decision -- "'nvidia' (Producción)" --> NIM
    Decision -- "'ollama' (Desarrollo / Offline)" --> Ollama

    style Factory fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    style Decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e
    style Cloud fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style Local fill:#faf5ff,stroke:#9333ea,stroke-width:2px
    style NIM fill:#ffffff,stroke:#16a34a,stroke-width:2px
    style Ollama fill:#ffffff,stroke:#9333ea,stroke-width:2px
    style NIM_Det fill:#ffffff,stroke:#86efac,stroke-dasharray: 5 5
    style OLL_Det fill:#ffffff,stroke:#d8b4fe,stroke-dasharray: 5 5
```

### Justificación de Ingeniería para Entornos Enterprise:
1. **Eficiencia de Costos y Privacidad (Edge Computing):** Durante fases de desarrollo, depuración y pruebas unitarias de herramientas MCP, el sistema opera con **Ollama Local** (`llama3-groq-tool-use:8b`). Esto permite iterar con latencia baja, sin costo por token y con privacidad total de datos confidenciales.
2. **Escalabilidad en Producción:** Cuando el sistema pasa a cargas de trabajo intensivas, se conmuta a **NVIDIA NIM** simplemente cambiando `LLM_PROVIDER=nvidia` en `.env`. NIM aporta inferencia acelerada sobre GPUs empresariales Tensor Core y microservicios contenerizados.
3. **Principio de Sustitución de Liskov e Interfaz Común:** Ambas soluciones implementan contratos compatibles con la especificación OpenAI (`/v1/chat/completions`), permitiendo al agente orquestador (`AgenteOrquestadorMCP`) descubrir, validar y ejecutar herramientas MCP sin cambiar una sola línea de código fuente.

---

## 4. Diagrama de Arquitectura de la Solución

```mermaid
flowchart TD
    subgraph Usuario ["Capa de Experiencia"]
        U(["👤 Operador / Usuario Final"])
    end

    subgraph Agente ["Capa de Orquestación Agéntica (Python / Antigravity IDE)"]
        A["🧠 Agente Orquestador\n(agente_nim_mcp.py)"]
        AL["🛡️ Allowlist Estricta\n(track_order)"]
        LOOP["🔁 Loop Seguro\n(Máx 3 Iteraciones)"]
        FACTORY["🏭 LLMProviderFactory\n(NIM / Ollama)"]
    end

    subgraph Inferencia ["Capa de Inferencia (LLM)"]
        direction TB
        NIM["☁️ NVIDIA NIM Cloud API\n(integrate.api.nvidia.com)"]
        OLLAMA["💻 Ollama Local Runtime\n(llama3-groq-tool-use:8b)"]
    end

    subgraph ProtocoloMCP ["Capa de Protocolo y Contratos (MCP)"]
        direction TB
        ClientMCP["🔌 Cliente MCP"]
        ServerMCP["⚙️ Servidor MCP Local\n(FastMCP / servidor_mcp.py)"]
        Tool["📦 Herramienta:\ntrack_order(order_id: str)"]
        DB[("💾 Mock Database:\nPedidos 45231 & 10001")]
    end

    subgraph Enterprise ["Capa Corporativa Futura (Salesforce & MuleSoft)"]
        direction TB
        Mule["🛡️ MuleSoft API Gateway\n(Gobernanza & OAuth)"]
        AF["☁️ Salesforce Agentforce\n(Agente Autónomo)"]
        OMS[("🏢 ERP / Logística / Transportistas")]
    end

    U <--> A
    A --> AL
    A --> LOOP
    A --> FACTORY
    FACTORY <--"OpenAI API Compatible"--> NIM
    FACTORY <--"OpenAI API Compatible"--> OLLAMA
    A --> ClientMCP
    ClientMCP <--"JSON-RPC 2.0 (Stdio / In-Process)"--> ServerMCP
    ServerMCP --> Tool
    Tool <--> DB
    Tool -.-> Mule
    Mule -.-> AF
    Mule -.-> OMS

    style Usuario fill:#f8fafc,stroke:#64748b,stroke-width:2px
    style Agente fill:#eff6ff,stroke:#2563eb,stroke-width:2px
    style Inferencia fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style ProtocoloMCP fill:#faf5ff,stroke:#9333ea,stroke-width:2px
    style Enterprise fill:#fffbeb,stroke:#d97706,stroke-width:2px

    style U fill:#ffffff,stroke:#64748b,stroke-width:1px
    style A fill:#ede9fe,stroke:#7c3aed,stroke-width:2px
    style AL fill:#ede9fe,stroke:#7c3aed,stroke-width:1px
    style LOOP fill:#ede9fe,stroke:#7c3aed,stroke-width:1px
    style FACTORY fill:#ede9fe,stroke:#7c3aed,stroke-width:1px
    style NIM fill:#ffffff,stroke:#16a34a,stroke-width:1px
    style OLLAMA fill:#ffffff,stroke:#16a34a,stroke-width:1px
    style ClientMCP fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1px
    style ServerMCP fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1px
    style Tool fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1px
    style DB fill:#f5f3ff,stroke:#8b5cf6,stroke-width:2px
    style Mule fill:#ffffff,stroke:#d97706,stroke-width:1px
    style AF fill:#ffffff,stroke:#d97706,stroke-width:1px
    style OMS fill:#ffffff,stroke:#d97706,stroke-width:1px
```

---

## 5. Estructura del Proyecto

```text
D:\bootcampSem2\
├── docs/
│   └── img/                    # Evidencias fotográficas de ejecución (Rúbrica)
├── .env.example                # Plantilla de variables de entorno (sin credenciales)
├── .gitignore                  # Protección estricta de secretos y entornos
├── requirements.txt            # Dependencias fijadas y auditadas
├── README.md                   # Documentación general y arquitectura
├── verificar_entorno.py        # Script de diagnóstico y verificación inicial
├── probar_nim.py               # Validación aislada de inferencia contra NVIDIA NIM
├── servidor_mcp.py             # Servidor MCP con herramienta 'track_order'
├── test_servidor_mcp.py        # Pruebas unitarias de descubrimiento e invocación MCP
├── agente_nim_mcp.py           # Agente orquestador con soporte NIM / Ollama y MCP
└── test_suite_automatizada.py  # Suite de pruebas automatizadas con pytest
```

---

## 6. Guía de Instalación y Ejecución Paso a Paso

### Paso 1: Configurar el Entorno Virtual

En PowerShell o Bash (WSL):
```bash
# Crear entorno virtual aislado
python -m venv .venv

# Activar el entorno virtual:
# En Windows PowerShell:
.venv\Scripts\Activate.ps1
# En Linux / WSL:
source .venv/bin/activate

# Actualizar pip e instalar dependencias:
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Paso 2: Verificar el Entorno
Ejecutar el script de diagnóstico:
```bash
python verificar_entorno.py
```

### Paso 3: Configurar Credenciales Seguras (.env)
```bash
cp .env.example .env
```
Edita `.env` con tu configuración (`LLM_PROVIDER=ollama` para pruebas locales o `LLM_PROVIDER=nvidia` para la nube).

---

## 7. Políticas de Seguridad Zero-Trust Aplicadas

1. **Gestión de Secretos:** `.env` está expresamente excluido en `.gitignore`. Ninguna clave se imprime en logs ni se envía en prompts.
2. **Control de Bucles Infinitos:** El orquestador limita a **3 iteraciones máximas** el ciclo de tool calling.
3. **Allowlist Estricta:** Solo se autoriza la ejecución de herramientas explícitamente registradas en la lista blanca (`track_order`).
4. **Resistencia a Alucinaciones:** Si un pedido no existe en el sistema, la herramienta responde estructuradamente `{"error": "No encontrado"}` y el modelo informa al usuario sin inventar estados.
5. **Principio de Mínimo Privilegio:** Operaciones de solo lectura en esta fase (`READ-ONLY`).

---

## 8. Evidencias de Evaluación (Rúbrica SKALA - Secciones 15 y 16)

A continuación se presentan las evidencias de ejecución de cada criterio técnico solicitado en la rúbrica oficial de evaluación:

### 📸 Evidencia 1: Diagnóstico de Entorno y Dependencias
* **Criterio (Punto 2):** Versión de Python (3.14.5) y entorno virtual activo (`.venv`) con dependencias instaladas y `.env` detectado.
* **Comando:** `python verificar_entorno.py`

![Evidencia 1: Diagnóstico de Entorno](docs/img/evidencia_01_entorno_virtual.png)

---

### 📸 Evidencia 2: Inferencia Directa con NVIDIA NIM (Cloud 200 OK)
* **Criterio (Punto 3):** Conectividad con la API de NVIDIA NIM (`https://integrate.api.nvidia.com/v1`), modelo `nvidia/nemotron-3-ultra-550b-a55b`, API Key protegida y respuesta `200 OK`.
* **Comando:** `python probar_nim.py`

![Evidencia 2: Inferencia Directa NIM](docs/img/evidencia_02_nim_directo_200ok.png)

---

### 📸 Evidencia 3: Descubrimiento de Herramientas FastMCP (`list_tools`)
* **Criterio (Punto 4):** Servidor FastMCP publicando la herramienta `track_order` con su docstring explicativo y esquema `inputSchema` obligatorio.
* **Comando:** `python test_servidor_mcp.py`

![Evidencia 3: Descubrimiento MCP](docs/img/evidencia_03_mcp_list_tools.png)

---

### 📸 Evidencia 4: Ciclo Completo del Agente con Tool Calling en NVIDIA NIM
* **Criterio (Punto 5):** Detección de la llamada a la herramienta, ejecución en el servidor MCP y síntesis final estructurada en lenguaje natural para el pedido `45231`.
* **Comando:** `python agente_nim_mcp.py` *(con `LLM_PROVIDER=nvidia`)*

![Evidencia 4: Tool Calling con NVIDIA NIM](docs/img/evidencia_04_agente_tool_call_nim.png)

---

### 📸 Evidencia 5: Batería de Pruebas Automatizadas con Pytest
* **Criterio (Punto 6):** 6/6 pruebas unitarias y de integración pasando en verde (`PASSED`), validando contratos de MCP, allowlist y resistencia a alucinaciones.
* **Comando:** `pytest -v test_suite_automatizada.py`

![Evidencia 5: Pruebas Automatizadas](docs/img/evidencia_05_pruebas_automatizadas_pytest.png)

---

### 📸 Evidencia 6: Inferencia Híbrida y Comparativa Local con Ollama
* **Criterio (Diapositiva 15):** Demostración del mismo agente y servidor MCP conmutando a ejecución local offline a costo $0 con Ollama.
* **Comando:** `python agente_nim_mcp.py` *(con `LLM_PROVIDER=ollama`)*

![Evidencia 6: Agente con Ollama Local](docs/img/evidencia_06_agente_ollama_local.png)

---

### 📸 Evidencia Extra A: Validación de Descarga del Modelo Local (Ollama)
* **Criterio:** Verificación del modelo `llama3-groq-tool-use:8b` (4.9 GB) descargado y listo para ejecución híbrida (GPU + RAM) en la máquina.
* **Comando:** `ollama list`

![Evidencia Extra: Modelo Local Descargado](docs/img/OllamaLlama3Model00.png)

---

### 📸 Evidencia Extra B: Organización de Salesforce Conectada en Antigravity IDE
* **Criterio (Lista de Comprobación):** Organización `AgentforceBootcamp` autenticada con status `Connected` y marcada como default (`🍁`).
* **Comando:** `sf org list`

![Evidencia Extra: Salesforce Org Conectada](docs/img/evidencia_07_salesforce_org_connected.png)

---

Desarrollado con rigor de ingeniería por **Emmanuel Sánchez**.
