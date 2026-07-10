from flask import Blueprint, request, jsonify
from flask_login import current_user
from app.models import ChatbotResponse, Pizza, Combo, DeliveryZone, Order, SystemConfig

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


@chatbot_bp.route('/mensaje', methods=['POST'])
def mensaje():
    data = request.get_json()
    texto = (data.get('mensaje', '') or '').lower().strip()

    respuesta = _buscar_respuesta(texto)
    return jsonify({'respuesta': respuesta, 'bot': 'ChinoBot 🤖'})


def _buscar_respuesta(texto: str) -> str:
    # 1. Buscar en BD
    try:
        from app.models import ChatbotResponse
        respuestas = ChatbotResponse.query.filter_by(activo=True).all()
        for r in respuestas:
            clave = r.pregunta_clave.lower()
            palabras = [p.strip() for p in clave.split(',')]
            if any(p in texto for p in palabras if p):
                return r.respuesta
    except Exception:
        pass

    # 2. Lógica dinámica
    if any(w in texto for w in ['pizza', 'pizzas', 'tienen', 'menu', 'menú']):
        try:
            pizzas = Pizza.query.filter_by(estado='activa').all()
            nombres = ', '.join(p.nombre for p in pizzas[:6])
            return f'🍕 Tenemos estas pizzas disponibles: {nombres}. ¡Todas deliciosas!'
        except Exception:
            return '🍕 Tenemos muchas pizzas increíbles. Visita nuestro menú para ver todas las opciones.'

    if any(w in texto for w in ['combo', 'combos', 'oferta']):
        try:
            combos = Combo.query.filter_by(estado='activo').all()
            lista = ', '.join(f'{c.nombre} (${c.precio})' for c in combos[:4])
            return f'🎁 Combos disponibles: {lista}. ¡Perfectos para compartir!'
        except Exception:
            return '🎁 ¡Tenemos combos increíbles! Revisa la sección de combos en nuestro menú.'

    if any(w in texto for w in ['delivery', 'entrega', 'envío', 'envio', 'flete', 'costo']):
        try:
            zonas = DeliveryZone.query.filter_by(estado='activa').order_by(DeliveryZone.costo_delivery).all()
            if zonas:
                rango = f'${float(zonas[0].costo_delivery):.2f} a ${float(zonas[-1].costo_delivery):.2f}'
                return f'🛵 El costo de delivery varía de {rango} según tu zona. ¡Llevamos hasta tu puerta!'
        except Exception:
            pass
        return '🛵 Nuestro delivery varía según la zona. David Centro desde $2.00. ¡Rápido y seguro!'

    if any(w in texto for w in ['yappy', 'pago', 'pagar', 'efectivo', 'tarjeta']):
        return '💳 ¡Sí aceptamos Yappy Comercial! También efectivo y tarjeta simulada. Comercio: CHINOS CAFÉ S.A.'

    if any(w in texto for w in ['pedido', 'estado', 'donde', 'dónde', 'rastrear']):
        if current_user.is_authenticated:
            try:
                ultimo = Order.query.filter_by(id_cliente=current_user.id)\
                               .order_by(Order.fecha_pedido.desc()).first()
                if ultimo:
                    return f'📦 Tu último pedido es {ultimo.numero} y está en estado: **{ultimo.estado_actual}**.'
            except Exception:
                pass
        return '📦 Para ver tu pedido, inicia sesión y ve a "Mis Pedidos". Ahí verás el timeline en tiempo real.'

    if any(w in texto for w in ['repartidor', 'ganancia', 'comision', 'comisión']):
        pct = SystemConfig.get('porcentaje_comision', '60')
        return f'🛵 Nuestros repartidores ganan el {pct}% del flete más las propinas. ¡Un ingreso justo!'

    if any(w in texto for w in ['horario', 'hora', 'abren', 'cierran', 'abierto']):
        return '🕐 Atendemos de Lunes a Domingo de 11:00 AM a 10:00 PM. ¡Siempre listos para servirte!'

    if any(w in texto for w in ['hola', 'buenos', 'buenas', 'saludo', 'hey', 'hi']):
        return '👋 ¡Hola! Soy ChinoBot, el asistente virtual de CHINOS CAFÉ. ¿En qué te puedo ayudar hoy?'

    if any(w in texto for w in ['gracias', 'thanks', 'perfecto', 'excelente']):
        return '😊 ¡Con mucho gusto! En CHINOS CAFÉ siempre estamos para servirte. ¡Que disfrutes tu pizza! 🍕'

    return '🤔 No entendí bien tu pregunta. Puedes preguntarme sobre pizzas, combos, delivery, pagos o el estado de tu pedido.'
