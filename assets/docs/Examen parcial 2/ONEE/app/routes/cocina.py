from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime
from app.models import (
    Order, OrderStatusHistory, Notification, Ingredient, PizzaCrust,
    PizzaSauce, Drink, Extra
)
from app.utils.email_simulator import (
    simular_correo_cancelacion, simular_correo_estado_pedido, simular_correo_retiro
)

cocina_bp = Blueprint('cocina', __name__, url_prefix='/cocina')

ESTADOS_COCINA = ['recibido', 'en_preparacion', 'en_horno', 'listo']
ESTADOS_LABELS = {
    'recibido': 'Nuevos',
    'en_preparacion': 'En Preparacion',
    'en_horno': 'En Horno',
    'listo': 'Listos',
}


def require_cocina(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.rol_nombre not in ('Operario/Cocina', 'Administrador'):
            flash('Acceso no autorizado.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated


def _pedido_autorizado_para_cocina(pedido):
    if pedido.metodo_entrega and pedido.metodo_entrega.nombre == 'retiro_local':
        return pedido.pagos.filter_by(estado='pagado').first() is not None or pedido.pagos.filter_by(metodo='efectivo').first() is not None
    return pedido.pagos.filter_by(estado='pagado').first() is not None or pedido.pagos.filter_by(metodo='efectivo').first() is not None


@cocina_bp.route('/dashboard')
@login_required
@require_cocina
def dashboard():
    pedidos_activos = Order.query.filter(Order.estado_actual.in_(ESTADOS_COCINA)).order_by(Order.fecha_pedido.asc()).all()
    columnas = {estado: [] for estado in ESTADOS_COCINA}
    for pedido in pedidos_activos:
        columnas[pedido.estado_actual].append(pedido)
    stats = {estado: len(items) for estado, items in columnas.items()}
    stock = {
        'Ingredientes': Ingredient.query.order_by(Ingredient.categoria, Ingredient.nombre).all(),
        'Masas': PizzaCrust.query.order_by(PizzaCrust.nombre).all(),
        'Salsas': PizzaSauce.query.order_by(PizzaSauce.nombre).all(),
        'Refrescos': Drink.query.order_by(Drink.nombre).all(),
        'Adicionales': Extra.query.order_by(Extra.nombre).all(),
    }
    return render_template(
        'cocina/dashboard.html',
        columnas=columnas,
        stats=stats,
        estados_labels=ESTADOS_LABELS,
        stock=stock,
    )


@cocina_bp.route('/avanzar/<int:pedido_id>', methods=['POST'])
@login_required
@require_cocina
def avanzar_estado(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    try:
        if pedido.estado_actual not in ESTADOS_COCINA:
            flash('Este pedido no esta en flujo de cocina.', 'warning')
            return redirect(url_for('cocina.dashboard'))
        if pedido.estado_actual == 'recibido' and not _pedido_autorizado_para_cocina(pedido):
            flash('Cocina no puede iniciar sin pago confirmado, salvo efectivo.', 'warning')
            return redirect(url_for('cocina.dashboard'))
        idx = ESTADOS_COCINA.index(pedido.estado_actual)
        if idx >= len(ESTADOS_COCINA) - 1:
            flash('El pedido ya esta listo.', 'info')
            return redirect(url_for('cocina.dashboard'))

        nuevo_estado = ESTADOS_COCINA[idx + 1]
        pedido.estado_actual = nuevo_estado
        db.session.add(OrderStatusHistory(
            id_pedido=pedido.id,
            estado=nuevo_estado,
            descripcion=f'Cocina actualizo a {ESTADOS_LABELS[nuevo_estado]}.',
            actualizado_por=current_user.id,
        ))
        if nuevo_estado == 'listo':
            db.session.add(Notification(
                id_usuario=pedido.id_cliente,
                titulo='Tu pedido esta listo',
                mensaje=f'Tu pedido {pedido.numero} esta listo.',
                tipo='pedido',
            ))
        db.session.commit()
        simular_correo_estado_pedido(
            pedido,
            nuevo_estado,
            f'Cocina actualizo tu pedido a {ESTADOS_LABELS[nuevo_estado]}.'
        )

        flash(f'Pedido {pedido.numero} actualizado a {ESTADOS_LABELS[nuevo_estado]}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('cocina.dashboard'))


@cocina_bp.route('/confirmar-retiro/<int:pedido_id>', methods=['POST'])
@login_required
@require_cocina
def confirmar_retiro(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    try:
        if not pedido.metodo_entrega or pedido.metodo_entrega.nombre != 'retiro_local':
            flash('Este pedido no es de retiro en local.', 'warning')
            return redirect(url_for('cocina.dashboard'))
        if pedido.estado_actual != 'listo':
            flash('Solo puedes confirmar retiro cuando el pedido esta listo.', 'warning')
            return redirect(url_for('cocina.dashboard'))

        ahora = datetime.utcnow()
        pedido.estado_actual = 'retirado'
        if pedido.retiro:
            pedido.retiro.estado = 'retirado'
            pedido.retiro.fecha_retiro = ahora
        db.session.add(OrderStatusHistory(
            id_pedido=pedido.id,
            estado='retirado',
            descripcion='Pedido retirado en local confirmado por cocina.',
            actualizado_por=current_user.id,
        ))
        db.session.add(Notification(
            id_usuario=pedido.id_cliente,
            titulo='Pedido retirado',
            mensaje=f'Tu pedido {pedido.numero} fue retirado en local.',
            tipo='pedido',
        ))
        db.session.commit()
        simular_correo_retiro(pedido)
        flash(f'Retiro local confirmado para {pedido.numero}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error confirmando retiro: {e}', 'danger')
    return redirect(url_for('cocina.dashboard'))


@cocina_bp.route('/stock/actualizar', methods=['POST'])
@login_required
@require_cocina
def actualizar_stock():
    model_map = {
        'ingrediente': Ingredient,
        'masa': PizzaCrust,
        'salsa': PizzaSauce,
        'refresco': Drink,
        'adicional': Extra,
    }
    tipo = request.form.get('tipo')
    model = model_map.get(tipo)
    if not model:
        flash('Tipo de producto invalido.', 'danger')
        return redirect(url_for('cocina.dashboard'))

    try:
        item = model.query.get_or_404(int(request.form.get('item_id')))
        if hasattr(item, 'stock'):
            stock = int(request.form.get('stock', item.stock or 0))
            if stock < 0:
                raise ValueError('El stock no puede ser negativo.')
            item.stock = stock
        estado = request.form.get('estado')
        if estado:
            item.estado = estado
        db.session.commit()
        flash('Stock/disponibilidad actualizados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error actualizando stock: {e}', 'danger')
    return redirect(url_for('cocina.dashboard'))


@cocina_bp.route('/cancelar/<int:pedido_id>', methods=['POST'])
@login_required
@require_cocina
def cancelar_pedido(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    motivo = request.form.get('motivo', '').strip()
    if not motivo:
        flash('Debes indicar motivo de cancelacion.', 'warning')
        return redirect(url_for('cocina.dashboard'))
    if pedido.estado_actual in ('entregado', 'cancelado'):
        flash('No se puede cancelar un pedido entregado o ya cancelado.', 'warning')
        return redirect(url_for('cocina.dashboard'))
    try:
        pedido.estado_actual = 'cancelado'
        pedido.motivo_cancelacion = motivo
        pedido.cancelado_por = current_user.id
        pedido.fecha_cancelacion = datetime.utcnow()
        db.session.add(OrderStatusHistory(
            id_pedido=pedido.id,
            estado='cancelado',
            descripcion=f'Cancelado por cocina: {motivo}',
            actualizado_por=current_user.id,
        ))
        pagado = pedido.pagos.filter_by(estado='pagado').first() is not None
        if pagado:
            db.session.add(OrderStatusHistory(
                id_pedido=pedido.id,
                estado='reembolso_simulado',
                descripcion='Reembolso registrado en modo simulado para pago confirmado.',
                actualizado_por=current_user.id,
            ))
        db.session.add(Notification(
            id_usuario=pedido.id_cliente,
            titulo='Pedido cancelado por cocina',
            mensaje=f'Tu pedido {pedido.numero} fue cancelado. Motivo: {motivo}',
            tipo='pedido',
        ))
        db.session.commit()
        simular_correo_cancelacion(pedido, motivo, reembolso=pagado)
        flash('Pedido cancelado y cliente notificado en outbox.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelando pedido: {e}', 'danger')
    return redirect(url_for('cocina.dashboard'))
