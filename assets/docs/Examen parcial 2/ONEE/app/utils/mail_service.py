import json
import mimetypes
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from flask import current_app

from app.extensions import db
from app.models import OutboxEmail


def smtp_config():
    return {
        'server': (current_app.config.get('MAIL_SERVER') or '').strip(),
        'port': int(current_app.config.get('MAIL_PORT') or 587),
        'use_tls': bool(current_app.config.get('MAIL_USE_TLS')),
        'username': (current_app.config.get('MAIL_USERNAME') or '').strip(),
        'password': (current_app.config.get('MAIL_PASSWORD') or '').strip(),
        'sender': (
            current_app.config.get('MAIL_DEFAULT_SENDER')
            or current_app.config.get('MAIL_USERNAME')
            or ''
        ).strip(),
    }


def smtp_status():
    cfg = smtp_config()
    missing = []
    for key in ('server', 'port', 'sender', 'password'):
        if not cfg.get(key):
            missing.append(key)

    return {
        'configured': not missing,
        'missing': missing,
        'server': cfg['server'],
        'port': cfg['port'],
        'use_tls': cfg['use_tls'],
        'sender': cfg['sender'],
        'username': cfg['username'],
    }


def sanitize_error(exc):
    msg = str(exc)
    cfg = smtp_config()
    for secret in (cfg.get('password'), cfg.get('username')):
        if secret:
            msg = msg.replace(secret, '***')
    return msg[:500]


def send_email(to, subject, body, order_id=None, fallback=True, html=None, attachments=None):
    attachments = attachments or []

    record = OutboxEmail(
        id_pedido=order_id,
        destinatario=to,
        asunto=subject,
        archivo_generado='smtp',
        tipo='smtp',
        fecha_generado=datetime.utcnow(),
        estado_envio='pendiente',
        cuerpo=body,
    )
    db.session.add(record)
    db.session.commit()

    result = _deliver_record(record, html=html, attachments=attachments)

    if not result['ok'] and fallback:
        _write_fallback_json(record, body, result['error'])

    return result


def retry_email(record):
    if not record.cuerpo:
        record.error_envio = 'No hay cuerpo de correo guardado para reintentar.'
        record.estado_envio = 'fallido'
        db.session.commit()
        return {'ok': False, 'error': record.error_envio}

    return _deliver_record(record)


def _deliver_record(record, html=None, attachments=None):
    cfg = smtp_config()
    attachments = attachments or []

    try:
        if not smtp_status()['configured']:
            raise RuntimeError(
                'SMTP incompleto. Revisa MAIL_SERVER, MAIL_PORT, '
                'MAIL_DEFAULT_SENDER y MAIL_PASSWORD.'
            )

        msg = EmailMessage()
        msg['From'] = cfg['sender']
        msg['To'] = record.destinatario
        msg['Subject'] = record.asunto

        msg.set_content(record.cuerpo or '')

        if html:
            msg.add_alternative(html, subtype='html')

        for file_path in attachments:
            _attach_file(msg, file_path)

        if cfg['use_tls']:
            with smtplib.SMTP(cfg['server'], cfg['port'], timeout=25) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                if cfg['username']:
                    smtp.login(cfg['username'], cfg['password'])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg['server'], cfg['port'], timeout=25) as smtp:
                if cfg['username']:
                    smtp.login(cfg['username'], cfg['password'])
                smtp.send_message(msg)

        record.estado_envio = 'enviado'
        record.error_envio = ''
        record.fecha_envio = datetime.utcnow()
        db.session.commit()
        return {'ok': True, 'error': None}

    except Exception as exc:
        db.session.rollback()
        record = OutboxEmail.query.get(record.id)
        if record:
            record.estado_envio = 'fallido'
            record.error_envio = sanitize_error(exc)
            db.session.commit()
        return {'ok': False, 'error': sanitize_error(exc)}


def _attach_file(msg, file_path):
    if not file_path or not os.path.exists(file_path):
        return

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'

    maintype, subtype = mime_type.split('/', 1)

    with open(file_path, 'rb') as fh:
        msg.add_attachment(
            fh.read(),
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(file_path),
        )


def _write_fallback_json(record, body, error):
    folder = current_app.config.get('OUTBOX_FOLDER', 'outbox')
    os.makedirs(folder, exist_ok=True)

    filename = f'correo_pendiente_{record.id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.json'
    payload = {
        'id': record.id,
        'pedido': record.id_pedido,
        'destinatario': record.destinatario,
        'asunto': record.asunto,
        'cuerpo': body,
        'error_smtp': error,
        'fecha': datetime.utcnow().isoformat(),
    }

    with open(os.path.join(folder, filename), 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    record.archivo_generado = filename
    db.session.commit()


def send_test_email(to=None):
    status = smtp_status()
    recipient = to or status['sender'] or status['username']

    return send_email(
        recipient,
        'Prueba SMTP CHINOS CAFE PIZZAFLOW',
        'Este es un correo real de prueba enviado desde el panel administrador.',
        html="""
        <div style="font-family:Arial,sans-serif;background:#f8f3eb;padding:24px">
          <div style="max-width:620px;margin:auto;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #eadcc8">
            <div style="background:#b7352c;color:white;padding:22px">
              <h1 style="margin:0">CHINOS CAFE PIZZAFLOW</h1>
              <p style="margin:6px 0 0">SMTP funcionando correctamente</p>
            </div>
            <div style="padding:24px;color:#2b2b2b">
              <h2 style="margin-top:0">Correo de prueba enviado</h2>
              <p>Si recibiste este mensaje, el envio real por SMTP ya esta activo.</p>
            </div>
          </div>
        </div>
        """,
    )