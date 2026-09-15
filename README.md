# ITESO BDNR - Cassandra Sample (Rama Esqueleto)

Plantilla y arquitectura base modular diseñada para implementar de forma sencilla cualquier modelo de datos en Apache Cassandra, utilizando una arquitectura cliente-servidor con una API REST en Python (Falcon ASGI) y un cliente de consola interactivo.

---

## Arquitectura

```
┌────────────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐
│     Cliente Python     │ HTTP  │        Servidor        │ CQL   │       Cassandra        │
│    (client/menu.py)    │ ────► │      (API REST /       │ ────► │     (Docker / Nodo)    │
│                        │       │      Falcon ASGI)      │       │                        │
└────────────────────────┘       └────────────────────────┘       └────────────────────────┘
         client/                          server/                         puerto 9042
```

---

## Estructura del Proyecto

```
iteso-bdnr-cassandra-sample/
├── client/
│   └── menu.py         # Menú interactivo de consola para realizar peticiones REST
├── server/
│   ├── app.py          # Configuración de la aplicación Falcon ASGI y rutas
│   ├── resources.py    # Controladores de endpoints REST (Health, Setup, Data)
│   └── model.py        # Conexión a Cassandra, creación de keyspace/tablas y consultas
├── requirements.txt    # Dependencias del proyecto (servidor y cliente)
└── README.md
```

---

## Cómo implementar cualquier modelo de datos

Esta plantilla permite adaptar el proyecto a cualquier caso de uso (por ejemplo: catálogo de canciones, usuarios, sensores, inventario, etc.) en tres pasos:

1. **Definir tu esquema en [server/model.py](server/model.py)**:
   - Modifica o agrega sentencias CQL en `CREATE_..._TABLE`.
   - Registra cada tabla en la lista `ALL_TABLES = [('nombre_tabla', CREATE_..._TABLE)]`.
   - Implementa o personaliza tus funciones de consulta e inserción (`insert_dict`, `insert_record`, `get_all_records`).
2. **Personalizar endpoints en [server/resources.py](server/resources.py) y [server/app.py](server/app.py)**:
   - Modifica `DataResource` o crea nuevos recursos Falcon según las entidades de tu modelo.
   - Registra o actualiza las rutas con `app.add_route('/ruta', recurso)`.
3. **Interactuar desde el cliente en [client/menu.py](client/menu.py)**:
   - Agrega o ajusta las opciones del menú para llamar a los nuevos endpoints de tu API.

---

## Puesta en Marcha

Se recomienda trabajar con **2 terminales**: una para mantener en ejecución el servidor ASGI y otra para utilizar el menú interactivo.

### 1. Iniciar Cassandra con Docker

```bash
docker run --name cassandra -p 9042:9042 -d cassandra

# Esperar aproximadamente 60 segundos a que el nodo termine de inicializar y verificar:
docker exec -it cassandra cqlsh -e "describe cluster"
```

### 2. Entorno Virtual e Instalación de Dependencias

```bash
# Crear entorno virtual (si no existe)
python3 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate       # En Linux / macOS
# .venv\Scripts\activate        # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Iniciar el Servidor de la API REST

En la primera terminal:

```bash
cd server
uvicorn app:app --reload --port 8001
```

El servidor quedará disponible en `http://localhost:8001`.

### 4. Ejecutar el Cliente Interactivo

En la segunda terminal (con el entorno virtual activado):

```bash
cd client
python menu.py
```

O directamente desde la raíz del repositorio:
```bash
python client/menu.py
```

---

## Opciones del Cliente Interactivo (`menu.py`)

El cliente por consola ofrece un menú en bucle que permite probar de inmediato las operaciones básicas:

| Opción | Acción | Petición REST |
|--------|--------|---------------|
| **1** | Verificar estado del servidor | `GET /health` |
| **2** | Inicializar esquema de base de datos | `POST /setup` (crea keyspace y tablas DDL) |
| **3** | Consultar registros | `GET /data` |
| **4** | Insertar un nuevo registro | `POST /data` (solicita los campos e inserta) |
| **0** | Salir | Cierra el programa |

---

## Endpoints REST Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/health` | Verifica la salud del servicio y el estado de la conexión a Cassandra |
| `POST` | `/setup`  | Ejecuta el DDL para crear el keyspace y las tablas en `ALL_TABLES` |
| `GET`  | `/data`   | Obtiene la lista de registros almacenados (parámetro opcional: `?limit=N`) |
| `POST` | `/data`   | Inserta un nuevo registro directamente a partir de un cuerpo JSON |

### Ejemplos con `curl`

```bash
# 1. Comprobar salud del servicio
curl http://localhost:8001/health

# 2. Crear keyspace y tablas
curl -X POST http://localhost:8001/setup

# 3. Consultar registros existentes
curl http://localhost:8001/data

# 4. Insertar un registro
curl -X POST http://localhost:8001/data \
  -H "Content-Type: application/json" \
  -d '{"id": "1", "nombre": "Elemento A", "categoria": "General", "valor": "99.9"}'
```

---

## Variables de Entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `API_URL` | `http://localhost:8001` | URL base de la API utilizada por el cliente |
| `CASSANDRA_HOST` | `localhost` | Host o dirección IP del nodo de Cassandra |
| `CASSANDRA_PORT` | `9042` | Puerto CQL de conexión |
| `CASSANDRA_KEYSPACE` | `app_keyspace` | Nombre del keyspace a utilizar en Cassandra |
| `CASSANDRA_REPLICATION_FACTOR` | `1` | Factor de replicación para el keyspace |

---

## Solución de Problemas

- **"No se pudo conectar con el servidor"**: Asegúrate de haber iniciado el servidor con `uvicorn app:app --reload --port 8001` dentro de la carpeta `server/`.
- **"Failed to connect to Cassandra"**: Cassandra suele tardar entre 40 y 60 segundos en iniciar en Docker. Revisa el estado de inicio con `docker logs cassandra`.
- **"ModuleNotFoundError: No module named 'requests'"**: Verifica que tu terminal tenga activo el entorno virtual (`source .venv/bin/activate`).
