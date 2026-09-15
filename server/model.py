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
    WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': {} }}
"""

CREATE_SAMPLE_TABLE = """
    CREATE TABLE IF NOT EXISTS sample_items (
        id        TEXT,
        nombre    TEXT,
        categoria TEXT,
        valor     TEXT,
        PRIMARY KEY (id)
    )
"""

ALL_TABLES = [
    ('sample_items', CREATE_SAMPLE_TABLE),
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


def get_all_records(session, table=None, limit=100):
    """Consulta registros de la tabla especificada o por defecto."""
    target_table = table or ALL_TABLES[0][0]
    rows = session.execute(f"SELECT * FROM {target_table} LIMIT {limit}")
    return [dict(r._asdict()) for r in rows]
