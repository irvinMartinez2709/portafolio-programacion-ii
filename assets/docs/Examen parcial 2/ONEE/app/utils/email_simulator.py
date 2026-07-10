import os
from datetime import datetime
from flask import current_app

from app.extensions import db
from app.models import OutboxEmail, SystemConfig, Pizza, Combo, Payment
from app.utils.file_uploads import static_image_url
from app.utils.json_generator import (
    generar_json_pedido_cliente,
    generar_json_pedido_empresa,
    generar_json_pedido_operario,
    generar_json_pago,
    generar_json_cancelacion,
    generar_json_reembolso,
    generar_json_entrega,
    generar_json_retiro,
)
from app.utils.mail_service import send_email


def simular_correos_pedido(pedido, user_id=None):
    resultados = []

    correo_empresa = SystemConfig.get('correo_empresa', 'pedidos@chinoscafe.pa')
    correo_operario = SystemConfig.get('correo_operario', 'cocina@chinoscafe.pa')
    correo_cliente = pedido.cliente.correo or 'cliente@ejemplo.pa'

    try:
        _, json_cliente = generar_json_pedido_cliente(pedido)
        _, json_empresa = generar_json_pedido_empresa(pedido)
        _, json_operario = generar_json_pedido_operario(pedido)

        _registrar_outbox(pedido.id, correo_cliente, f'Tu pedido {pedido.numero} fue confirmado', json_cliente)
        _registrar_outbox(pedido.id, correo_empresa, f'Nuevo pedido {pedido.numero}', json_empresa)
        _registrar_outbox(pedido.id, correo_operario, f'Orden cocina {pedido.numero}', json_operario)
        db.session.commit()

        _try_real_email(
            correo_cliente,
            f'Tu pedido {pedido.numero} fue recibido',
            _pedido_texto(pedido, 'recibido'),
            pedido.id,
            html=_pedido_html(
                pedido,
                'Pedido recibido',
                'Ya tenemos tu orden. Te avisaremos por correo cada avance del proceso.',
                estado_visual='recibido',
            ),
            attachments=_pedido_attachments(pedido, json_cliente, incluir_comprobante=True),
        )

        _try_real_email(
            correo_empresa,
            f'Nuevo pedido {pedido.numero}',
            _pedido_texto(pedido, 'nuevo pedido'),
            pedido.id,
            html=_pedido_html(
                pedido,
                'Nuevo pedido recibido',
                'Revisar productos, pago, cliente y datos de entrega.',
                estado_visual='recibido',
            ),
            attachments=_pedido_attachments(pedido, json_empresa, incluir_comprobante=True),
        )

        _try_real_email(
            correo_operario,
            f'Cocina: preparar {pedido.numero}',
            _pedido_texto(pedido, 'orden de cocina'),
            pedido.id,
            html=_pedido_html(
                pedido,
                'Orden enviada a cocina',
                'Preparar segun el detalle del pedido.',
                estado_visual='en_preparacion',
            ),
            attachments=_pedido_attachments(pedido, json_operario, incluir_comprobante=False),
        )

        resultados.append({'ok': True})

    except Exception as exc:
        db.session.rollback()
        resultados.append({'error': str(exc)})

    return resultados


def simular_correo_pago(pago):
    correo_empresa = SystemConfig.get('correo_empresa', 'pagos@chinoscafe.pa')

    try:
        _, filename = generar_json_pago(pago)

        _registrar_outbox(
            pago.id_pedido,
            correo_empresa,
            f'Pago confirmado pedido {pago.pedido.numero}',
            filename,
        )
        db.session.commit()

        attachments = _pedido_attachments(
            pago.pedido,
            filename,
            incluir_comprobante=True,
            pago_actual=pago,
        )

        _try_real_email(
            correo_empresa,
            f'Pago recibido {pago.pedido.numero}',
            f'Pago registrado para el pedido {pago.pedido.numero}. Monto: ${float(pago.monto):.2f}.',
            pago.id_pedido,
            html=_pedido_html(
                pago.pedido,
                'Pago recibido',
                f'Metodo: {pago.metodo}. Referencia: {pago.referencia or "N/A"}. Se adjunta comprobante si fue subido.',
                estado_visual='pago',
                pago=pago,
            ),
            attachments=attachments,
        )

        if pago.pedido.cliente.correo:
            _try_real_email(
                pago.pedido.cliente.correo,
                f'Recibimos tu pago {pago.pedido.numero}',
                f'Tu pago del pedido {pago.pedido.numero} fue registrado.',
                pago.id_pedido,
                html=_pedido_html(
                    pago.pedido,
                    'Pago confirmado',
                    'Gracias. Ya registramos tu pago y el pedido seguira el flujo de cocina.',
                    estado_visual='pago',
                    pago=pago,
                ),
                attachments=attachments,
            )

        return {'destinatario': correo_empresa, 'archivo': filename}

    except Exception as exc:
        db.session.rollback()
        return {'error': str(exc)}


