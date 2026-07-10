from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Role, AuditLog

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        attempts = int(session.get('login_attempts', 0))
        if attempts >= 5:
            flash('Demasiados intentos. Reinicia la sesion del navegador antes de intentar de nuevo.', 'danger')
            return render_template('auth/login.html')

        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')

        try:
            user = User.query.filter_by(usuario=usuario, estado='activo').first()
            if user and user.check_password(password):
                login_user(user)
                session['login_attempts'] = 0
                db.session.add(AuditLog(
                    id_usuario=user.id,
                    accion='LOGIN',
                    descripcion=f'Inicio de sesion: {user.usuario}',
                    ip_origen=request.remote_addr,
                ))
                db.session.commit()
                flash(f'Bienvenido, {user.nombre}.', 'success')
                return _redirect_by_role(user)
            session['login_attempts'] = attempts + 1
            flash('Usuario o contrasena incorrectos.', 'danger')
        except Exception:
            flash('Error del sistema. Intenta de nuevo.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        telefono = request.form.get('telefono', '').strip()
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not nombre or not correo or not usuario or not password:
            flash('Completa todos los campos obligatorios.', 'warning')
            return render_template('auth/register.html')
        if password != confirm:
            flash('Las contrasenas no coinciden.', 'warning')
            return render_template('auth/register.html')
        if len(password) < 6:
            flash('La contrasena debe tener al menos 6 caracteres.', 'warning')
            return render_template('auth/register.html')
        if User.query.filter_by(correo=correo).first():
            flash('Ese correo ya esta registrado.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(usuario=usuario).first():
            flash('Ese usuario ya existe.', 'danger')
            return render_template('auth/register.html')

        try:
            rol = Role.query.filter_by(nombre='Cliente').first()
            if not rol:
                flash('Rol de cliente no configurado.', 'danger')
                return render_template('auth/register.html')
            user = User(id_rol=rol.id, nombre=nombre, correo=correo, telefono=telefono, usuario=usuario)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Cuenta creada. Ya puedes iniciar sesion.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('No se pudo completar el registro. Intenta de nuevo.', 'danger')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    try:
        db.session.add(AuditLog(
            id_usuario=current_user.id,
            accion='LOGOUT',
            descripcion=f'Cierre de sesion: {current_user.usuario}',
            ip_origen=request.remote_addr,
        ))
        db.session.commit()
    except Exception:
        pass
    logout_user()
    flash('Sesion cerrada correctamente.', 'info')
    return redirect(url_for('public.index'))


def _redirect_by_role(user):
    role = user.rol_nombre
    if role == 'Administrador':
        return redirect(url_for('admin.dashboard'))
    if role == 'Operario/Cocina':
        return redirect(url_for('cocina.dashboard'))
    if role == 'Repartidor':
        return redirect(url_for('repartidor.dashboard'))
    return redirect(url_for('cliente.dashboard'))
