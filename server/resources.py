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


class OrderResource:
    # endpoint para crear una orden completa (orden y productos)

    def __init__(self, conn):
        self.conn = conn

    async def on_post(self, req, resp):
        """POST /orders — body: {"order": {...}, "products": [{...}, ...]}"""
        try:
            body = await req.get_media() or {}
            order_data = body.get('order')
            products = body.get('products', [])

            if not order_data:
                resp.media = {'error': "Se requiere el campo 'order' con los datos de la orden"}
                resp.status = falcon.HTTP_400
                return

            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)
            resultado = model.create_order(session, order_data, products)
            resp.media = {'status': 'created', 'order': resultado}
            resp.status = falcon.HTTP_201
        except Exception as e:
            log.exception("Error al crear la orden")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500


class OrdersByCustomerResource:
    # Q1 - ordenes de un cliente

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp, email):
        # GET /customers/{email}/orders
        try:
            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)
            items = model.get_orders_by_customer(session, email)
            resp.media = {'count': len(items), 'data': items}
        except Exception as e:
            log.exception("Error al consultar ordenes del cliente")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500


class ProductsByOrderResource:
    # Q2 - productos de una orden

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp, order_number):
        # GET /orders/{order_number}/products
        try:
            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)
            items = model.get_products_by_order(session, order_number)
            resp.media = {'count': len(items), 'data': items}
        except Exception as e:
            log.exception("Error al consultar productos de la orden")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500


class ShipmentResource:
    # endpoint para crear un shipment

    def __init__(self, conn):
        self.conn = conn

    async def on_post(self, req, resp):
        # POST /shipments
        try:
            body = await req.get_media() or {}
            if not body:
                resp.media = {'error': "Cuerpo JSON requerido"}
                resp.status = falcon.HTTP_400
                return

            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)
            resultado = model.create_shipment(session, body)
            resp.media = {'status': 'created', 'shipment': resultado}
            resp.status = falcon.HTTP_201
        except Exception as e:
            log.exception("Error al crear el shipment")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500


class ShipmentsByOrderResource:
    # Q3.1 - Q3.5 - shipments de una orden mas los filtro de cada una

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp, order_number):
        
        # GET /orders/{order_number}/shipments
        # filtros del query
        
        try:
            status = req.get_param('status')
            type_ = req.get_param('type')
            start_date = req.get_param('start_date')
            end_date = req.get_param('end_date')

            session = self.conn.session
            session.set_keyspace(self.conn.keyspace)

            # elegimos la funcion segun que filtros vinieron
            if type_ and status:
                items = model.get_shipments_by_order_type_and_status(
                    session, order_number, type_, status, start_date, end_date)
            elif type_:
                items = model.get_shipments_by_order_and_type(
                    session, order_number, type_, start_date, end_date)
            elif status:
                items = model.get_shipments_by_order_and_status(
                    session, order_number, status, start_date, end_date)
            elif start_date and end_date:
                items = model.get_shipments_by_order_and_date_range(
                    session, order_number, start_date, end_date)
            else:
                items = model.get_shipments_by_order(session, order_number)

            resp.media = {'count': len(items), 'data': items}
        except Exception as e:
            log.exception("Error al consultar shipments de la orden")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500