def simular_correo_estado_pedido(pedido, estado, descripcion=''):
    if not pedido.cliente.correo:
        return {'ok': False, 'error': 'Cliente sin correo.'}

    textos = {
        'en_preparacion': ('Tu pedido se esta preparando', 'Nuestro equipo ya empezo a preparar tu pedido.'),
        'en_horno': ('Tu pedido esta en el horno', 'Ya casi. Tu pizza esta horneandose.'),
        'listo': ('Tu pedido esta listo', 'Tu pedido ya salio de cocina.'),
        'asignado_repartidor': ('Repartidor asignado', 'Tu pedido ya tiene repartidor asignado.'),
        'en_camino': ('Tu pedido va en camino', 'El repartidor ya salio hacia tu ubicacion.'),
        'entregado': ('Pedido entregado', 'Gracias por pedir con CHINOS CAFE PIZZAFLOW.'),
    }

    titulo, detalle = textos.get(estado, (f'Actualizacion {pedido.numero}', descripcion or estado))

    return _try_real_email(
        pedido.cliente.correo,
        f'{titulo} - {pedido.numero}',
        _pedido_texto(pedido, estado),
        pedido.id,
        html=_pedido_html(
            pedido,
            titulo,
            descripcion or detalle,
            estado_visual=estado,
        ),
        attachments=_pedido_attachments(pedido, None, incluir_comprobante=False),
    )


def simular_correo_cancelacion(pedido, motivo, reembolso=False):
    try:
        _, filename = generar_json_cancelacion(pedido, motivo, reembolso)

        _registrar_outbox(
            pedido.id,
            pedido.cliente.correo or 'cliente@ejemplo.pa',
            f'Pedido {pedido.numero} cancelado',
            filename,
        )

        attachments = [_outbox_path(filename)]

        if reembolso:
            _, refund_file = generar_json_reembolso(pedido, pedido.total, motivo)
            _registrar_outbox(
                pedido.id,
                SystemConfig.get('correo_empresa', 'pagos@chinoscafe.pa'),
                f'Reembolso simulado {pedido.numero}',
                refund_file,
            )
            attachments.append(_outbox_path(refund_file))

        db.session.commit()

        _try_real_email(
            pedido.cliente.correo or 'cliente@ejemplo.pa',
            f'Pedido {pedido.numero} cancelado',
            f'Tu pedido {pedido.numero} fue cancelado. Motivo: {motivo}.',
            pedido.id,
            html=_pedido_html(
                pedido,
                'Pedido cancelado',
                f'Motivo: {motivo}. {"Se registro reembolso simulado." if reembolso else ""}',
                alerta=True,
                estado_visual='cancelado',
            ),
            attachments=attachments,
        )

        return {'archivo': filename}

    except Exception as exc:
        db.session.rollback()
        return {'error': str(exc)}


def simular_correo_entrega(reporte):
    try:
        _, filename = generar_json_entrega(reporte)

        _registrar_outbox(
            reporte.id_pedido,
            reporte.pedido.cliente.correo or 'cliente@ejemplo.pa',
            f'Entrega {reporte.pedido.numero}',
            filename,
        )
        db.session.commit()

        _try_real_email(
            reporte.pedido.cliente.correo or 'cliente@ejemplo.pa',
            f'Tu pedido {reporte.pedido.numero} fue entregado',
            f'Tu pedido {reporte.pedido.numero} fue marcado como entregado.',
            reporte.id_pedido,
            html=_pedido_html(
                reporte.pedido,
                'Pedido entregado',
                f'Resultado: {reporte.resultado}. {reporte.observacion_final or ""}',
                estado_visual='entregado',
            ),
            attachments=[_outbox_path(filename)],
        )

        return {'archivo': filename}

    except Exception as exc:
        db.session.rollback()
        return {'error': str(exc)}


