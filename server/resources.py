#!/usr/bin/env python3
"""
Clases de recursos Falcon para la API REST (Esqueleto Genérico).
Expone endpoints estándar para inicialización, carga de datos y CRUD base.
"""
import logging
import falcon
import model

log = logging.getLogger(__name__)


class HealthResource:
    """Endpoint para verificar el estado de salud de la API y de Cassandra."""

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp):
        """GET /health"""
        if self.conn.is_connected():
            resp.media = {'status': 'healthy', 'database': 'connected'}
        else:
            resp.media = {'status': 'unhealthy', 'database': 'disconnected'}
            resp.status = falcon.HTTP_503


class SetupResource:
    """Endpoint administrativo para crear keyspace y tablas (DDL)."""

    def __init__(self, conn):
        self.conn = conn

    async def on_post(self, req, resp):
        """POST /setup"""
        try:
            session = self.conn.session
            model.create_keyspace(session, self.conn.keyspace, self.conn.replication_factor)
            session.set_keyspace(self.conn.keyspace)
            model.create_schema(session)
            resp.media = {
                'status': 'success',
                'message': f'Keyspace {self.conn.keyspace} y tablas creadas exitosamente',
                'tables': [name for name, _ in model.ALL_TABLES],
            }
            resp.status = falcon.HTTP_201
        except Exception as e:
            log.exception("Fallo al ejecutar setup")
            resp.media = {'status': 'error', 'message': str(e)}
            resp.status = falcon.HTTP_500


class DataResource:
    """
    Recurso plantilla para operaciones del nuevo modelo de datos.
    Personalizable según los requerimientos de la aplicación.
    """

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp):
        """GET /data — Consulta registros"""
        try:
            limit = req.get_param_as_int('limit') or 100
            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)
            items = model.get_all_records(session, limit=limit)
            resp.media = {'count': len(items), 'data': items}
        except Exception as e:
            log.exception("Error al consultar registros")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500

    async def on_post(self, req, resp):
        """POST /data — Inserta un registro directamente desde el JSON recibido"""
        try:
            body = await req.get_media() or {}
            if not body:
                resp.media = {'error': "Cuerpo JSON requerido"}
                resp.status = falcon.HTTP_400
                return

            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)
            resultado = model.insert_record(session, body)
            resp.media = {'status': 'created', 'item': resultado}
            resp.status = falcon.HTTP_201
        except Exception as e:
            log.exception("Error al insertar registro")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500
