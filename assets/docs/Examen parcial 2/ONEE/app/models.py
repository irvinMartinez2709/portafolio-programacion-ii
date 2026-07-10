from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    usuarios = db.relationship('User', backref='role', lazy='dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True)
    telefono = db.Column(db.String(30))
    direccion = db.Column(db.Text)
    id_zona_preferida = db.Column(db.Integer, db.ForeignKey('zonas_entrega.id'))
    foto_perfil = db.Column(db.String(255))
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), default='activo')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship('Order', foreign_keys='Order.id_cliente', backref='cliente', lazy='dynamic')
    notificaciones = db.relationship('Notification', backref='usuario', lazy='dynamic')
    zona_preferida = db.relationship('DeliveryZone', foreign_keys=[id_zona_preferida])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def rol_nombre(self):
        return self.role.nombre if self.role else ''

    def is_admin(self):
        return self.rol_nombre == 'Administrador'

    def is_cliente(self):
        return self.rol_nombre == 'Cliente'

    def is_cocina(self):
        return self.rol_nombre == 'Operario/Cocina'

    def is_repartidor(self):
        return self.rol_nombre == 'Repartidor'


class Employee(db.Model):
    __tablename__ = 'empleados'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cedula = db.Column(db.String(30))
    cargo = db.Column(db.String(80))
    salario_base = db.Column(db.Numeric(10, 2), default=0.00)
    fecha_contratacion = db.Column(db.Date)
    estado = db.Column(db.String(20), default='activo')
    usuario = db.relationship('User', backref='empleado_ref', uselist=False)
    cocinero = db.relationship('Cook', backref='empleado', uselist=False)
    repartidor = db.relationship('Driver', backref='empleado', uselist=False)


class Cook(db.Model):
    __tablename__ = 'cocineros'
    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    especialidad = db.Column(db.String(100))
    turno = db.Column(db.String(20), default='tarde')


class Driver(db.Model):
    __tablename__ = 'repartidores'
    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    tipo_vehiculo = db.Column(db.String(30), default='moto')
    placa = db.Column(db.String(20))
    id_zona_actual = db.Column(db.Integer, db.ForeignKey('zonas_entrega.id'))
    disponible = db.Column(db.Boolean, default=True)
    porcentaje_comision = db.Column(db.Numeric(5, 2), default=60.00)
    asignaciones = db.relationship('DeliveryAssignment', backref='repartidor', lazy='dynamic')
    zona_actual = db.relationship('DeliveryZone', foreign_keys=[id_zona_actual])


class ZoneChangeRequest(db.Model):
    __tablename__ = 'solicitudes_cambio_zona'
    id = db.Column(db.Integer, primary_key=True)
    id_repartidor = db.Column(db.Integer, db.ForeignKey('repartidores.id'), nullable=False)
    id_zona_anterior = db.Column(db.Integer, db.ForeignKey('zonas_entrega.id'))
    id_zona_nueva = db.Column(db.Integer, db.ForeignKey('zonas_entrega.id'), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    motivo = db.Column(db.Text)
    respuesta_admin = db.Column(db.Text)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime)
    id_admin_responde = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    repartidor = db.relationship('Driver', backref='solicitudes_zona')
    zona_anterior = db.relationship('DeliveryZone', foreign_keys=[id_zona_anterior])
    zona_nueva = db.relationship('DeliveryZone', foreign_keys=[id_zona_nueva])


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

class Pizza(db.Model):
    __tablename__ = 'pizzas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    tipo_masa = db.Column(db.String(80))
    tipo_salsa = db.Column(db.String(80))
    tipo_queso = db.Column(db.String(80))
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    imagen = db.Column(db.String(255), default='pizza_default.png')
    estado = db.Column(db.String(20), default='activa')
    ingredientes = db.relationship('Ingredient', secondary='pizza_ingredientes', backref='pizzas', lazy='dynamic')


class Ingredient(db.Model):
    __tablename__ = 'ingredientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(80))
    precio_extra = db.Column(db.Numeric(10, 2), default=0.00)
    stock = db.Column(db.Integer, default=100)
    imagen = db.Column(db.String(255))
    icono = db.Column(db.String(10), default='🧀')
    estado = db.Column(db.String(20), default='activo')


class PizzaCrust(db.Model):
    __tablename__ = 'masas_pizza'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(60), unique=True, nullable=False)
    precio_adicional = db.Column(db.Numeric(10, 2), default=0.00)
    imagen = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='activa')