def simular_correo_retiro(pedido):
    try:
        _, filename = generar_json_retiro(pedido)
        correo_empresa = SystemConfig.get('correo_empresa', 'pedidos@chinoscafe.pa')

        _registrar_outbox(
            pedido.id,
            pedido.cliente.correo or 'cliente@ejemplo.pa',
            f'Retiro local {pedido.numero}',
            filename,
        )
        _registrar_outbox(
            pedido.id,
            correo_empresa,
            f'Retiro local confirmado {pedido.numero}',
            filename,
        )
        db.session.commit()

        attachments = [_outbox_path(filename)]
        _try_real_email(
            pedido.cliente.correo or 'cliente@ejemplo.pa',
            f'Tu pedido {pedido.numero} fue retirado',
            f'Tu pedido {pedido.numero} fue confirmado como retirado en local.',
            pedido.id,
            html=_pedido_html(
                pedido,
                'Pedido retirado en local',
                'Confirmamos el retiro de tu pedido en sucursal. Gracias por elegir CHINOS CAFE PIZZAFLOW.',
                estado_visual='entregado',
            ),
            attachments=attachments,
        )
        _try_real_email(
            correo_empresa,
            f'Retiro local confirmado {pedido.numero}',
            f'El pedido {pedido.numero} fue retirado en local.',
            pedido.id,
            html=_pedido_html(
                pedido,
                'Retiro local confirmado',
                'El pedido fue retirado por el cliente en sucursal.',
                estado_visual='entregado',
            ),
            attachments=attachments,
        )
        return {'archivo': filename}

    except Exception as exc:
        db.session.rollback()
        return {'error': str(exc)}


def _pedido_html(pedido, titulo, mensaje, alerta=False, estado_visual=None, pago=None):
    color = '#d93b2f' if not alerta else '#8b1e16'
    verde = '#256f4a'
    fondo = '#f7f2ea'
    estado_visual = estado_visual or pedido.estado_actual

    items_html = ''
    for detalle in pedido.detalles:
        items_html += f"""
        <tr>
          <td style="padding:14px 10px;border-bottom:1px solid #eee">
            <strong>{detalle.nombre_item}</strong>
            <div style="font-size:12px;color:#777">{detalle.tipo_item}</div>
          </td>
          <td style="padding:14px 10px;border-bottom:1px solid #eee;text-align:center">{detalle.cantidad}</td>
          <td style="padding:14px 10px;border-bottom:1px solid #eee;text-align:right;font-weight:700">${float(detalle.subtotal):.2f}</td>
        </tr>
        """

    pago_html = ''
    if pago:
        comprobante = 'Si, adjunto' if pago.comprobante else 'No subido'
        pago_html = f"""
        <div style="background:#eef9f2;border:1px solid #cdebd8;border-radius:14px;padding:16px;margin:18px 0">
          <div style="font-size:13px;color:#256f4a;text-transform:uppercase;font-weight:700">Pago</div>
          <div><strong>Metodo:</strong> {pago.metodo}</div>
          <div><strong>Referencia:</strong> {pago.referencia or "N/A"}</div>
          <div><strong>Monto:</strong> ${float(pago.monto):.2f}</div>
          <div><strong>Comprobante:</strong> {comprobante}</div>
        </div>
        """

    pasos = [
        ('recibido', 'Recibido'),
        ('pago', 'Pago'),
        ('en_preparacion', 'Preparando'),
        ('en_horno', 'Horno'),
        ('listo', 'Listo'),
        ('en_camino', 'En camino'),
        ('entregado', 'Entregado'),
    ]
    activos = {estado_visual}
    if estado_visual in ('en_preparacion', 'en_horno', 'listo', 'asignado_repartidor', 'en_camino', 'entregado'):
        activos.update(['recibido', 'pago'])
    if estado_visual in ('en_horno', 'listo', 'asignado_repartidor', 'en_camino', 'entregado'):
        activos.add('en_preparacion')
    if estado_visual in ('listo', 'asignado_repartidor', 'en_camino', 'entregado'):
        activos.add('en_horno')
    if estado_visual in ('asignado_repartidor', 'en_camino', 'entregado'):
        activos.add('listo')
    if estado_visual in ('entregado',):
        activos.add('en_camino')

    pasos_html = ''
    for codigo, label in pasos:
        bg = color if codigo in activos else '#e9dfd3'
        fg = 'white' if codigo in activos else '#7b6f62'
        pasos_html += f"""
        <td style="padding:4px;text-align:center">
          <div style="background:{bg};color:{fg};border-radius:999px;padding:8px 6px;font-size:12px;font-weight:700">{label}</div>
        </td>
        """

    return f"""
    <div style="margin:0;padding:0;background:{fondo};font-family:Arial,Helvetica,sans-serif;color:#292929">
      <div style="max-width:760px;margin:auto;padding:24px">
        <div style="background:white;border-radius:22px;overflow:hidden;border:1px solid #eadcc8;box-shadow:0 10px 30px rgba(0,0,0,.08)">
          <div style="background:{color};color:white;padding:28px">
            <div style="font-size:13px;letter-spacing:.12em;text-transform:uppercase;font-weight:700">CHINOS CAFE PIZZAFLOW</div>
            <h1 style="margin:10px 0 0;font-size:30px;line-height:1.15">{titulo}</h1>
            <p style="margin:8px 0 0;font-size:17px">Pedido {pedido.numero}</p>
          </div>

          <div style="padding:26px">
            <p style="font-size:18px;margin:0 0 10px">Hola <strong>{pedido.cliente.nombre}</strong>,</p>
            <p style="font-size:16px;line-height:1.55;margin:0 0 22px">{mensaje}</p>

            <table style="width:100%;border-collapse:collapse;margin:6px 0 22px">
              <tr>{pasos_html}</tr>
            </table>

            <div style="background:#fff8ef;border:1px solid #f0dfc8;border-radius:16px;padding:18px;margin:18px 0">
              <div style="font-size:13px;color:{color};text-transform:uppercase;font-weight:700">Resumen</div>
              <div><strong>Estado actual:</strong> {pedido.estado_actual}</div>
              <div><strong>Total:</strong> ${float(pedido.total):.2f}</div>
              <div><strong>Delivery:</strong> ${float(pedido.monto_delivery or 0):.2f}</div>
              <div><strong>Propina:</strong> ${float(pedido.propina or 0):.2f}</div>
              <div><strong>Direccion:</strong> {pedido.direccion_entrega or "Retiro en local"}</div>
            </div>

            {pago_html}

            <h2 style="font-size:20px;margin:24px 0 10px;color:{verde}">Detalle del pedido</h2>
            <table style="width:100%;border-collapse:collapse">
              <thead>
                <tr style="background:{verde};color:white">
                  <th style="padding:12px;text-align:left">Producto</th>
                  <th style="padding:12px;text-align:center">Cant.</th>
                  <th style="padding:12px;text-align:right">Subtotal</th>
                </tr>
              </thead>
              <tbody>{items_html}</tbody>
            </table>

            <div style="margin-top:24px;padding:16px;border-radius:14px;background:#f3f3f3;color:#555;font-size:13px;line-height:1.45">
              Adjuntamos el JSON del pedido, el comprobante de pago cuando exista y las imagenes disponibles de pizzas o combos.
            </div>
          </div>
        </div>
      </div>
    </div>
    """


