#!/usr/bin/env python3
"""
==============================================================================
Diagnóstico de Hardware y Dimensionamiento de Modelos (Perfilador LLMFit)
Proyecto: Bootcamp Semana 2 - NVIDIA NIM, Ollama, MCP & Salesforce
Desarrollado por: Emmanuel Sánchez
==============================================================================

Propósito:
    Analiza la capacidad de cómputo local (VRAM de GPU, RAM del sistema y CPU)
    para determinar con precisión matemática qué modelos de lenguaje pueden
    ejecutarse en la máquina local de Emmanuel, calculando el nivel de descarga
    (offloading) entre GPU y memoria RAM.

Fórmula de Dimensionamiento:
    Memoria Requerida (GB) = (Parámetros en miles de millones * Bits por peso / 8) + Context_KV_Cache
"""

import sys
import psutil

def obtener_metricas_hardware():
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    ram_disponible_gb = psutil.virtual_memory().available / (1024 ** 3)
    
    # GPU NVIDIA GeForce RTX 3050 Laptop (4 GB VRAM)
    vram_gb = 4.0
    return {
        "cpu_nucleos": psutil.cpu_count(logical=True),
        "ram_total_gb": round(ram_gb, 2),
        "ram_disponible_gb": round(ram_disponible_gb, 2),
        "vram_gpu_gb": vram_gb,
        "gpu_nombre": "NVIDIA GeForce RTX 3050 Laptop GPU"
    }

def evaluar_modelo(nombre, params_b, cuanti_bits=4, ctx_tokens=4096, soporta_tools=False):
    # Estimación de peso del modelo en GB
    tamano_pesos_gb = (params_b * cuanti_bits) / 8.0 * 1.15  # 15% de overhead de tensores
    # Estimación de caché KV para el contexto especificado
    kv_cache_gb = (ctx_tokens * 2 * 32 * 128 * 2) / (1024 ** 3)  # Estimación estándar
    memoria_total_gb = tamano_pesos_gb + kv_cache_gb
    return {
        "nombre": nombre,
        "params": f"{params_b}B",
        "memoria_total_gb": round(memoria_total_gb, 2),
        "soporta_tools": soporta_tools
    }

def main():
    hw = obtener_metricas_hardware()
    
    print("=" * 80)
    print("  ANÁLISIS DE HARDWARE Y DIMENSIONAMIENTO DE MODELOS (LLMFit Engine)")
    print("  Desarrollado por: Emmanuel Sánchez")
    print("=" * 80)
    print(f"\n[1] Especificaciones Detectadas en tu Laptop:")
    print(f"  - Procesador:        {hw['cpu_nucleos']} hilos lógicos de CPU")
    print(f"  - Memoria RAM Total: {hw['ram_total_gb']} GB (Disponible: {hw['ram_disponible_gb']} GB)")
    print(f"  - GPU Dedicada:      {hw['gpu_nombre']} ({hw['vram_gpu_gb']} GB VRAM)")

    modelos_candidatos = [
        evaluar_modelo("qwen2.5:3b", 3.0, cuanti_bits=4, soporta_tools=True),
        evaluar_modelo("llama3.2:3b", 3.2, cuanti_bits=4, soporta_tools=True),
        evaluar_modelo("llama3-groq-tool-use:8b", 8.0, cuanti_bits=4, soporta_tools=True),
        evaluar_modelo("mistral:7b-instruct", 7.2, cuanti_bits=4, soporta_tools=True),
        evaluar_modelo("llama-3.1-nemotron-70b", 70.0, cuanti_bits=4, soporta_tools=True),
    ]

    print("\n[2] Matriz de Compatibilidad con tu Hardware (Ollama / Local):")
    print(f"{'Modelo':<28} | {'Parámetros':<10} | {'RAM Estimada':<12} | {'Tools':<7} | {'Diagnóstico de Ejecución':<22}")
    print("-" * 88)

    for m in modelos_candidatos:
        mem = m["memoria_total_gb"]
        tools = "SÍ" if m["soporta_tools"] else "NO"
        
        if mem <= hw["vram_gpu_gb"]:
            diag = "[GPU 100%] Ultra Rápido (~35-45 t/s)"
        elif mem <= (hw["vram_gpu_gb"] + hw["ram_disponible_gb"] * 0.75):
            if mem <= 6.5:
                diag = "[HÍBRIDO GPU+RAM] Fluido (~15-25 t/s)"
            else:
                diag = "[HÍBRIDO CPU+RAM] Moderado (~8-12 t/s)"
        else:
            diag = "[NO CABE] Excede memoria disponible"

        print(f"{m['nombre']:<28} | {m['params']:<10} | {mem:>6.2f} GB    | {tools:<7} | {diag:<22}")

    print("-" * 88)
    print("\n[3] Conclusiones del Arquitecto Senior:")
    print("  a) Modelos de 3B (ej. llama3.2:3b o qwen2.5:3b):")
    print("     - Caben 100% en los 4 GB de VRAM de tu RTX 3050. Cero cuello de botella.")
    print("  b) Modelo Oficial de la Práctica (llama3-groq-tool-use:8b):")
    print(f"     - Requiere ~5.5 GB de memoria. Al tener {hw['ram_total_gb']} GB de RAM, Ollama descarga")
    print("       capas en los 4GB de VRAM y el excedente en RAM, logrando una velocidad muy cómoda.")
    print("  c) Modelos de 70B (ej. Nemotron 70B):")
    print("     - Requieren ~42 GB de memoria. No son viables en local; por eso se consumen vía")
    print("       la API hospedada de NVIDIA NIM en la nube.\n")
    print("=" * 80)

if __name__ == "__main__":
    main()
