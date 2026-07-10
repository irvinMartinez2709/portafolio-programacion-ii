"""
Datos semilla para demostración de CHINOS CAFÉ PIZZAFLOW.
Ejecutar después de crear las tablas.
"""
from decimal import Decimal
from datetime import date, datetime
from app.extensions import db
from app.models import (Role, User, Employee, Cook, Driver, Pizza, Ingredient,
                        PizzaCrust, PizzaSauce,
                        Drink, Extra, Combo, ComboDetail, Branch, District,
                        Township, DeliveryZone, DeliveryMethod, SystemConfig,
                        ChatbotResponse)


def seed_all():
    print("[seed] Iniciando seed de datos...")

    _seed_config()
    _seed_roles()
    _seed_users()
    _seed_employees()
    _seed_products()
    _seed_locations()
    _seed_chatbot()
    _seed_combos()

    print("[seed] Seed completado exitosamente.")


def _seed_config():
    configs = [
        ('nombre_empresa', 'CHINOS CAFÉ S.A.', 'Nombre de la empresa'),
        ('yappy_numero', '6000-1234', 'Número Yappy Comercial'),
        ('correo_empresa', 'pedidos@chinoscafe.pa', 'Correo principal empresa'),
        ('correo_operario', 'cocina@chinoscafe.pa', 'Correo de cocina'),
        ('min_ingredientes', '2', 'Mínimo de ingredientes por pizza'),
        ('max_ingredientes', '10', 'Máximo de ingredientes por pizza'),
        ('porcentaje_comision', '60', 'Comisión default repartidor (%)'),
        ('impuesto', '7', 'ITBMS (%)'),
        ('modo_offline', 'true', 'Sistema en modo offline'),
        ('mail_server', 'smtp.gmail.com', 'Servidor SMTP'),
        ('mail_port', '587', 'Puerto SMTP'),
        ('mail_use_tls', 'true', 'TLS SMTP'),
        ('mail_username', '', 'Usuario SMTP'),
        ('mail_default_sender', '', 'Remitente SMTP'),
        ('costo_base_delivery', '2.00', 'Costo base delivery'),
        ('color_primario', '#1f3d2b', 'Color principal'),
        ('home_titulo', 'CHINOS CAFE PIZZAFLOW', 'Titulo principal de home'),
    ]
    for clave, valor, desc in configs:
        if not SystemConfig.query.filter_by(clave=clave).first():
            db.session.add(SystemConfig(clave=clave, valor=valor, descripcion=desc))
    db.session.commit()
    print("  OK Configuracion")


def _seed_roles():
    roles = [
        ('Cliente', 'Usuario final que realiza pedidos'),
        ('Administrador', 'Control total del sistema'),
        ('Operario/Cocina', 'Gestiona preparación de pedidos'),
        ('Repartidor', 'Entrega pedidos a domicilio'),
    ]
    for nombre, desc in roles:
        if not Role.query.filter_by(nombre=nombre).first():
            db.session.add(Role(nombre=nombre, descripcion=desc))
    db.session.commit()
    print("  OK Roles")


def _seed_users():
    users_data = [
        ('Administrador', 'Carlos Chinos', 'admin@chinoscafe.pa', '6600-0001', 'admin', 'admin123'),
        ('Cliente',       'María González', 'cliente@ejemplo.pa', '6600-0002', 'cliente', 'cliente123'),
        ('Operario/Cocina','Pedro Cocina',  'cocina@chinoscafe.pa','6600-0003', 'cocina', 'cocina123'),
        ('Repartidor',    'Juan Reparto',   'reparto@chinoscafe.pa','6600-0004','repartidor','reparto123'),
        ('Cliente',       'Ana Morales',    'ana@ejemplo.pa',    '6600-0005', 'ana', 'ana123'),
    ]
    for rol_n, nombre, correo, tel, usuario, pwd in users_data:
        if not User.query.filter_by(usuario=usuario).first():
            rol = Role.query.filter_by(nombre=rol_n).first()
            u = User(id_rol=rol.id, nombre=nombre, correo=correo,
                     telefono=tel, usuario=usuario)
            u.set_password(pwd)
            db.session.add(u)
    db.session.commit()
    print("  OK Usuarios")


