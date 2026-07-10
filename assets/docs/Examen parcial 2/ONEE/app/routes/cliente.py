import json
import unicodedata
from decimal import Decimal
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Pizza, Ingredient, PizzaCrust, PizzaSauce, Drink, Extra, Combo, DeliveryZone, DeliveryMethod,
    Order, OrderDetail, OrderStatusHistory, Payment, LocalPickup,
    SystemConfig, Notification, Branch
)
from app.utils.calculations import calcular_total_pedido
from app.utils.email_simulator import (
    simular_correos_pedido, simular_correo_pago, simular_correo_cancelacion
)
from app.utils.file_uploads import save_payment_receipt
from app.utils.file_uploads import save_image_upload

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')


def require_cliente(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.rol_nombre not in ('Cliente', 'Administrador'):
            flash('Acceso no autorizado.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated


@cliente_bp.route('/dashboard')
@login_required
@require_cliente
def dashboard():
    pedidos = Order.query.filter_by(id_cliente=current_user.id).order_by(Order.fecha_pedido.desc()).limit(5).all()
    notifs = Notification.query.filter_by(id_usuario=current_user.id, leida=False).order_by(Notification.fecha_creacion.desc()).limit(5).all()
    return render_template('cliente/dashboard.html', pedidos=pedidos, notifs=notifs)


@cliente_bp.route('/pizzas')
@login_required
@require_cliente
def ver_pizzas():
    pizzas = Pizza.query.filter_by(estado='activa').all()
    combos = Combo.query.filter_by(estado='activo').all()
    return render_template('cliente/pizzas.html', pizzas=pizzas, combos=combos)


@cliente_bp.route('/pizza-builder')
@login_required
@require_cliente
def pizza_builder():
    try:
        min_ing = int(SystemConfig.get('min_ingredientes', 2))
        max_ing = int(SystemConfig.get('max_ingredientes', 10))
        ingredientes = Ingredient.query.filter_by(estado='activo').all()
        bebidas = Drink.query.filter_by(estado='activo').all()
        adicionales = Extra.query.filter_by(estado='activo').all()
        pizzas_base = Pizza.query.filter_by(estado='activa').all()
        masas_db = PizzaCrust.query.filter_by(estado='activa').order_by(PizzaCrust.nombre).all()
        salsas_db = PizzaSauce.query.filter_by(estado='activa').order_by(PizzaSauce.nombre).all()
    except Exception as e:
        flash(f'Error cargando ingredientes: {e}', 'danger')
        min_ing, max_ing = 2, 10
        ingredientes, bebidas, adicionales, pizzas_base = [], [], [], []
        masas_db, salsas_db = [], []

    def price_for(*tokens):
        for ing in ingredientes:
            nombre = (ing.nombre or '').lower()
            if any(token in nombre for token in tokens):
                return float(ing.precio_extra or 0)
        return 0.0

    visual_ingredients = [
        {'id': 'pepperoni', 'name': 'Pepperoni', 'file': 'pepperoni_piece.webp', 'size': 48, 'price': price_for('pepperoni')},
        {'id': 'chorizo', 'name': 'Chorizo', 'file': 'chorizo_piece.webp', 'size': 45, 'price': price_for('chorizo')},
        {'id': 'jamon', 'name': 'Jamon', 'file': 'jamon_piece.webp', 'size': 46, 'price': price_for('jam')},
        {'id': 'pollo', 'name': 'Pollo', 'file': 'pollo_piece.webp', 'size': 44, 'price': price_for('pollo')},
        {'id': 'champinon', 'name': 'Champinon', 'file': 'champinon_piece.webp', 'size': 45, 'price': price_for('champi')},
        {'id': 'cebolla', 'name': 'Cebolla', 'file': 'cebolla_piece.webp', 'size': 43, 'price': price_for('cebolla')},
        {'id': 'pina', 'name': 'Pina', 'file': 'pina_piece.webp', 'size': 44, 'price': price_for('pina', 'piña')},
        {'id': 'jalapeno', 'name': 'Jalapeno', 'file': 'jalapeno_piece.webp', 'size': 40, 'price': price_for('jalap')},
        {'id': 'aceituna', 'name': 'Aceituna', 'file': 'aceituna_piece.webp', 'size': 38, 'price': price_for('aceituna')},
        {'id': 'pimiento', 'name': 'Pimiento verde', 'file': 'pimiento_piece.webp', 'size': 42, 'price': price_for('pimiento')},
        {'id': 'tomate', 'name': 'Tomate', 'file': 'tomate_piece.webp', 'size': 44, 'price': price_for('tomate')},
        {'id': 'carne_molida', 'name': 'Carne molida', 'file': 'carne_molida_piece.webp', 'size': 42, 'price': price_for('carne')},
        {'id': 'tasajo', 'name': 'Tasajo', 'file': 'tasajo_piece.webp', 'size': 44, 'price': price_for('tasajo')},
    ]

    default_crusts = [
        {'id': 'delgada', 'name': 'Masa delgada', 'file': 'masa_delgada.webp'},
        {'id': 'tradicional', 'name': 'Masa tradicional', 'file': 'masa_tradicional.webp'},
        {'id': 'pan', 'name': 'Masa pan pizza', 'file': 'masa_pan.webp'},
    ]
    default_sauces = [
        {'id': 'tomate', 'name': 'Salsa de tomate', 'file': 'salsa_tomate.webp'},
        {'id': 'ranch', 'name': 'Salsa ranch', 'file': 'salsa_ranch.webp'},
        {'id': 'garlic', 'name': 'Salsa garlic', 'file': 'salsa_garlic.webp'},
    ]
    crusts = [
        {'id': m.codigo, 'name': m.nombre, 'file': m.imagen or default_crusts[0]['file'], 'price': float(m.precio_adicional or 0)}
        for m in masas_db
    ] or default_crusts
    sauces = [
        {'id': s.codigo, 'name': s.nombre, 'file': s.imagen or default_sauces[0]['file'], 'price': float(s.precio_adicional or 0)}
        for s in salsas_db
    ] or default_sauces
    return render_template(
        'cliente/pizza_builder.html',
        ingredientes=ingredientes, bebidas=bebidas, adicionales=adicionales,
        pizzas_base=pizzas_base, min_ing=min_ing, max_ing=max_ing,
        visual_ingredients=visual_ingredients, crusts=crusts, sauces=sauces
    )


def _int_config(key, default):
    try:
        return int(SystemConfig.get(key, default))
    except (TypeError, ValueError):
        return default


def _custom_ingredient_count(raw_text):
    if not raw_text:
        return None
    parts = [part.strip() for part in raw_text.split(';') if part.strip()]
    toppings = [
        part for part in parts
        if not part.lower().startswith(('masa:', 'salsa:'))
    ]
    return len(toppings)


def _normalize_name(value):
    normalized = unicodedata.normalize('NFKD', value or '')
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _extra_price_from_custom_text(raw_text):
    if not raw_text:
        return Decimal('0.00')
    total = Decimal('0.00')
    multipliers = {'poco': Decimal('1'), 'normal': Decimal('1'), 'extra': Decimal('1.5')}
    ingredientes = Ingredient.query.filter_by(estado='activo').all()
    masas = PizzaCrust.query.filter_by(estado='activa').all()
    salsas = PizzaSauce.query.filter_by(estado='activa').all()

    for part in [p.strip() for p in raw_text.split(';') if p.strip()]:
        lower = part.lower()
        if lower.startswith('masa:'):
            name = _normalize_name(part.split(':', 1)[1])
            match = next((m for m in masas if _normalize_name(m.nombre) == name), None)
            total += Decimal(str(match.precio_adicional or 0)) if match else Decimal('0.00')
            continue
        if lower.startswith('salsa:'):
            name = _normalize_name(part.split(':', 1)[1])
            match = next((s for s in salsas if _normalize_name(s.nombre) == name), None)
            total += Decimal(str(match.precio_adicional or 0)) if match else Decimal('0.00')
            continue

        ing_name = _normalize_name(part.split('(', 1)[0])
        amount = 'normal'
        if '(' in part and ')' in part:
            amount = part.split('(', 1)[1].split(',', 1)[0].strip().lower()
        match = next((ing for ing in ingredientes if _normalize_name(ing.nombre) == ing_name), None)
        if match:
            total += Decimal(str(match.precio_extra or 0)) * multipliers.get(amount, Decimal('1'))
    return total.quantize(Decimal('0.01'))


def _catalog_item_for_order(item):
    tipo = (item.get('tipo') or '').strip()
    try:
        item_id = int(item.get('id_item'))
        cantidad = int(item.get('cantidad', 1))
    except (TypeError, ValueError):
        raise ValueError('Producto invalido en el carrito.')
    if cantidad < 1:
        raise ValueError('La cantidad de cada producto debe ser mayor a cero.')

    model_map = {
        'pizza': (Pizza, 'precio_base', 'activa'),
        'combo': (Combo, 'precio', 'activo'),
        'refresco': (Drink, 'precio', 'activo'),
        'adicional': (Extra, 'precio', 'activo'),
    }
    if tipo not in model_map:
        raise ValueError(f'Tipo de producto no permitido: {tipo}.')

    model, price_field, active_state = model_map[tipo]
    db_item = model.query.get(item_id)
    if not db_item or getattr(db_item, 'estado', None) != active_state:
        raise ValueError('Uno de los productos del carrito ya no esta disponible.')

    ingredientes_extra = item.get('ingredientes_extra', '') or ''
    if tipo == 'pizza':
        min_ing = _int_config('min_ingredientes', 2)
        max_ing = _int_config('max_ingredientes', 10)
        custom_count = _custom_ingredient_count(ingredientes_extra)
        if custom_count is not None:
            if custom_count < min_ing:
                raise ValueError(f'La pizza personalizada debe tener al menos {min_ing} ingredientes.')
            if custom_count > max_ing:
                raise ValueError(f'La pizza personalizada no puede tener mas de {max_ing} ingredientes.')

    price = Decimal(str(getattr(db_item, price_field) or 0))
    if tipo == 'pizza' and ingredientes_extra:
        price += _extra_price_from_custom_text(ingredientes_extra)

    return {
        'tipo': tipo,
        'id_item': db_item.id,
        'nombre': item.get('nombre') or db_item.nombre,
        'cantidad': cantidad,
        'precio': price,
        'ingredientes_extra': ingredientes_extra,
    }


@cliente_bp.route('/nuevo-pedido', methods=['GET', 'POST'])
@login_required
@require_cliente
def nuevo_pedido():
    zonas = DeliveryZone.query.filter_by(estado='activa').all()
    bebidas = Drink.query.filter_by(estado='activo').all()
    adicionales = Extra.query.filter_by(estado='activo').all()
    pizzas = Pizza.query.filter_by(estado='activa').all()
    combos = Combo.query.filter_by(estado='activo').all()
    sucursal = Branch.query.filter_by(estado='activa').first()

    if request.method == 'POST':
        try:
            tipo_entrega = request.form.get('tipo_entrega')
            observaciones = request.form.get('observaciones', '')
            raw_items = json.loads(request.form.get('items_json', '[]'))
            items = [_catalog_item_for_order(item) for item in raw_items]
            id_zona = request.form.get('id_zona') or None
            direccion = request.form.get('direccion_entrega', '')
            if not items:
                flash('Debes agregar al menos un producto al pedido.', 'warning')
                return redirect(url_for('cliente.nuevo_pedido'))

            metodo = DeliveryMethod.query.filter_by(nombre=tipo_entrega).first()
            if not metodo:
                flash('Metodo de entrega invalido.', 'danger')
                return redirect(url_for('cliente.nuevo_pedido'))

            monto_delivery = Decimal('0.00')
            if tipo_entrega == 'delivery':
                if not id_zona or not direccion.strip():
                    flash('Selecciona zona y direccion para delivery.', 'warning')
                    return redirect(url_for('cliente.nuevo_pedido'))
                zona = DeliveryZone.query.get(int(id_zona))
                monto_delivery = Decimal(str(zona.costo_delivery if zona else 0))

            subtotal = sum(i['precio'] * i['cantidad'] for i in items)
            propina_max = min(subtotal * Decimal('0.30'), Decimal('20.00'))
            propina_custom = request.form.get('propina_custom', '').strip()
            if propina_custom:
                propina = Decimal(propina_custom)
            else:
                propina_pct = Decimal(request.form.get('propina_pct', '0') or '0')
                propina = (subtotal * propina_pct / Decimal('100')).quantize(Decimal('0.01'))
            if propina < 0:
                propina = Decimal('0.00')
            if propina > propina_max:
                propina = propina_max

            impuesto_pct = float(SystemConfig.get('impuesto', '7'))
            totales = calcular_total_pedido(float(subtotal), float(monto_delivery), impuesto_pct=impuesto_pct)
            total_final = Decimal(str(totales['total'])) + propina

            pedido = Order(
                id_cliente=current_user.id,
                id_metodo_entrega=metodo.id,
                id_sucursal=sucursal.id if sucursal else 1,
                id_zona=int(id_zona) if id_zona else None,
                subtotal=Decimal(str(totales['subtotal'])),
                monto_delivery=Decimal(str(totales['monto_delivery'])),
                impuesto=Decimal(str(totales['impuesto'])),
                propina=propina,
                total=total_final,
                estado_actual='recibido',
                direccion_entrega=direccion,
                observaciones=observaciones,
            )
            db.session.add(pedido)
            db.session.flush()

            for item in items:
                db.session.add(OrderDetail(
                    id_pedido=pedido.id,
                    tipo_item=item['tipo'],
                    id_item=item['id_item'],
                    nombre_item=item['nombre'],
                    cantidad=int(item['cantidad']),
                    precio_unitario=item['precio'],
                    subtotal=item['precio'] * item['cantidad'],
                    ingredientes_extra=item.get('ingredientes_extra', ''),
                ))

            db.session.add(OrderStatusHistory(
                id_pedido=pedido.id,
                estado='recibido',
                descripcion='Pedido recibido. Pendiente de pago o confirmacion.',
                actualizado_por=current_user.id,
            ))

            if tipo_entrega == 'retiro_local':
                db.session.add(LocalPickup(
                    id_pedido=pedido.id,
                    id_sucursal=sucursal.id if sucursal else 1,
                    codigo_retiro=f'PF-{pedido.id:05d}',
                    nombre_persona_retira=current_user.nombre,
                    estado='pendiente',
                ))

            db.session.commit()
            simular_correos_pedido(pedido, current_user.id)
            db.session.add(Notification(
                id_usuario=current_user.id,
                titulo='Pedido confirmado',
                mensaje=f'Tu pedido {pedido.numero} fue recibido.',
                tipo='pedido',
            ))
            db.session.commit()
            flash(f'Pedido {pedido.numero} creado exitosamente.', 'success')
            return redirect(url_for('cliente.ver_pedido', pedido_id=pedido.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear pedido: {e}', 'danger')

    return render_template(
        'cliente/nuevo_pedido.html',
        zonas=zonas, bebidas=bebidas, adicionales=adicionales, pizzas=pizzas, combos=combos
    )


@cliente_bp.route('/pedido/<int:pedido_id>')
@login_required
@require_cliente
def ver_pedido(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    if pedido.id_cliente != current_user.id and not current_user.is_admin():
        flash('No tienes permiso para ver este pedido.', 'danger')
        return redirect(url_for('cliente.dashboard'))
    historial = OrderStatusHistory.query.filter_by(id_pedido=pedido_id).order_by(OrderStatusHistory.fecha_estado).all()
    return render_template('cliente/ver_pedido.html', pedido=pedido, historial=historial)


@cliente_bp.route('/mis-pedidos')
@login_required
@require_cliente
def mis_pedidos():
    pedidos = Order.query.filter_by(id_cliente=current_user.id).order_by(Order.fecha_pedido.desc()).all()
    return render_template('cliente/mis_pedidos.html', pedidos=pedidos)


@cliente_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@require_cliente
def perfil():
    zonas = DeliveryZone.query.filter_by(estado='activa').order_by(DeliveryZone.nombre_zona).all()
    if request.method == 'POST':
        try:
            current_user.nombre = request.form.get('nombre', current_user.nombre).strip()
            current_user.telefono = request.form.get('telefono', '').strip()
            current_user.direccion = request.form.get('direccion', '').strip()
            zona_id = request.form.get('id_zona_preferida') or None
            current_user.id_zona_preferida = int(zona_id) if zona_id else None
            foto = save_image_upload(request.files.get('foto_perfil'), 'profiles', f'user_{current_user.id}')
            if foto:
                current_user.foto_perfil = foto
            new_password = request.form.get('new_password', '')
            if new_password:
                if len(new_password) < 6:
                    flash('La nueva contrasena debe tener al menos 6 caracteres.', 'warning')
                    return redirect(url_for('cliente.perfil'))
                current_user.set_password(new_password)
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('cliente.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando perfil: {e}', 'danger')
    pedidos = Order.query.filter_by(id_cliente=current_user.id).order_by(Order.fecha_pedido.desc()).limit(10).all()
    return render_template('cliente/perfil.html', zonas=zonas, pedidos=pedidos)


@cliente_bp.route('/pagar/<int:pedido_id>', methods=['GET', 'POST'])
@login_required
@require_cliente
def pagar(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    if pedido.id_cliente != current_user.id:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('cliente.dashboard'))

    pago_existente = Payment.query.filter_by(id_pedido=pedido_id, estado='pagado').first()
    config = {
        'nombre_empresa': SystemConfig.get('nombre_empresa', 'CHINOS CAFE S.A.'),
        'yappy_numero': SystemConfig.get('yappy_numero', '6000-0000'),
    }

    if request.method == 'POST':
        metodo = request.form.get('metodo_pago')
        referencia = request.form.get('referencia', '')
        try:
            comprobante_path = None
            if metodo == 'yappy':
                comprobante_path = save_payment_receipt(request.files.get('comprobante'), pedido.id)
                if not comprobante_path:
                    flash('Sube el comprobante Yappy en PNG, JPG, JPEG o PDF.', 'warning')
                    return redirect(url_for('cliente.pagar', pedido_id=pedido.id))

            pago = Payment(
                id_pedido=pedido.id,
                metodo=metodo,
                referencia=referencia,
                monto=pedido.total,
                estado='pendiente' if metodo == 'efectivo' else 'pagado',
                comprobante=comprobante_path,
            )
            db.session.add(pago)
            db.session.add(OrderStatusHistory(
                id_pedido=pedido.id,
                estado='pago_pendiente_efectivo' if metodo == 'efectivo' else 'pago_confirmado',
                descripcion=f'Pago registrado con metodo {metodo}.',
                actualizado_por=current_user.id,
            ))
            db.session.commit()
            simular_correo_pago(pago)
            flash('Pago registrado. Cocina vera el pedido sin saltarse el flujo.', 'success')
            return redirect(url_for('cliente.ver_pedido', pedido_id=pedido.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar pago: {e}', 'danger')

    return render_template('cliente/pagar.html', pedido=pedido, pago_existente=pago_existente, config=config)


@cliente_bp.route('/cancelar/<int:pedido_id>', methods=['POST'])
@login_required
@require_cliente
def cancelar_pedido(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    if pedido.id_cliente != current_user.id:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('cliente.dashboard'))
    if pedido.estado_actual != 'recibido':
        flash('Solo puedes cancelar antes de que cocina inicie la preparacion.', 'warning')
        return redirect(url_for('cliente.ver_pedido', pedido_id=pedido.id))
    motivo = request.form.get('motivo', 'Cancelado por el cliente')
    try:
        pagado = pedido.pagos.filter_by(estado='pagado').first() is not None
        pedido.estado_actual = 'cancelado'
        pedido.motivo_cancelacion = motivo
        pedido.cancelado_por = current_user.id
        pedido.fecha_cancelacion = datetime.utcnow()
        db.session.add(OrderStatusHistory(
            id_pedido=pedido.id,
            estado='cancelado',
            descripcion=motivo,
            actualizado_por=current_user.id,
        ))
        if pagado:
            db.session.add(OrderStatusHistory(
                id_pedido=pedido.id,
                estado='reembolso_simulado',
                descripcion='Reembolso registrado en modo simulado para pago confirmado.',
                actualizado_por=current_user.id,
            ))
        db.session.add(Notification(
            id_usuario=current_user.id,
            titulo='Pedido cancelado',
            mensaje=f'Tu pedido {pedido.numero} fue cancelado. Motivo: {motivo}',
            tipo='pedido',
        ))
        db.session.commit()
        simular_correo_cancelacion(pedido, motivo, reembolso=pagado)
        flash('Pedido cancelado correctamente.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cancelar: {e}', 'danger')
    return redirect(url_for('cliente.ver_pedido', pedido_id=pedido.id))


@cliente_bp.route('/api/zona/<int:zona_id>')
@login_required
def api_zona(zona_id):
    zona = DeliveryZone.query.get_or_404(zona_id)
    return jsonify({'costo': float(zona.costo_delivery), 'tiempo': zona.tiempo_estimado_min, 'nombre': zona.nombre_zona})
