import json
import os
from datetime import datetime
from flask import current_app


def _outbox_path():
    return current_app.config.get('OUTBOX_FOLDER', 'outbox')


def _write_json(filename: str, data: dict) -> str:
    """Write JSON file to outbox folder. Returns full path."""
    folder = _outbox_path()
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        try:
            from app.extensions import db
            from app.models import JsonLog
            pedido_id = data.get('pedido', {}).get('id') if isinstance(data.get('pedido'), dict) else None
            if not pedido_id:
                import re
                match = re.search(r'_(\d{4,})\.json$', filename)
                pedido_id = int(match.group(1)) if match else None
            db.session.add(JsonLog(
                id_pedido=pedido_id,
                tipo_json=data.get('tipo', filename.split('_')[0]),
                contenido_json=json.dumps(data, ensure_ascii=False, indent=2, default=str),
                archivo=filename,
            ))
        except Exception as log_exc:
            current_app.logger.warning(f'JSON log not stored for {filename}: {log_exc}')
        return filepath
    except Exception as e:
        current_app.logger.error(f'Error writing JSON {filename}: {e}')
        return ''


def generar_json_pedido_cliente(pedido) -> str:
    data = {
        'tipo': 'CONFIRMACION_PEDIDO_CLIENTE',
        'empresa': 'CHINOS CAFÉ S.A.',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': {
            'numero': pedido.numero,
            'fecha': pedido.fecha_pedido.isoformat(),
            'estado': pedido.estado_actual,
            'cliente': pedido.cliente.nombre,
            'metodo_entrega': pedido.metodo_entrega.nombre if pedido.metodo_entrega else '',
            'subtotal': float(pedido.subtotal),
            'delivery': float(pedido.monto_delivery),
            'impuesto': float(pedido.impuesto),
            'total': float(pedido.total),
            'items': [
                {
                    'tipo': d.tipo_item,
                    'nombre': d.nombre_item,
                    'cantidad': d.cantidad,
                    'precio_unitario': float(d.precio_unitario),
                    'subtotal': float(d.subtotal),
                }
                for d in pedido.detalles
            ],
        },
    }
    filename = f'pedido_cliente_{pedido.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_pedido_empresa(pedido) -> str:
    data = {
        'tipo': 'NOTIFICACION_EMPRESA',
        'empresa': 'CHINOS CAFÉ S.A.',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': {
            'numero': pedido.numero,
            'cliente': {'nombre': pedido.cliente.nombre, 'correo': pedido.cliente.correo},
            'total': float(pedido.total),
            'metodo_entrega': pedido.metodo_entrega.nombre if pedido.metodo_entrega else '',
            'zona': pedido.zona.nombre_zona if pedido.zona else 'Retiro local',
            'estado': pedido.estado_actual,
        },
    }
    filename = f'pedido_empresa_{pedido.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_pedido_operario(pedido) -> str:
    data = {
        'tipo': 'ORDEN_COCINA',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': {
            'numero': pedido.numero,
            'items': [
                {
                    'nombre': d.nombre_item,
                    'cantidad': d.cantidad,
                    'ingredientes_extra': d.ingredientes_extra or '',
                }
                for d in pedido.detalles
            ],
            'observaciones': pedido.observaciones or '',
        },
    }
    filename = f'pedido_operario_{pedido.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_pago(pago) -> str:
    data = {
        'tipo': 'CONFIRMACION_PAGO',
        'empresa': 'CHINOS CAFÉ S.A.',
        'timestamp': datetime.utcnow().isoformat(),
        'pago': {
            'id': pago.id,
            'pedido': pago.pedido.numero,
            'metodo': pago.metodo,
            'referencia': pago.referencia,
            'monto': float(pago.monto),
            'estado': pago.estado,
            'fecha': pago.fecha_pago.isoformat(),
        },
    }
    filename = f'pago_empresa_{pago.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_cancelacion(pedido, motivo, reembolso=False) -> str:
    data = {
        'tipo': 'CANCELACION_PEDIDO',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': {
            'numero': pedido.numero,
            'cliente': pedido.cliente.nombre,
            'estado': pedido.estado_actual,
            'motivo': motivo,
            'total': float(pedido.total),
            'reembolso_simulado': bool(reembolso),
        },
    }
    filename = f'cancelacion_{pedido.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_reembolso(pedido, monto, motivo) -> str:
    data = {
        'tipo': 'REEMBOLSO_SIMULADO',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': pedido.numero,
        'monto': float(monto),
        'motivo': motivo,
        'estado': 'pendiente_revision',
    }
    filename = f'reembolso_{pedido.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_entrega(reporte) -> str:
    data = {
        'tipo': 'REPORTE_ENTREGA',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': reporte.pedido.numero,
        'resultado': reporte.resultado,
        'observacion_final': reporte.observacion_final,
        'hora_entrega': reporte.hora_entrega.isoformat() if reporte.hora_entrega else None,
    }
    filename = f'entrega_{reporte.id:04d}.json'
    return _write_json(filename, data), filename


def generar_json_retiro(pedido) -> str:
    data = {
        'tipo': 'CONFIRMACION_RETIRO_LOCAL',
        'timestamp': datetime.utcnow().isoformat(),
        'pedido': {
            'id': pedido.id,
            'numero': pedido.numero,
            'cliente': pedido.cliente.nombre,
            'estado': pedido.estado_actual,
            'codigo_retiro': pedido.retiro.codigo_retiro if pedido.retiro else None,
            'fecha_retiro': pedido.retiro.fecha_retiro.isoformat() if pedido.retiro and pedido.retiro.fecha_retiro else None,
            'total': float(pedido.total),
            'items': [
                {
                    'tipo': d.tipo_item,
                    'nombre': d.nombre_item,
                    'cantidad': d.cantidad,
                    'subtotal': float(d.subtotal),
                }
                for d in pedido.detalles
            ],
        },
    }
    filename = f'retiro_local_{pedido.id:04d}.json'
    return _write_json(filename, data), filename
