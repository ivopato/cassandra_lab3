#!/usr/bin/env python3
"""
Capa de modelo de base de datos para Cassandra (Esqueleto Genérico).

Plantilla para implementar fácilmente cualquier modelo de datos.
Permite insertar diccionarios o CSVs directamente sin mapeos complejos.
"""
import logging
import os
import sys
import time
import uuid

from cassandra.cluster import Cluster

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conexión a Cassandra
# ---------------------------------------------------------------------------

class CassandraConnection:

    def __init__(self, hosts=None, port=9042, keyspace='app_keyspace', replication_factor=1):
        self.hosts = hosts or ['localhost']
        self.port = port
        self.keyspace = keyspace
        self.replication_factor = replication_factor
        self.cluster = None
        self.session = None

    def connect(self, retries=5, delay=5):
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                log.info(f"Conectando a Cassandra en {self.hosts}:{self.port} (intento {attempt}/{retries})")
                self.cluster = Cluster(self.hosts, port=self.port)
                self.session = self.cluster.connect()
                return True
            except Exception as e:
                last_exc = e
                log.warning(f"Fallo de conexión ({attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(delay)
        raise last_exc

    def close(self):
        for obj in (self.session, self.cluster):
            if obj:
                try:
                    obj.shutdown()
                except Exception:
                    pass

    def is_connected(self):
        return self.session is not None and not self.session.is_shutdown


# ---------------------------------------------------------------------------
# DDL — Definición de Tablas (Personalizable para tu modelo)
# ---------------------------------------------------------------------------

CREATE_KEYSPACE = """
    CREATE KEYSPACE IF NOT EXISTS {}
    WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': 1 }}
"""


# orders_by_customers - ordenes de un cliente por order_date DESC (uso email porque no se repite)
CREATE_ORDERS_BY_CUSTOMERS_TABLE = """
    CREATE TABLE IF NOT EXISTS orders_by_customers (
        email TEXT,
        name TEXT,
        order_number TEXT,
        order_date TIMEUUID,
        total_amount FLOAT,
        status TEXT,
        PRIMARY KEY ((email), order_date, order_number)
    )
"""

# products_by_order - productos de una orden por price DESC
CREATE_PRODUCTS_BY_ORDER_TABLE = """
    CREATE TABLE IF NOT EXISTS products_by_order (
        order_number TEXT,
        product_name TEXT,
        category TEXT,
        price FLOAT,
        quantity INT,
        PRIMARY KEY ((order_number), price, product_name)
    )
"""

# shipments_by_o_sd - shipments de una orden y por rango de shipment_date (2 queries)
CREATE_SHIPMENTS_BY_O_SD_TABLE = """
    CREATE TABLE IF NOT EXISTS shipments_by_o_sd (
        order_number TEXT,
        shipment_date TIMEUUID,
        tracking_number TEXT,
        status TEXT,
        type TEXT,
        total_amount FLOAT,
        customer_name TEXT,
        PRIMARY KEY ((order_number), shipment_date, tracking_number)
    )
"""

# shipments_by_o_ssd - shipments de una orden por status 
CREATE_SHIPMENTS_BY_O_SSD_TABLE = """
    CREATE TABLE IF NOT EXISTS shipments_by_o_ssd (
        order_number TEXT,
        status TEXT,
        shipment_date TIMEUUID,
        tracking_number TEXT,
        type TEXT,
        total_amount FLOAT,
        customer_name TEXT,
        PRIMARY KEY ((order_number, status), shipment_date, tracking_number)
    )
"""

# shipments_by_o_tsd - shipments de una orden por type 
CREATE_SHIPMENTS_BY_O_TSD_TABLE = """
    CREATE TABLE IF NOT EXISTS shipments_by_o_tsd (
        order_number TEXT,
        type TEXT,
        shipment_date TIMEUUID,
        tracking_number TEXT,
        status TEXT,
        total_amount FLOAT,
        customer_name TEXT,
        PRIMARY KEY ((order_number, type), shipment_date, tracking_number)
    )
"""

# shipments_by_o_tssd - shipments de una orden por type y status 
CREATE_SHIPMENTS_BY_O_TSSD_TABLE = """
    CREATE TABLE IF NOT EXISTS shipments_by_o_tssd (
        order_number TEXT,
        type TEXT,
        status TEXT,
        shipment_date TIMEUUID,
        tracking_number TEXT,
        total_amount FLOAT,
        customer_name TEXT,
        PRIMARY KEY ((order_number, type, status), shipment_date, tracking_number)
    ) 
"""

ALL_TABLES = [
    ('orders_by_customers', CREATE_ORDERS_BY_CUSTOMERS_TABLE),
    ('products_by_order', CREATE_PRODUCTS_BY_ORDER_TABLE),
    ('shipments_by_o_sd', CREATE_SHIPMENTS_BY_O_SD_TABLE),
    ('shipments_by_o_ssd', CREATE_SHIPMENTS_BY_O_SSD_TABLE),
    ('shipments_by_o_tsd', CREATE_SHIPMENTS_BY_O_TSD_TABLE),
    ('shipments_by_o_tssd', CREATE_SHIPMENTS_BY_O_TSSD_TABLE),
]


def _exec(session, cql, retries=3, delay=3):
    """Ejecuta una sentencia CQL con reintentos."""
    for attempt in range(1, retries + 1):
        try:
            session.execute(cql, timeout=30)
            time.sleep(0.1)
            return
        except Exception as e:
            log.warning(f"Error CQL ({attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay * attempt)
            else:
                raise


def create_keyspace(session, keyspace, replication_factor):
    """Crea el keyspace si no existe."""
    _exec(session, CREATE_KEYSPACE.format(keyspace, replication_factor))


def create_schema(session):
    """Crea todas las tablas registradas en ALL_TABLES."""
    for name, ddl in ALL_TABLES:
        log.info(f"Creando tabla: {name}")
        _exec(session, ddl)


# ---------------------------------------------------------------------------
# Inserción y Operaciones Simplificadas
# ---------------------------------------------------------------------------

def insert_dict(session, table: str, data: dict):
    """
    Inserta de forma genérica cualquier diccionario en una tabla de Cassandra.
    Las claves del diccionario deben coincidir con los nombres de columna.
    """
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    stmt = session.prepare(query)
    session.execute(stmt, list(data.values()))


def insert_record(session, data: dict, table=None):
    """Inserta un registro individual en la tabla especificada o por defecto."""
    target_table = table or ALL_TABLES[0][0]
    insert_dict(session, target_table, data)
    return data


# tablas con datos iguales (shipments)
SHIPMENT_TABLES = ['shipments_by_o_sd', 'shipments_by_o_ssd', 'shipments_by_o_tsd', 'shipments_by_o_tssd']


def create_order(session, order_data: dict, products: list):
    # insertamos la orden en orders_by_customers y cada producto en products_by_order
    if 'order_date' not in order_data:
        order_data['order_date'] = uuid.uuid1()

    insert_dict(session, 'orders_by_customers', order_data)

    for product in products:
        product['order_number'] = order_data['order_number']
        insert_dict(session, 'products_by_order', product)

    return order_data


def create_shipment(session, shipment_data: dict):
    # insertamos el mismo shipment en las 4 tablas de shipment que tenemos (o sea si pongo en una se inserta en todas esas)
    if 'shipment_date' not in shipment_data:
        shipment_data['shipment_date'] = uuid.uuid1()

    for table in SHIPMENT_TABLES:
        insert_dict(session, table, shipment_data)

    return shipment_data


def get_all_records(session, table=None, limit=100):
    """Consulta registros de la tabla especificada o por defecto."""
    target_table = table or ALL_TABLES[0][0]
    rows = session.execute(f"SELECT * FROM {target_table} LIMIT {limit}")
    return [dict(r._asdict()) for r in rows]


# ---------------------------------------------------------------------------
# Consultas (trataré de seguir el formato del esqueleto)
# ---------------------------------------------------------------------------

def get_orders_by_customer(session, email):
    # 1. ordenes de un cliente por order_date DESC
    query = "SELECT * FROM orders_by_customers WHERE email = %s ORDER BY order_date DESC"
    rows = session.execute(query, [email])
    return [dict(r._asdict()) for r in rows]


def get_products_by_order(session, order_number):
    # 2. productos de una orden por price DESC
    query = "SELECT * FROM products_by_order WHERE order_number = %s ORDER BY price DESC"
    rows = session.execute(query, [order_number])
    return [dict(r._asdict()) for r in rows]


def get_shipments_by_order(session, order_number):
    # 3.1. shipments de una orden
    query = "SELECT * FROM shipments_by_o_sd WHERE order_number = %s ORDER BY shipment_date DESC"
    rows = session.execute(query, [order_number])
    return [dict(r._asdict()) for r in rows]


def get_shipments_by_order_and_date_range(session, order_number, start_date, end_date):
    # 3.2. shipments de una orden por shipment_date
    query = """
        SELECT * FROM shipments_by_o_sd
        WHERE order_number = %s AND shipment_date >= %s AND shipment_date <= %s
        ORDER BY shipment_date DESC
    """
    rows = session.execute(query, [order_number, start_date, end_date])
    return [dict(r._asdict()) for r in rows]


def get_shipments_by_order_and_status(session, order_number, status, start_date=None, end_date=None):
    # 3.3. shipments de una orden por status (opcional por fecha)
    query = "SELECT * FROM shipments_by_o_ssd WHERE order_number = %s AND status = %s"
    params = [order_number, status]

    if start_date and end_date:
        query += " AND shipment_date >= %s AND shipment_date <= %s"
        params.append(start_date)
        params.append(end_date)

    query += " ORDER BY shipment_date DESC"
    rows = session.execute(query, params)
    return [dict(r._asdict()) for r in rows]


def get_shipments_by_order_and_type(session, order_number, type_, start_date=None, end_date=None):
    # 3.4. shipments de una orden por type (tmb opcional por fecha)
    query = "SELECT * FROM shipments_by_o_tsd WHERE order_number = %s AND type = %s"
    params = [order_number, type_]

    if start_date and end_date:
        query += " AND shipment_date >= %s AND shipment_date <= %s"
        params.append(start_date)
        params.append(end_date)

    query += " ORDER BY shipment_date DESC"
    rows = session.execute(query, params)
    return [dict(r._asdict()) for r in rows]


def get_shipments_by_order_type_and_status(session, order_number, type_, status, start_date=None, end_date=None):
    # 3.5. shipments de una orden por type y status (opcional fecha)
    query = "SELECT * FROM shipments_by_o_tssd WHERE order_number = %s AND type = %s AND status = %s"
    params = [order_number, type_, status]

    if start_date and end_date:
        query += " AND shipment_date >= %s AND shipment_date <= %s"
        params.append(start_date)
        params.append(end_date)

    query += " ORDER BY shipment_date DESC"
    rows = session.execute(query, params)
    return [dict(r._asdict()) for r in rows]