def _seed_employees():
    # Empleados para cocina y repartidor
    cocina_user = User.query.filter_by(usuario='cocina').first()
    rep_user    = User.query.filter_by(usuario='repartidor').first()

    if cocina_user and not Employee.query.filter_by(id_usuario=cocina_user.id).first():
        emp_c = Employee(id_usuario=cocina_user.id, cedula='8-100-100',
                         cargo='Operario de Cocina', salario_base=Decimal('600.00'),
                         fecha_contratacion=date(2023, 1, 15))
        db.session.add(emp_c)
        db.session.flush()
        db.session.add(Cook(id_empleado=emp_c.id, especialidad='Pizzas artesanales', turno='tarde'))

    if rep_user and not Employee.query.filter_by(id_usuario=rep_user.id).first():
        emp_r = Employee(id_usuario=rep_user.id, cedula='8-200-200',
                         cargo='Repartidor', salario_base=Decimal('400.00'),
                         fecha_contratacion=date(2023, 3, 1))
        db.session.add(emp_r)
        db.session.flush()
        db.session.add(Driver(id_empleado=emp_r.id, tipo_vehiculo='moto',
                               placa='CH-1234', disponible=True,
                               porcentaje_comision=Decimal('60.00')))

    db.session.commit()
    print("  OK Empleados")


def _seed_products():
    # Ingredientes
    ingredientes = [
        ('Pepperoni',      'Carnes',       0.75, '🍖', 100),
        ('Jamón',          'Carnes',       0.60, '🥩', 100),
        ('Pollo asado',    'Carnes',       0.80, '🍗', 80),
        ('Champiñones',    'Vegetales',    0.40, '🍄', 100),
        ('Pimientos rojos','Vegetales',    0.35, '🌶️', 100),
        ('Cebolla',        'Vegetales',    0.25, '🧅', 100),
        ('Aceitunas negras','Vegetales',   0.50, '🫒', 80),
        ('Tomate fresco',  'Vegetales',    0.30, '🍅', 100),
        ('Queso extra',    'Quesos',       0.65, '🧀', 100),
        ('Mozzarella',     'Quesos',       0.60, '🧀', 100),
        ('Albahaca fresca','Hierbas',      0.20, '🌿', 80),
        ('Orégano extra',  'Hierbas',      0.15, '🌿', 100),
        ('Piña',           'Frutas',       0.40, '🍍', 80),
        ('Maíz',           'Vegetales',    0.30, '🌽', 100),
        ('Salsa BBQ extra','Salsas',       0.45, '🫙', 80),
    ]
    for nombre, cat, precio, icono, stock in ingredientes:
        if not Ingredient.query.filter_by(nombre=nombre).first():
            db.session.add(Ingredient(nombre=nombre, categoria=cat,
                                      precio_extra=Decimal(str(precio)),
                                      icono=icono, stock=stock))

    masas = [
        ('Masa delgada', 'delgada', Decimal('0.00'), 'img/pizza/masas/masa_delgada.webp'),
        ('Masa tradicional', 'tradicional', Decimal('0.00'), 'img/pizza/masas/masa_tradicional.webp'),
        ('Masa pan pizza', 'pan', Decimal('1.00'), 'img/pizza/masas/masa_pan.webp'),
    ]
    for nombre, codigo, precio, imagen in masas:
        if not PizzaCrust.query.filter_by(codigo=codigo).first():
            db.session.add(PizzaCrust(nombre=nombre, codigo=codigo,
                                      precio_adicional=precio, imagen=imagen))

    salsas = [
        ('Salsa de tomate', 'tomate', Decimal('0.00'), 'img/pizza/salsas/salsa_tomate.webp'),
        ('Salsa ranch', 'ranch', Decimal('0.50'), 'img/pizza/salsas/salsa_ranch.webp'),
        ('Salsa garlic', 'garlic', Decimal('0.50'), 'img/pizza/salsas/salsa_garlic.webp'),
    ]
    for nombre, codigo, precio, imagen in salsas:
        if not PizzaSauce.query.filter_by(codigo=codigo).first():
            db.session.add(PizzaSauce(nombre=nombre, codigo=codigo,
                                      precio_adicional=precio, imagen=imagen))

    # Pizzas
    pizzas = [
        ('Margarita Clásica',    'La clásica italiana con tomate, mozzarella y albahaca',    'Delgada', 'Tomate', 'Mozzarella',  Decimal('8.99')),
        ('Pepperoni Suprema',    'Cargada de pepperoni premium y queso derretido',           'Gruesa',  'Tomate', 'Mozzarella',  Decimal('10.99')),
        ('Hawaiana Tropical',    'Combinación perfecta de jamón y piña dulce',               'Delgada', 'Tomate', 'Mozzarella',  Decimal('9.99')),
        ('BBQ Pollo',            'Pollo asado con salsa BBQ ahumada y cebolla caramelizada', 'Gruesa',  'BBQ',    'Mozzarella',  Decimal('11.99')),
        ('Vegetariana Garden',   'Fresca mezcla de vegetales sobre base de tomate',          'Delgada', 'Tomate', 'Mozzarella',  Decimal('9.49')),
        ('Cuatro Quesos',        'Explosión de mozzarella, cheddar, gouda y parmesano',      'Gruesa',  'Tomate', 'Cuatro quesos',Decimal('12.99')),
    ]
    for nombre, desc, masa, salsa, queso, precio in pizzas:
        if not Pizza.query.filter_by(nombre=nombre).first():
            db.session.add(Pizza(nombre=nombre, descripcion=desc, tipo_masa=masa,
                                  tipo_salsa=salsa, tipo_queso=queso, precio_base=precio))

    # Refrescos
    bebidas = [
        ('Coca-Cola', '355ml', Decimal('1.25')),
        ('Pepsi',     '355ml', Decimal('1.25')),
        ('Sprite',    '355ml', Decimal('1.25')),
        ('Agua Purificada', '500ml', Decimal('0.75')),
        ('Jugo de Naranja', '400ml', Decimal('1.50')),
        ('Limonada Natural','400ml', Decimal('1.75')),
    ]
    for nombre, tamano, precio in bebidas:
        if not Drink.query.filter_by(nombre=nombre).first():
            db.session.add(Drink(nombre=nombre, tamano=tamano, precio=precio))

    # Adicionales
    adicionales = [
        ('Pan de Ajo',     'Crujiente pan de ajo con mantequilla y hierbas', Decimal('1.50')),
        ('Salsa Ranch',    'Aderezo cremoso ranch',                          Decimal('0.75')),
        ('Salsa BBQ',      'Salsa ahumada barbacoa',                         Decimal('0.75')),
        ('Papas Crinkle',  'Papas onduladas crujientes',                     Decimal('2.50')),
        ('Alitas de Pollo','6 alitas con salsa de tu elección',              Decimal('5.99')),
        ('Queso Dip',      'Dip de queso fundido con jalapeños',             Decimal('1.25')),
    ]
    for nombre, desc, precio in adicionales:
        if not Extra.query.filter_by(nombre=nombre).first():
            db.session.add(Extra(nombre=nombre, descripcion=desc, precio=precio))

    db.session.commit()
    print("  OK Productos")


