#!/usr/bin/env python3
"""
Aplicación Falcon ASGI para la API REST con Cassandra (Esqueleto Genérico).
"""
import logging
import os
import falcon.asgi

from model import CassandraConnection
from resources import (
    HealthResource,
    SetupResource,
    DataResource,
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

# Lectura de variables de entorno
CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', '9042'))
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'app_keyspace')
CASSANDRA_REPLICATION_FACTOR = int(os.getenv('CASSANDRA_REPLICATION_FACTOR', '1'))


class LoggingMiddleware:
    """Middleware para registro de peticiones y respuestas."""

    async def process_request(self, req, resp):
        log.info(f"Petición: {req.method} {req.uri}")

    async def process_response(self, req, resp, resource, req_succeeded):
        log.info(f"Respuesta: {resp.status} para {req.method} {req.uri}")


class CORSMiddleware:
    """Middleware para encabezados CORS."""

    async def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        resp.set_header('Access-Control-Allow-Headers', 'Content-Type')


def create_app():
    """Crea y configura la aplicación Falcon ASGI."""
    connection = CassandraConnection(
        hosts=[CASSANDRA_HOST],
        port=CASSANDRA_PORT,
        keyspace=CASSANDRA_KEYSPACE,
        replication_factor=CASSANDRA_REPLICATION_FACTOR,
    )

    try:
        connection.connect()
        log.info(f"Conexión exitosa a Cassandra en {CASSANDRA_HOST}:{CASSANDRA_PORT}")
    except Exception as e:
        log.error(f"Fallo al conectar con Cassandra: {e}")
        raise

    app = falcon.asgi.App(middleware=[
        LoggingMiddleware(),
        CORSMiddleware(),
    ])

    # Instanciación de recursos
    health_resource = HealthResource(connection)
    setup_resource  = SetupResource(connection)
    data_resource   = DataResource(connection)

    # Registro de rutas REST
    app.add_route('/health', health_resource)
    app.add_route('/setup',  setup_resource)
    app.add_route('/data',   data_resource)

    log.info("Rutas registradas:")
    log.info("  GET   /health")
    log.info("  POST  /setup")
    log.info("  GET   /data")
    log.info("  POST  /data")

    return app


app = create_app()