class PizzaSauce(db.Model):
    __tablename__ = 'salsas_pizza'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(60), unique=True, nullable=False)
    precio_adicional = db.Column(db.Numeric(10, 2), default=0.00)
    imagen = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='activa')


pizza_ingredientes = db.Table('pizza_ingredientes',
    db.Column('id_pizza', db.Integer, db.ForeignKey('pizzas.id'), primary_key=True),
    db.Column('id_ingrediente', db.Integer, db.ForeignKey('ingredientes.id'), primary_key=True),
    db.Column('cantidad', db.String(50))
)


class Drink(db.Model):
    __tablename__ = 'refrescos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tamano = db.Column(db.String(50))
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=50)
    imagen = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='activo')


class Extra(db.Model):
    __tablename__ = 'adicionales'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    categoria = db.Column(db.String(80))
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=50)
    imagen = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='activo')


class Combo(db.Model):
    __tablename__ = 'combos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    imagen = db.Column(db.String(255), default='combo_default.png')
    estado = db.Column(db.String(20), default='activo')
    detalles = db.relationship('ComboDetail', backref='combo', lazy='dynamic', cascade='all, delete-orphan')


class ComboDetail(db.Model):
    __tablename__ = 'combo_detalle'
    id = db.Column(db.Integer, primary_key=True)
    id_combo = db.Column(db.Integer, db.ForeignKey('combos.id'), nullable=False)
    tipo_item = db.Column(db.String(20), nullable=False)
    id_item = db.Column(db.Integer, nullable=False)
    nombre_item = db.Column(db.String(120))
    cantidad = db.Column(db.Integer, default=1)


# ─── LOCATION ────────────────────────────────────────────────────────────────

class Branch(db.Model):
    __tablename__ = 'sucursales'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    direccion = db.Column(db.Text, nullable=False)
    telefono = db.Column(db.String(30))
    estado = db.Column(db.String(20), default='activa')


class District(db.Model):
    __tablename__ = 'distritos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='activo')
    corregimientos = db.relationship('Township', backref='distrito', lazy='dynamic')


