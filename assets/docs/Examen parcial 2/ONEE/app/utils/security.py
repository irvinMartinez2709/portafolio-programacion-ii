from functools import wraps
from flask import flash, redirect, request, url_for
from flask_login import current_user


def role_required(*role_names):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.rol_nombre not in role_names:
                flash('Acceso no autorizado.', 'danger')
                return redirect(url_for('public.index'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def audit_description(action, entity, entity_id=None):
    ident = f' #{entity_id}' if entity_id else ''
    return f'{action} {entity}{ident} desde {request.remote_addr or "local"}'
