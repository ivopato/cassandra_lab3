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


def crear_orden():
    # pide los datos de una orden y sus productos y hace POST/orders."""
    url = f"{API_URL}/orders"
    print(f"\n[INFO] Crear orden en: {url}")

    email = input("Email del cliente: ").strip()
    name = input("Nombre del cliente: ").strip()
    order_number = input("Número de orden: ").strip()
    total_amount = input("Total de la orden: ").strip()
    status = input("Status de la orden: ").strip()

    order_data = {
        "email": email,
        "name": name,
        "order_number": order_number,
        "total_amount": float(total_amount) if total_amount else 0,
        "status": status,
    }

    products = []
    cantidad = input("Cuántos productos tiene la orden?: ").strip()
    cantidad = int(cantidad) if cantidad.isdigit() else 0

    for i in range(cantidad):
        print(f"\nProducto {i + 1}:")
        product_name = input("  Nombre del producto: ").strip()
        category = input("  Categoría: ").strip()
        price = input("  Precio: ").strip()
        quantity = input("  Cantidad: ").strip()

        products.append({
            "product_name": product_name,
            "category": category,
            "price": float(price) if price else 0,
            "quantity": int(quantity) if quantity else 0,
        })

    payload = {"order": order_data, "products": products}

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def consultar_ordenes_cliente():
    # Q1 - pide el email del cliente y hace GET/orders/{email}
    email = input("Email del cliente: ").strip()
    url = f"{API_URL}/customers/{email}/orders"
    print(f"\n[INFO] Consultando ordenes en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def consultar_productos_orden():
    # Q2- pide el número de orden y hace GET/orders/{order_number}/products
    order_number = input("Número de orden: ").strip()
    url = f"{API_URL}/orders/{order_number}/products"
    print(f"\n[INFO] Consultando productos en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def crear_shipment():
    # pide los datos de un shipment y hace POST/shipments
    url = f"{API_URL}/shipments"
    print(f"\n[INFO] Crear shipment en: {url}")

    order_number = input("Número de orden: ").strip()
    tracking_number = input("Tracking number: ").strip()
    status = input("Status (Pending, Shipped, In Transit, Out for Delivery, Delivered, Delayed, Returned): ").strip()
    type_ = input("Type (Standard, Express, Same-day): ").strip()
    total_amount = input("Total: ").strip()
    customer_name = input("Nombre del cliente: ").strip()

    payload = {
        "order_number": order_number,
        "tracking_number": tracking_number,
        "status": status,
        "type": type_,
        "total_amount": float(total_amount) if total_amount else 0,
        "customer_name": customer_name,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def consultar_shipments_orden():
    # Q3.1 - Q3.5 - pide el número de orden y filtros opcionales, y hace GET /orders/{order_number}/shipments."""
    order_number = input("Número de orden: ").strip()

    print("\nFiltros opcionales (dejar vacío para omitir):")
    status = input("    Status: ").strip()
    type_ = input("    Type: ").strip()
    start_date = input("    Fecha inicio (start_date): ").strip()
    end_date = input("  Fecha fin (end_date): ").strip()

    params = {}
    if status:
        params['status'] = status
    if type_:
        params['type'] = type_
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    url = f"{API_URL}/orders/{order_number}/shipments"
    print(f"\n[INFO] Consultando shipments en: {url}")
    try:
        response = requests.get(url, params=params, timeout=10)
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
    print(" 1. Verificar estado del servidor (GET/health)")
    print(" 2. Inicializar esquema de base de datos (POST/setup)")
    print(" 3. Crear una orden (POST/orders)")
    print(" 4. Consultar ordenes de un cliente (GET/customers/{email}/orders)")
    print(" 5. Consultar productos de una orden (GET/orders/{order_number}/products)")
    print(" 6. Crear un shipment (POST/shipments)")
    print(" 7. Consultar shipments de una orden (GET/orders/{order_number}/shipments)")
    print(" 0. Salir")
    print("=" * 45)


def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción [0-7]: ").strip()

        if opcion == '1':
            verificar_salud()
        elif opcion == '2':
            inicializar_bd()
        elif opcion == '3':
            crear_orden()
        elif opcion == '4':
            consultar_ordenes_cliente()
        elif opcion == '5':
            consultar_productos_orden()
        elif opcion == '6':
            crear_shipment()
        elif opcion == '7':
            consultar_shipments_orden()
        elif opcion == '0':
            print("\nSaliendo del programa. ¡Hasta luego!")
            sys.exit(0)
        else:
            print("\n[AVISO] Opción no válida. Por favor, ingresa un número del 0 al 7.")


if __name__ == '__main__':
    main()
