#!/usr/bin/env python3
"""
Menú simple de consola en Python para realizar peticiones REST (Esqueleto Genérico).
Permite interactuar de forma interactiva y llamar a funciones para probar la API.
"""
import os
import sys
import requests

API_URL = os.getenv('API_URL', 'http://localhost:8001')


def verificar_salud():
    """Realiza una petición GET para comprobar el estado de la API."""
    url = f"{API_URL}/health"
    print(f"\n[INFO] Consultando estado en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] No se pudo conectar con el servidor: {err}")


def inicializar_bd():
    """Realiza una petición POST para inicializar el esquema de base de datos (DDL)."""
    url = f"{API_URL}/setup"
    print(f"\n[INFO] Solicitando setup en: {url}")
    try:
        response = requests.post(url, timeout=30)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error al realizar la petición: {err}")


def consultar_registros():
    """Realiza una petición GET para consultar registros existentes."""
    url = f"{API_URL}/data"
    print(f"\n[INFO] Consultando datos en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def insertar_registro():
    """Realiza una petición POST para insertar un nuevo registro."""
    url = f"{API_URL}/data"
    print(f"\n[INFO] Insertar registro en: {url}")
    item_id = input("ID: ").strip()
    nombre = input("Nombre: ").strip()
    categoria = input("Categoría: ").strip()
    valor = input("Valor: ").strip()

    payload = {
        "id": item_id,
        "nombre": nombre,
        "categoria": categoria,
        "valor": valor
    }
    # Enviar solo campos con valor
    payload = {k: v for k, v in payload.items() if v}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def mostrar_menu():
    """Despliega el menú de opciones en pantalla."""
    print("\n" + "=" * 45)
    print("        MENÚ PRINCIPAL - REST CLIENT")
    print("=" * 45)
    print(f" Servidor objetivo: {API_URL}")
    print("-" * 45)
    print(" 1. Verificar estado del servidor (GET /health)")
    print(" 2. Inicializar esquema de base de datos (POST /setup)")
    print(" 3. Consultar registros (GET /data)")
    print(" 4. Insertar un nuevo registro (POST /data)")
    print(" 0. Salir")
    print("=" * 45)


def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción [0-4]: ").strip()

        if opcion == '1':
            verificar_salud()
        elif opcion == '2':
            inicializar_bd()
        elif opcion == '3':
            consultar_registros()
        elif opcion == '4':
            insertar_registro()
        elif opcion == '0':
            print("\nSaliendo del programa. ¡Hasta luego!")
            sys.exit(0)
        else:
            print("\n[AVISO] Opción no válida. Por favor, ingresa un número del 0 al 4.")


if __name__ == '__main__':
    main()
