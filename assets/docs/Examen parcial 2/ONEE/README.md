# CHINOS CAFE PIZZAFLOW

Sistema web Flask para pedidos de pizzeria con roles de cliente, administrador, cocina y repartidor.

## Requisitos

- Python 3.10 o superior
- PyCharm o terminal
- SQLite para desarrollo

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Abrir:

```text
http://127.0.0.1:5000
```

## Acceso local

El seed crea usuarios de prueba para desarrollo local. Cambia sus contrasenas desde el panel de administrador antes de exponer el sistema en una red o servidor.

Usuarios iniciales:

- admin
- cliente
- cocina
- repartidor

Las contrasenas demo se crean solo para desarrollo. Si vas a publicar el sistema, entra como administrador, cambia esas contrasenas y configura `SECRET_KEY` en `.env`.

## Seguridad y credenciales

El ZIP no incluye `.env` ni credenciales reales. Configura correo en tu `.env` local:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=tu_app_password
MAIL_DEFAULT_SENDER=tu_correo@gmail.com
```

La pantalla admin de SMTP muestra datos simulados, pero no expone contrasenas. `MAIL_PASSWORD` se lee desde variables de entorno.

Tambien se incluye:

- Flask-WTF con CSRF en formularios POST.
- Rutas protegidas por rol.
- Validacion de archivos para comprobantes e imagenes.
- Handlers 403, 404 y 500.
- `.gitignore` para evitar subir `.env`, base de datos, outbox, venv y uploads.

## Flujo de pedido

1. Cliente crea pedido.
2. Cliente registra pago Yappy/tarjeta o efectivo.
3. Cocina avanza: recibido, en preparacion, en horno, listo.
4. Admin asigna repartidor solo cuando el pedido esta listo.
5. Repartidor marca en camino.
6. Repartidor registra reporte y marca entregado.

Reglas principales:

- Repartidor no puede salir si cocina no marco listo y admin no asigno.
- Repartidor no puede entregar si el pedido no esta en camino.
- Admin no puede asignar delivery sin pago confirmado, salvo efectivo.
- Cliente solo puede cancelar antes de preparacion.
- Admin puede cancelar con motivo; si ya estaba pagado, se genera reembolso simulado.
- Cocina puede cancelar pedidos no entregados con motivo; se registra usuario, fecha y notificacion simulada al cliente.
- Propina permitida: 0%, 5%, 10%, 15% o monto manual. El backend limita a 30% del subtotal o $20, lo que sea menor.

## Registro y perfiles

- `/auth/register` permite registrar clientes con correo unico y contrasena hasheada.
- Cliente puede editar nombre, telefono, direccion, zona preferida, foto y contrasena en `/cliente/perfil`.
- Repartidor puede editar telefono y solicitar cambio de zona en `/repartidor/perfil`.
- Admin aprueba o rechaza solicitudes de zona en `/admin/repartidores/solicitudes`.

## Comprobantes Yappy

Formatos permitidos: PNG, JPG, JPEG y PDF.
Tamano maximo: 5 MB.
Ubicacion:

```text
app/static/uploads/payments/
```

## Outbox y JSON

El sistema trabaja en modo offline por defecto. En vez de enviar correos reales, genera JSON y registros de outbox para:

- pedido_cliente
- pedido_empresa
- pedido_operario
- pago_empresa
- cancelacion
- reembolso
- entrega

Carpeta:

```text
outbox/
```

Panel admin:

```text
/admin/outbox
/admin/json
```

## Imagenes

No se generan imagenes. Coloca assets reales en:

```text
app/static/img/
```

Estructura preparada para el constructor visual:

```text
branding/
pizza/masas/
pizza/salsas/
pizza/ingredientes/
yappy/
users/
delivery/
placeholders/
```

Ver `app/static/img/README.md` para medidas y reglas de nombres.

El constructor visual usa imagenes transparentes por pieza. No usa Canvas, SVG ni imagenes completas de pizza por ingrediente. Cada topping se replica con JavaScript y se distribuye dentro del circulo segun cantidad y ubicacion.

El panel admin ahora permite mantener catalogos:

- Pizzas
- Masas
- Salsas
- Ingredientes
- Refrescos
- Adicionales
- Combos
- Zonas
- Usuarios, clientes, cocina y repartidores

## Cache de navegador

CSS y JS usan `ASSET_VERSION` como parametro `v`. En desarrollo tambien se activan headers `no-cache`.

Para limpiar cache:

- Chrome/Edge: Ctrl + Shift + R
- O borrar cache del navegador desde herramientas de desarrollo
- Cambiar `ASSET_VERSION` en `.env`

## Rutas principales

```text
/                         Home publica
/menu                     Menu publico
/auth/login               Login
/auth/register            Registro de cliente
/cliente/dashboard        Panel cliente
/cliente/nuevo-pedido     Crear pedido
/cliente/pizza-builder    Builder por capas
/cliente/mis-pedidos      Pedidos del cliente
/cliente/perfil           Perfil cliente
/cocina/dashboard         Kanban de cocina
/repartidor/dashboard     Panel repartidor
/repartidor/perfil        Perfil repartidor
/admin/dashboard          Dashboard admin
/admin/usuarios           Usuarios
/admin/clientes           Clientes
/admin/repartidores       Repartidores
/admin/cocina-personal    Cocina
/admin/masas              Masas del constructor
/admin/salsas             Salsas del constructor
/admin/pedidos            Todos los pedidos
/admin/pagos              Pagos y comprobantes
/admin/json               Visor JSON
/admin/configuracion      Configuracion sistema/SMTP
```

## Preparacion para MariaDB

En produccion cambia `DATABASE_URL`:

```env
DATABASE_URL=mysql+pymysql://usuario:password@localhost/chinos_cafe
```

Instala el driver correspondiente y usa un servidor WSGI detras de NGINX. No uses el servidor de desarrollo de Flask en produccion.

---

## Rutas de imágenes — Branding y Menú

Coloca tus archivos en las siguientes rutas para que el sistema los encuentre automáticamente:

### Branding
| Propósito       | Ruta                                        |
|-----------------|---------------------------------------------|
| Logo            | `app/static/img/branding/logo.png`          |
| Favicon         | `app/static/img/branding/favicon.ico`       |
| Banner home     | `app/static/img/branding/banner-home.webp`  |
| Fondo login     | `app/static/img/branding/bg-login.webp`     |
| Fondo admin     | `app/static/img/branding/bg-admin.webp`     |

### Pizza
| Propósito       | Ruta                                           |
|-----------------|------------------------------------------------|
| Masas           | `app/static/img/pizza/masas/`                  |
| Salsas          | `app/static/img/pizza/salsas/`                 |
| Ingredientes    | `app/static/img/pizza/ingredientes/`           |

### Menú
| Propósito       | Ruta                                           |
|-----------------|------------------------------------------------|
| Refrescos       | `app/static/img/menu/refrescos/`               |
| Adicionales     | `app/static/img/menu/adicionales/`             |
| Combos          | `app/static/img/menu/combos/`                  |

### Perfiles
| Propósito             | Ruta                                               |
|-----------------------|----------------------------------------------------|
| Fotos de clientes     | `app/static/uploads/profiles/clientes/`            |
| Fotos de repartidores | `app/static/uploads/profiles/repartidores/`        |
| Fotos de staff/cocina | `app/static/uploads/profiles/staff/`               |

---

## ¿Funciona sin base de datos?

**No.** El servidor Flask inicia, pero cualquier ruta que use la base de datos lanzará un error 500.

### Partes que NO funcionan sin base de datos
- Login / registro
- Panel de administrador
- Constructor de pizza
- Carrito y pedidos
- Panel de repartidor y cocina

### Inicializar la base de datos SQLite

```bash
# 1. Copia el archivo de entorno
copy .env.example .env    # Windows
cp .env.example .env      # Linux/Mac