def _seed_locations():
    # Sucursal
    if not Branch.query.first():
        db.session.add(Branch(
            nombre='CHINOS CAFÉ - David Centro',
            direccion='Av. Obaldía, frente al Parque Miguel de Cervantes, David, Chiriquí',
            telefono='774-0000',
        ))

    # Métodos de entrega
    for nombre, desc in [('delivery', 'Entrega a domicilio'), ('retiro_local', 'Retiro en sucursal')]:
        if not db.session.execute(
            db.select(DeliveryMethod).filter_by(nombre=nombre)
        ).scalar_one_or_none():
            db.session.add(DeliveryMethod(nombre=nombre, descripcion=desc))

    # Distrito
    if not District.query.filter_by(nombre='David').first():
        david = District(nombre='David')
        db.session.add(david)
        db.session.flush()

        corregimientos = ['David', 'Pedregal', 'San Pablo Nuevo', 'San Pablo Viejo',
                          'Las Lomas', 'Chiriquí', 'Guacá', 'Doleguita']
        for nombre_c in corregimientos:
            db.session.add(Township(id_distrito=david.id, nombre=nombre_c))
        db.session.flush()

        zonas = [
            ('David', 'David Centro',    'Zona céntrica de David',  Decimal('2.00'), 20),
            ('David', 'San Mateo',       'Sector San Mateo',        Decimal('2.50'), 25),
            ('Doleguita', 'Doleguita',   'Corregimiento Doleguita', Decimal('2.25'), 25),
            ('Pedregal', 'Pedregal',     'Corregimiento Pedregal',  Decimal('3.00'), 30),
            ('Las Lomas', 'Las Lomas',   'Sector Las Lomas',        Decimal('3.50'), 35),
            ('San Pablo Viejo', 'San Pablo Viejo', 'San Pablo Viejo', Decimal('3.75'), 40),
            ('San Pablo Nuevo', 'San Pablo Nuevo', 'San Pablo Nuevo', Decimal('3.75'), 40),
            ('Chiriquí', 'Chiriquí',     'Corregimiento Chiriquí',  Decimal('4.00'), 45),
            ('Guacá', 'Guacá',           'Sector Guacá',            Decimal('4.50'), 50),
        ]
        for corr_nombre, zona_nombre, desc, costo, tiempo in zonas:
            corr = Township.query.filter_by(nombre=corr_nombre, id_distrito=david.id).first()
            if corr:
                db.session.add(DeliveryZone(
                    id_corregimiento=corr.id,
                    nombre_zona=zona_nombre,
                    descripcion=desc,
                    costo_delivery=costo,
                    tiempo_estimado_min=tiempo,
                ))

    db.session.commit()
    driver = Driver.query.first()
    zona = DeliveryZone.query.filter_by(nombre_zona='David Centro').first()
    if driver and zona and not driver.id_zona_actual:
        driver.id_zona_actual = zona.id
        db.session.commit()
    print("  OK Ubicaciones")