class Township(db.Model):
    __tablename__ = 'corregimientos'
    id = db.Column(db.Integer, primary_key=True)
    id_distrito = db.Column(db.Integer, db.ForeignKey('distritos.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='activo')
    zonas = db.relationship('DeliveryZone', backref='corregimiento', lazy='dynamic')


class DeliveryZone(db.Model):
    __tablename__ = 'zonas_entrega'
    id = db.Column(db.Integer, primary_key=True)
    id_corregimiento = db.Column(db.Integer, db.ForeignKey('corregimientos.id'), nullable=False)
    nombre_zona = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    costo_delivery = db.Column(db.Numeric(10, 2), nullable=False)
    tiempo_estimado_min = db.Column(db.Integer, default=30)
    estado = db.Column(db.String(20), default='activa')


class DeliveryMethod(db.Model):
    __tablename__ = 'metodos_entrega'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(30), nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)


# ─── ORDERS ──────────────────────────────────────────────────────────────────

class Order(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_metodo_entrega = db.Column(db.Integer, db.ForeignKey('metodos_entrega.id'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id'), nullable=False)
    id_zona = db.Column(db.Integer, db.ForeignKey('zonas_entrega.id'), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    monto_delivery = db.Column(db.Numeric(10, 2), default=0.00)
    descuento = db.Column(db.Numeric(10, 2), default=0.00)
    impuesto = db.Column(db.Numeric(10, 2), default=0.00)
    propina = db.Column(db.Numeric(10, 2), default=0.00)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado_actual = db.Column(db.String(50), default='recibido')
    direccion_entrega = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    motivo_cancelacion = db.Column(db.Text)
    cancelado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_cancelacion = db.Column(db.DateTime)
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('OrderDetail', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')
    historial = db.relationship('OrderStatusHistory', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')
    pagos = db.relationship('Payment', backref='pedido', lazy='dynamic')
    retiro = db.relationship('LocalPickup', backref='pedido', uselist=False)
    asignacion = db.relationship('DeliveryAssignment', backref='pedido', uselist=False)
    reporte_entrega = db.relationship('DeliveryReport', backref='pedido', uselist=False)
    zona = db.relationship('DeliveryZone', backref='pedidos')
    sucursal = db.relationship('Branch', backref='pedidos')
    metodo_entrega = db.relationship('DeliveryMethod', backref='pedidos')

    @property
    def numero(self):
        return f'PF-{self.id:05d}'


class OrderDetail(db.Model):
    __tablename__ = 'pedido_detalle'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    tipo_item = db.Column(db.String(20), nullable=False)
    id_item = db.Column(db.Integer, nullable=False)
    nombre_item = db.Column(db.String(120), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    ingredientes_extra = db.Column(db.Text)  # JSON string for custom pizza ingredients


class OrderStatusHistory(db.Model):
    __tablename__ = 'pedido_estados_historial'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    actualizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_estado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_por_user = db.relationship('User', foreign_keys=[actualizado_por])


class LocalPickup(db.Model):
    __tablename__ = 'retiros_local'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id'), nullable=False)
    codigo_retiro = db.Column(db.String(20), unique=True, nullable=False)
    nombre_persona_retira = db.Column(db.String(120))
    telefono_persona_retira = db.Column(db.String(30))
    hora_estimada_retiro = db.Column(db.DateTime)
    estado = db.Column(db.String(30), default='pendiente')
    fecha_retiro = db.Column(db.DateTime)


class DeliveryAssignment(db.Model):
    __tablename__ = 'asignaciones_delivery'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    id_repartidor = db.Column(db.Integer, db.ForeignKey('repartidores.id'), nullable=False)
    monto_flete = db.Column(db.Numeric(10, 2), nullable=False)
    porcentaje_comision = db.Column(db.Numeric(5, 2), default=60.00)
    comision_repartidor = db.Column(db.Numeric(10, 2), nullable=False)
    ganancia_empresa_delivery = db.Column(db.Numeric(10, 2), nullable=False)
    propina = db.Column(db.Numeric(10, 2), default=0.00)
    estado = db.Column(db.String(20), default='asignado')
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega = db.Column(db.DateTime)

    @property
    def ganancia_total(self):
        return (self.comision_repartidor or 0) + (self.propina or 0)


class DeliveryReport(db.Model):
    __tablename__ = 'reportes_entrega'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    id_repartidor = db.Column(db.Integer, db.ForeignKey('repartidores.id'), nullable=False)
    resultado = db.Column(db.String(50), nullable=False)
    observacion_final = db.Column(db.Text)
    hora_entrega = db.Column(db.DateTime, default=datetime.utcnow)


# ─── PAYMENTS ────────────────────────────────────────────────────────────────

class Payment(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    metodo = db.Column(db.String(30), nullable=False)
    referencia = db.Column(db.String(100))
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    comprobante = db.Column(db.String(255))
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)


# ─── LOGS & SIMULATION ───────────────────────────────────────────────────────

class JsonLog(db.Model):
    __tablename__ = 'json_logs'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'))
    tipo_json = db.Column(db.String(80), nullable=False)
    contenido_json = db.Column(db.Text, nullable=False)
    archivo = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class OutboxEmail(db.Model):
    __tablename__ = 'correos_outbox'
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id'))
    destinatario = db.Column(db.String(120))
    asunto = db.Column(db.String(150))
    archivo_generado = db.Column(db.String(255))
    tipo = db.Column(db.String(10), default='json')
    fecha_generado = db.Column(db.DateTime, default=datetime.utcnow)
    estado_envio = db.Column(db.String(20), default='pendiente')
    error_envio = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime)
    cuerpo = db.Column(db.Text)


class ChatbotResponse(db.Model):
    __tablename__ = 'chatbot_respuestas'
    id = db.Column(db.Integer, primary_key=True)
    pregunta_clave = db.Column(db.String(150), nullable=False)
    respuesta = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(80))
    activo = db.Column(db.Boolean, default=True)


class SystemConfig(db.Model):
    __tablename__ = 'configuracion'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)

    @staticmethod
    def get(key, default=None):
        try:
            cfg = SystemConfig.query.filter_by(clave=key).first()
            return cfg.valor if cfg else default
        except Exception:
            return default

    @staticmethod
    def set(key, value):
        try:
            cfg = SystemConfig.query.filter_by(clave=key).first()
            if cfg:
                cfg.valor = str(value)
            else:
                cfg = SystemConfig(clave=key, valor=str(value))
                db.session.add(cfg)
            db.session.commit()
        except Exception:
            db.session.rollback()


class Notification(db.Model):
    __tablename__ = 'notificaciones_sistema'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    titulo = db.Column(db.String(150))
    mensaje = db.Column(db.Text)
    tipo = db.Column(db.String(20), default='sistema')
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    tabla_afectada = db.Column(db.String(100))
    accion = db.Column(db.String(20), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_accion = db.Column(db.DateTime, default=datetime.utcnow)
    ip_origen = db.Column(db.String(45))


class Coupon(db.Model):
    __tablename__ = 'cupones'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    tipo_descuento = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(20), default='activo')