# 2. Edita .env y asegúrate de tener:
DATABASE_URL=sqlite:///pizzaflow.db
SECRET_KEY=cambia_esto_por_una_clave_secreta

# 3. Inicia el servidor (crea tablas automáticamente)
python run.py
```

### Crear datos demo / seed

```bash
# En otra terminal con el entorno activado:
python -c "from app import create_app; from app.seed import seed_all; app=create_app(); app.app_context().push(); seed_all()"
```

O usando Flask shell:

```bash
flask shell
>>> from app.seed import seed_all
>>> seed_all()
```

### Comando rápido para probar

```bash
python run.py
# Abrir http://127.0.0.1:5000
```

---

## Cómo migrar de SQLite a MariaDB

### 1. Instalar MariaDB

```bash
# Ubuntu/Debian
sudo apt install mariadb-server
sudo mysql_secure_installation

# Windows: descargar instalador desde https://mariadb.org/download/
```

### 2. Crear base de datos y usuario

```sql
CREATE DATABASE pizzaflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tu_usuario'@'localhost' IDENTIFIED BY 'tu_contraseña';
GRANT ALL PRIVILEGES ON pizzaflow.* TO 'tu_usuario'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Instalar driver Python

Agrega a `requirements.txt`:
```
PyMySQL>=1.1.0
```

O instala directamente:
```bash
pip install PyMySQL
```

### 4. Configurar DATABASE_URL en `.env`

```env
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost/pizzaflow
```

> **Nunca pongas credenciales reales en el repositorio.** Usa siempre `.env` y asegúrate de que `.gitignore` lo excluya.

### 5. Ejemplo de DATABASE_URL (sin credenciales reales)

```
DATABASE_URL=mysql+pymysql://USUARIO:CONTRASEÑA@localhost/pizzaflow
```

### 6. Inicializar tablas en MariaDB

```bash
python run.py
# Flask-SQLAlchemy creará las tablas automáticamente en el primer inicio
```

---

## Regla de ganancias del repartidor

| Concepto           | Detalle                                                       |
|--------------------|---------------------------------------------------------------|
| Comisión base      | % configurado en el perfil del repartidor (default 60%)       |
| Cálculo            | `comision = monto_flete × porcentaje / 100`                   |
| Propina            | Se suma completa a la ganancia del repartidor                 |
| Ganancia total     | `comision + propina`                                          |
| Solo cuenta        | Pedidos con estado `entregado`                                |
| No cuenta          | Pedidos cancelados, pendientes, o en camino                   |
| Ganancia mínima    | $2.00 si el flete es $0 (entregas especiales)                 |

---

## Seguridad

- `SECRET_KEY` se lee desde variable de entorno `.env` — nunca hardcodeada
- `DATABASE_URL` se lee desde `.env`
- Credenciales SMTP se leen desde `.env`
- `.gitignore` excluye `.env`, `*.db`, `__pycache__`, uploads
- Todas las rutas de admin están protegidas con `@require_admin`
- Rutas de repartidor protegidas con `@require_repartidor`
- CSRF token en todos los formularios POST