def _seed_chatbot():
    respuestas = [
        ('que pizzas,pizzas tienen,menu pizzas', 'Tenemos Margarita Clásica, Pepperoni Suprema, Hawaiana, BBQ Pollo, Vegetariana y Cuatro Quesos. ¡Todas deliciosas! 🍕', 'productos'),
        ('cuanto cuesta delivery,precio envio,costo flete', 'El delivery varía según tu zona: David Centro $2.00, San Mateo $2.50, Pedregal $3.00, Las Lomas $3.50 y más. 🛵', 'delivery'),
        ('aceptan yappy,pago yappy,como pagar', '¡Claro que sí! Aceptamos Yappy Comercial, efectivo y tarjeta. Comercio: CHINOS CAFÉ S.A. 💳', 'pagos'),
        ('estado pedido,donde esta,rastrear pedido', 'Para ver tu pedido, inicia sesión y ve a "Mis Pedidos". Verás el timeline en tiempo real. 📦', 'pedidos'),
        ('que combos,combos disponibles,ofertas', '¡Tenemos combos increíbles! Combo Familiar, Combo Pareja y más. ¡Revisa la sección de Combos! 🎁', 'productos'),
        ('cuanto gana repartidor,comision repartidor', 'Nuestros repartidores ganan el 60% del flete más las propinas del cliente. ¡Un ingreso justo! 💰', 'empresa'),
        ('horario,que horas,cuando abren', 'Atendemos de Lunes a Domingo de 11:00 AM a 10:00 PM. 🕐', 'empresa'),
        ('telefono,contacto,numero', 'Llámanos al 774-0000 o escríbenos aquí. Estamos en Av. Obaldía, David. 📞', 'empresa'),
    ]
    for clave, resp, cat in respuestas:
        if not ChatbotResponse.query.filter_by(pregunta_clave=clave).first():
            db.session.add(ChatbotResponse(pregunta_clave=clave, respuesta=resp, categoria=cat))
    db.session.commit()
    print("  OK ChinoBot")


def _seed_combos():
    pizza = Pizza.query.filter_by(nombre='Pepperoni Suprema').first()
    bebida = Drink.query.filter_by(nombre='Coca-Cola').first()
    adicional = Extra.query.filter_by(nombre='Pan de Ajo').first()

    combos_data = [
        ('Combo Pareja',    'Pizza mediana + 2 refrescos + pan de ajo', Decimal('18.99')),
        ('Combo Familiar',  '2 Pizzas + 4 refrescos + 2 adicionales',   Decimal('34.99')),
        ('Combo Personal',  'Pizza personal + refresco',                 Decimal('11.99')),
    ]
    for nombre, desc, precio in combos_data:
        if not Combo.query.filter_by(nombre=nombre).first():
            c = Combo(nombre=nombre, descripcion=desc, precio=precio)
            db.session.add(c)
            db.session.flush()
            if pizza:
                db.session.add(ComboDetail(id_combo=c.id, tipo_item='pizza',
                                            id_item=pizza.id, nombre_item=pizza.nombre, cantidad=1))
            if bebida:
                db.session.add(ComboDetail(id_combo=c.id, tipo_item='refresco',
                                            id_item=bebida.id, nombre_item=bebida.nombre, cantidad=1))
    db.session.commit()
    print("  OK Combos")