def _pedido_texto(pedido, estado):
    return (
        f'Hola {pedido.cliente.nombre},\n\n'
        f'Tu pedido {pedido.numero} tiene estado: {estado}.\n'
        f'Total: ${float(pedido.total):.2f}\n\n'
        'CHINOS CAFE PIZZAFLOW'
    )


def _pedido_attachments(pedido, json_filename=None, incluir_comprobante=False, pago_actual=None):
    files = []

    if json_filename:
        files.append(_outbox_path(json_filename))

    if incluir_comprobante:
        pago = pago_actual
        if not pago:
            pago = pedido.pagos.order_by(Payment.fecha_pago.desc()).first()
        if pago and pago.comprobante:
            files.append(_static_or_upload_path(pago.comprobante))

    for detalle in pedido.detalles:
        imagen = None

        if detalle.tipo_item == 'pizza':
            item = Pizza.query.get(detalle.id_item)
            imagen = item.imagen if item else None

        if detalle.tipo_item == 'combo':
            item = Combo.query.get(detalle.id_item)
            imagen = item.imagen if item else None

        if imagen:
            files.append(_static_or_upload_path(imagen))

    clean = []
    seen = set()

    for file_path in files:
        if file_path and file_path not in seen and os.path.exists(file_path):
            seen.add(file_path)
            clean.append(file_path)

    return clean


def _outbox_path(filename):
    if not filename:
        return None
    return os.path.join(current_app.config['OUTBOX_FOLDER'], filename)


def _static_or_upload_path(path):
    if not path:
        return None

    normalized = static_image_url(path) or path
    normalized = normalized.replace('\\', '/').lstrip('/')

    static_path = os.path.join(current_app.root_path, 'static', *normalized.split('/'))
    if os.path.exists(static_path):
        return static_path

    upload_path = os.path.join(current_app.root_path, 'static', 'uploads', *normalized.split('/'))
    if os.path.exists(upload_path):
        return upload_path

    return static_path


def _registrar_outbox(id_pedido, destinatario, asunto, archivo):
    registro = OutboxEmail(
        id_pedido=id_pedido,
        destinatario=destinatario,
        asunto=asunto,
        archivo_generado=archivo,
        tipo='json',
        fecha_generado=datetime.utcnow(),
    )
    db.session.add(registro)


def _try_real_email(destinatario, asunto, cuerpo, id_pedido=None, html=None, attachments=None):
    if not destinatario or '@' not in destinatario:
        return {'ok': False, 'error': 'Destinatario invalido.'}

    return send_email(
        destinatario,
        asunto,
        cuerpo,
        order_id=id_pedido,
        fallback=True,
        html=html,
        attachments=attachments or [],
    )
