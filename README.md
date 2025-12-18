# 🏭 Central Norte Analytics Dashboard

**Central Norte Analytics** es una plataforma web integral de monitoreo de producción industrial. Proporciona visualización de datos en tiempo real, cálculo de KPIs, detección de paradas de máquina y generación de reportes, todo protegido bajo un sistema de autenticación robusto basado en roles.

-----

## 🚀 Características Principales

### 📊 Visualización y Monitoreo

  * **KPIs en Tiempo Real:** Visualización instantánea de producción total (bolsas), peso estimado acumulado y métricas de inactividad.
  * **Gráficos Interactivos:**
      * **Evolución de Producción:** Gráfico de línea/área con zoom y paneo para analizar tendencias temporales. Soporta curvas suaves o escalonadas.
      * **Balance de Línea:** Comparativa de barras apiladas (Entrada vs. Salida vs. Descarte).
      * **Distribución de Productos:** Gráfico de dona con desglose porcentual por tipo de producto.
  * **Detección de Paradas:** Algoritmo automático que identifica periodos de inactividad basados un umbral configurable (default: 300s) y los visualiza sobre la línea de tiempo.

### 🛠️ Herramientas de Gestión

  * **Filtros Avanzados:** Filtrado por rango de fechas/horas, turno (Mañana/Tarde/Noche), línea de producción y tipo de producto.
  * **Reportes PDF:** Generación de reportes ejecutivos directamente desde el navegador con vista previa.
  * **Configuración de UI (Admin):** Panel administrativo para habilitar/deshabilitar componentes visuales (tarjetas) para diferentes roles de usuario.

### 🔐 Seguridad y Arquitectura

  * **Control de Acceso Basado en Roles (RBAC):** Diferenciación estricta entre `Administrador` y `Cliente`.
  * **Auditoría de Seguridad:** Sistema de logging (`security_logger`) que registra intentos de login, consultas realizadas y direcciones IP, cumpliendo prácticas OWASP.
  * **Arquitectura Modular:** Separación clara entre Backend (Flask), Capa de Datos (Pandas/MySQL) y Frontend (ES6 Modules).

-----

## 🏗️ Arquitectura del Sistema

El proyecto sigue una arquitectura **MVC (Modelo-Vista-Controlador)** adaptada a una aplicación web moderna con Flask.

### Backend (Python/Flask)

  * **`app.py`:** Punto de entrada. Utiliza el patrón *Application Factory* e inicializa extensiones (LoginManager, CORS).
  * **Blueprints:**
      * `routes.py`: Endpoints de la API REST para datos del dashboard (`/api/dashboard`) y configuraciones.
      * `auth_routes.py`: Rutas de autenticación (Login/Logout).
  * **Capa de Datos:**
      * `db_manager.py`: Gestión de conexiones MySQL y caché de metadatos en memoria (evita JOINS costosos).
      * `data_processor.py`: Lógica de negocio pura. Utiliza **Pandas** para limpieza, resampleo de series temporales y cálculo de métricas.
  * **Seguridad:**
      * `auth_manager.py`: Verificación de credenciales contra base de datos.
      * `security_logger.py`: Módulo personalizado para auditoría.

### Frontend (Vanilla JS + Bootstrap 5)

El frontend utiliza **Módulos ES6** nativos para mantener el código organizado:

  * `main.js`: Controlador principal. Orquesta eventos, filtros y lógica de la página.
  * `charts.js`: Encapsula la lógica de **Chart.js** (configuración, renderizado, plugins de zoom/anotaciones).
  * `ui.js`: Manipulación del DOM, formateo de números/fechas y gestión de estados de carga.
  * `api.js`: Capa de servicio para comunicación HTTP con el backend.

-----

## 📂 Estructura del Proyecto

```text
dashboard/
├── app.py                 # Inicialización de la App Flask
├── config.py              # Configuración de entorno y base de datos
├── requirements.txt       # Dependencias de Python
├── static/
│   ├── css/               # Estilos (style.css, accessibility.css)
│   └── js/                # Módulos JavaScript (main.js, charts.js, etc.)
├── templates/             # Plantillas HTML (index.html, login.html)
├── utils/                 # Módulos de utilidad
│   ├── auth_manager.py    # Gestión de usuarios
│   ├── data_processor.py  # Procesamiento de DataFrames
│   ├── db_manager.py      # Conexión a BD
│   └── security_logger.py # Logger de seguridad
├── routes.py              # Rutas de la API
├── auth_routes.py         # Rutas de Autenticación
└── manage_users.py        # Script CLI para gestión de usuarios
```

-----

## ⚙️ Instalación y Configuración

### Prerrequisitos

  * Python 3.8+
  * MySQL Server
  * Navegador moderno (Chrome, Firefox, Edge)

### Pasos de Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <url-del-repositorio>
    cd dashboard
    ```

2.  **Crear entorno virtual e instalar dependencias:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configuración de Variables de Entorno:**
    Crear un archivo `.env` en la raíz con las credenciales de base de datos:

    ```env
    FLASK_SECRET_KEY=tu_clave_secreta_super_segura
    APP_ENV=local

    # Base de Datos de Producción
    MYSQL_HOST=localhost
    MYSQL_USER=usuario_db
    MYSQL_PASSWORD=password_db
    MYSQL_DB=nombre_db

    # Base de Datos de Autenticación
    AUTH_MYSQL_HOST=localhost
    AUTH_MYSQL_USER=usuario_auth
    AUTH_MYSQL_PASSWORD=password_auth
    AUTH_MYSQL_DB=cametcom_usuarios
    ```

4.  **Gestión de Usuarios:**
    Utilizar el script CLI incluido para crear el primer usuario administrador:

    ```bash
    python manage_users.py create admin1 mi_password administrador Camet
    ```

5.  **Ejecutar la aplicación:**

    ```bash
    python app.py
    ```

    Acceder a `http://localhost:5000`.

-----

## 🔌 API Reference

La aplicación expone una API REST interna protegida para el consumo del frontend.

### `GET /api/dashboard`

Obtiene los datos procesados para el dashboard.

  * **Parámetros:** `start` (ISO Date), `end` (ISO Date), `interval` (1h, 15min, etc.), `lines` (ID línea), `shift` (Turno).
  * **Respuesta:** JSON con metadatos, KPIs calculados, datasets para gráficos y lista de eventos de parada.

### `GET /api/ui_settings`

Obtiene la configuración de visibilidad de componentes.

  * **Respuesta:** JSON con reglas booleanas por rol (`admin`/`client`).

### `POST /api/ui_settings`

Actualiza la configuración global de la UI (Requiere rol Administrador).

-----

## 🛡️ Seguridad

  * **Protección de Contraseñas:** Uso de `bcrypt` con salting para almacenamiento de hashes.
  * **Sesiones:** Cookies `HttpOnly`, `SameSite=Lax` y `Secure` (en producción).
  * **Auditoría:** Registro detallado en base de datos de cada consulta de datos sensible, incluyendo parámetros de filtro, usuario y IP de origen.

-----

## 👥 Créditos

Desarrollado para **Central Norte** / **Camet**.

  * **Tecnologías:** Flask, Pandas, Chart.js, Bootstrap 5.