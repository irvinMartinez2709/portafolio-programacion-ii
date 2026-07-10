from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (Employee, Driver, DeliveryAssignment, DeliveryReport,
                        OrderStatusHistory, Notification, DeliveryZone,
                        ZoneChangeRequest, Order)
from app.utils.calculations import calcular_delivery
from app.utils.email_simulator import simular_correo_entrega
from app.utils.email_simulator import simular_correo_entrega, simular_correo_estado_pedido

repartidor_bp = Blueprint('repartidor', __name__, url_prefix='/repartidor')

# ── Ganancia base por entrega (si no hay comision calculada) ──────────────
GANANCIA_BASE_POR_ENTREGA = 2.00  # $2.00 base si monto_flete es 0


def require_repartidor(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.rol_nombre not in ('Repartidor', 'Administrador'):
            flash('Acceso no autorizado.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated


def _get_driver():
    if current_user.is_admin():
        return Driver.query.first()
    emp = Employee.query.filter_by(id_usuario=current_user.id).first()
    return Driver.query.filter_by(id_empleado=emp.id).first() if emp else None


def _calcular_ganancias(driver):
    """Calcula ganancias del día, totales y conteo de entregas."""
    hoy = date.today()
    ganancias_hoy = 0.0
    ganancias_total = 0.0
    entregas_hoy = 0
    entregas_total = 0

    asignaciones_entregadas = (DeliveryAssignment.query
                               .filter_by(id_repartidor=driver.id, estado='entregado')
                               .all())
    for asig in asignaciones_entregadas:
        ganancia = float(asig.comision_repartidor or 0) + float(asig.propina or 0)
        # Si la comision es 0 (asignacion sin calculo), usar base
        if ganancia == 0:
            ganancia = GANANCIA_BASE_POR_ENTREGA
        ganancias_total += ganancia
        entregas_total += 1
        if asig.fecha_entrega and asig.fecha_entrega.date() == hoy:
            ganancias_hoy += ganancia
            entregas_hoy += 1

    return {
        'ganancias_hoy': round(ganancias_hoy, 2),
        'ganancias_total': round(ganancias_total, 2),
        'entregas_hoy': entregas_hoy,
        'entregas_total': entregas_total,
    }


@repartidor_bp.route('/dashboard')
@login_required
@require_repartidor
def dashboard():
    driver = _get_driver()
    asignaciones = []
    pedidos_disponibles = []
    stats = {'ganancias_hoy': 0.0, 'ganancias_total': 0.0,
             'entregas_hoy': 0, 'entregas_total': 0}

    if driver:
        # Asignaciones propias (activas + historial reciente)
        asignaciones = (DeliveryAssignment.query
                        .filter_by(id_repartidor=driver.id)
                        .order_by(DeliveryAssignment.fecha_asignacion.desc())
                        .all())

        # ── CORRECCIÓN: Pedidos disponibles de la zona del repartidor ────────
        # El admin asigna al repartidor via /pedidos/<pid>/asignar-repartidor
        # Esta sección muestra pedidos "listo" o "asignado_repartidor" de su zona
        # para referencia, pero también pedidos ya asignados a él
        if driver.id_zona_actual:
            pedidos_disponibles = (Order.query
                .filter(
                    Order.id_zona == driver.id_zona_actual,
                    Order.estado_actual == 'listo',
                    ~Order.id.in_(db.session.query(DeliveryAssignment.id_pedido)),
                )
                .order_by(Order.fecha_pedido.desc())
                .limit(20)
                .all())

        stats = _calcular_ganancias(driver)

    return render_template(
        'repartidor/dashboard.html',
        driver=driver,
        asignaciones=asignaciones,
        pedidos_disponibles=pedidos_disponibles,
        ganancias_hoy=stats['ganancias_hoy'],
        ganancias_total=stats['ganancias_total'],
        entregas_hoy=stats['entregas_hoy'],
        entregas_total=stats['entregas_total'],
    )


@repartidor_bp.route('/aceptar/<int:pedido_id>', methods=['POST'])
@login_required
@require_repartidor
def aceptar_pedido(pedido_id):
    driver = _get_driver()
    if not driver:
        flash('Perfil de repartidor no encontrado.', 'warning')
        return redirect(url_for('repartidor.dashboard'))
    if not driver.disponible:
        flash('Debes estar disponible para aceptar pedidos.', 'warning')
        return redirect(url_for('repartidor.dashboard'))

    pedido = Order.query.get_or_404(pedido_id)
    try:
        if not pedido.metodo_entrega or pedido.metodo_entrega.nombre != 'delivery':
            flash('Solo puedes aceptar pedidos de delivery.', 'warning')
            return redirect(url_for('repartidor.dashboard'))
        if pedido.estado_actual != 'listo':
            flash('Solo puedes aceptar pedidos marcados como listos por cocina.', 'warning')
            return redirect(url_for('repartidor.dashboard'))
        if pedido.asignacion:
            flash('Este pedido ya fue asignado a un repartidor.', 'info')
            return redirect(url_for('repartidor.dashboard'))
        if driver.id_zona_actual and pedido.id_zona != driver.id_zona_actual:
            flash('Este pedido no pertenece a tu zona actual.', 'warning')
            return redirect(url_for('repartidor.dashboard'))

        pago_pagado = pedido.pagos.filter_by(estado='pagado').first()
        pago_efectivo = pedido.pagos.filter_by(metodo='efectivo').first()
        if not pago_pagado and not pago_efectivo:
            flash('No puedes aceptar un pedido sin pago confirmado, salvo efectivo.', 'warning')
            return redirect(url_for('repartidor.dashboard'))

        pct = float(driver.porcentaje_comision or 60)
        calc = calcular_delivery(float(pedido.monto_delivery or 0), pct)
        asig = DeliveryAssignment(
            id_pedido=pedido.id,
            id_repartidor=driver.id,
            monto_flete=pedido.monto_delivery or 0,
            porcentaje_comision=pct,
            comision_repartidor=calc['comision_repartidor'],
            ganancia_empresa_delivery=calc['ganancia_empresa_delivery'],
            propina=pedido.propina or 0,
        )
        pedido.estado_actual = 'asignado_repartidor'
        db.session.add(asig)
        db.session.add(OrderStatusHistory(
            id_pedido=pedido.id,
            estado='asignado_repartidor',
            descripcion=f'Pedido aceptado por repartidor: {driver.empleado.usuario.nombre}',
            actualizado_por=current_user.id,
        ))
        db.session.add(Notification(
            id_usuario=pedido.id_cliente,
            titulo='Repartidor asignado',
            mensaje=f'Tu pedido {pedido.numero} fue aceptado por un repartidor.',
            tipo='delivery',
        ))
        db.session.commit()
        simular_correo_estado_pedido(
            pedido,
            'asignado_repartidor',
            f'Tu pedido fue aceptado por {driver.empleado.usuario.nombre}.'
        )
        flash(f'Pedido {pedido.numero} aceptado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error aceptando pedido: {e}', 'danger')
    return redirect(url_for('repartidor.dashboard'))


@repartidor_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@require_repartidor
def perfil():
    driver = _get_driver()
    zonas = DeliveryZone.query.filter_by(estado='activa').order_by(DeliveryZone.nombre_zona).all()
    if not driver:
        flash('Perfil de repartidor no encontrado.', 'warning')
        return redirect(url_for('repartidor.dashboard'))
    if request.method == 'POST':
        try:
            current_user.telefono = request.form.get('telefono', '').strip()
            zona_nueva = request.form.get('id_zona_nueva')
            motivo = request.form.get('motivo', '').strip()
            if zona_nueva:
                req = ZoneChangeRequest(
                    id_repartidor=driver.id,
                    id_zona_anterior=driver.id_zona_actual,
                    id_zona_nueva=int(zona_nueva),
                    motivo=motivo,
                )
                db.session.add(req)
            db.session.commit()
            flash('Perfil actualizado. Solicitud enviada si elegiste nueva zona.', 'success')
            return redirect(url_for('repartidor.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando perfil: {e}', 'danger')
    solicitudes = (ZoneChangeRequest.query
                   .filter_by(id_repartidor=driver.id)
                   .order_by(ZoneChangeRequest.fecha_solicitud.desc())
                   .limit(10).all())
    asignaciones = (DeliveryAssignment.query
                    .filter_by(id_repartidor=driver.id)
                    .order_by(DeliveryAssignment.fecha_asignacion.desc())
                    .limit(20).all())
    stats = _calcular_ganancias(driver)
    return render_template(
        'repartidor/perfil.html',
        driver=driver, zonas=zonas,
        solicitudes=solicitudes, asignaciones=asignaciones,
        **stats,
    )


@repartidor_bp.route('/en-camino/<int:asig_id>', methods=['POST'])
@login_required
@require_repartidor
def en_camino(asig_id):
    asig = DeliveryAssignment.query.get_or_404(asig_id)
    try:
        driver = _get_driver()
        if not current_user.is_admin() and (not driver or asig.id_repartidor != driver.id):
            flash('No tienes permiso sobre esta asignacion.', 'danger')
            return redirect(url_for('repartidor.dashboard'))
        if asig.pedido.estado_actual != 'asignado_repartidor' or asig.estado != 'asignado':
            flash('Solo puedes salir cuando cocina ya marco listo y admin asigno el pedido.', 'warning')
            return redirect(url_for('repartidor.dashboard'))
        asig.estado = 'en_camino'
        asig.pedido.estado_actual = 'en_camino'
        db.session.add(OrderStatusHistory(
            id_pedido=asig.id_pedido,
            estado='en_camino',
            descripcion='Repartidor en camino.',
            actualizado_por=current_user.id,
        ))
        db.session.add(Notification(
            id_usuario=asig.pedido.id_cliente,
            titulo='Tu pedido va en camino',
            mensaje=f'Tu pedido #{asig.pedido.numero} esta en camino.',
            tipo='delivery',
        ))
        db.session.commit()
        simular_correo_estado_pedido(
            asig.pedido,
            'en_camino',
            'El repartidor ya va en camino con tu pedido.'
        )
        flash('Estado actualizado a En camino.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('repartidor.dashboard'))


@repartidor_bp.route('/entregado/<int:asig_id>', methods=['POST'])
@login_required
@require_repartidor
def entregado(asig_id):
    asig = DeliveryAssignment.query.get_or_404(asig_id)
    resultado = request.form.get('resultado', 'entregado_exitosamente')
    observacion = request.form.get('observacion_final', '')
    try:
        driver = _get_driver()
        if not current_user.is_admin() and (not driver or asig.id_repartidor != driver.id):
            flash('No tienes permiso sobre esta asignacion.', 'danger')
            return redirect(url_for('repartidor.dashboard'))
        if asig.estado != 'en_camino' or asig.pedido.estado_actual != 'en_camino':
            flash('No puedes entregar un pedido que no esta en camino.', 'warning')
            return redirect(url_for('repartidor.dashboard'))

        ahora = datetime.utcnow()
        asig.estado = 'entregado'
        asig.fecha_entrega = ahora
        asig.pedido.estado_actual = 'entregado'

        # ── CORRECCIÓN GANANCIAS: asegurar que comision_repartidor esté seteada ──
        if not asig.comision_repartidor or float(asig.comision_repartidor) == 0:
            pct = float(asig.porcentaje_comision or 60)
            flete = float(asig.monto_flete or 0)
            if flete > 0:
                asig.comision_repartidor = round(flete * pct / 100, 2)
            else:
                asig.comision_repartidor = GANANCIA_BASE_POR_ENTREGA
        asig.propina = asig.pedido.propina or asig.propina or 0

        reporte = DeliveryReport(
            id_pedido=asig.id_pedido,
            id_repartidor=asig.id_repartidor,
            resultado=resultado,
            observacion_final=observacion,
            hora_entrega=ahora,
        )
        db.session.add(reporte)
        db.session.add(OrderStatusHistory(
            id_pedido=asig.id_pedido,
            estado='entregado',
            descripcion=f'Reporte entrega: {resultado}. {observacion}',
            actualizado_por=current_user.id,
        ))
        db.session.add(Notification(
            id_usuario=asig.pedido.id_cliente,
            titulo='Pedido entregado',
            mensaje=f'Tu pedido #{asig.pedido.numero} fue entregado.',
            tipo='delivery',
        ))
        db.session.commit()
        simular_correo_entrega(reporte)
        flash('Pedido marcado como entregado. ¡Ganancia registrada!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('repartidor.dashboard'))
