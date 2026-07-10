import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from decimal import Decimal
from datetime import datetime
from app.extensions import db
from app.models import (Pizza, Ingredient, PizzaCrust, PizzaSauce, Drink, Extra, Combo, ComboDetail,
                        DeliveryZone, District, Township, Driver, Employee, User, Role,
                        Order, OrderStatusHistory, Payment, SystemConfig, OutboxEmail, JsonLog,
                        Branch, AuditLog, Notification, ChatbotResponse, Cook, ZoneChangeRequest)
from app.models import DeliveryAssignment
from app.utils.calculations import calcular_delivery
from app.utils.email_simulator import simular_correo_cancelacion
from app.utils.file_uploads import save_catalog_image
from app.utils.mail_service import smtp_status, send_test_email, retry_email
from app.utils.email_simulator import simular_correo_cancelacion, simular_correo_estado_pedido

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated


def _decimal_form(name, default='0'):
    return Decimal(str(request.form.get(name, default) or default)).quantize(Decimal('0.01'))


def _admin_count():
    rol_admin = Role.query.filter_by(nombre='Administrador').first()
    if not rol_admin:
        return 0
    return User.query.filter_by(id_rol=rol_admin.id, estado='activo').count()


def _validate_unique_user(user):
    duplicate_usuario = User.query.filter(User.usuario == user.usuario, User.id != user.id).first()
    if duplicate_usuario:
        raise ValueError('Ese nombre de usuario ya existe.')
    if user.correo:
        duplicate_correo = User.query.filter(User.correo == user.correo, User.id != user.id).first()
        if duplicate_correo:
            raise ValueError('Ese correo ya esta registrado.')


def _employee_for(user, cargo):
    emp = Employee.query.filter_by(id_usuario=user.id).first()
    if not emp:
        emp = Employee(id_usuario=user.id, cargo=cargo)
        db.session.add(emp)
        db.session.flush()
    else:
        emp.cargo = cargo
    return emp


def _sync_staff_profile(user):
    if user.rol_nombre == 'Operario/Cocina':
        emp = _employee_for(user, 'Operario de Cocina')
        if not Cook.query.filter_by(id_empleado=emp.id).first():
            db.session.add(Cook(
                id_empleado=emp.id,
                especialidad=request.form.get('especialidad', 'Pizzas artesanales'),
                turno=request.form.get('turno', 'tarde'),
            ))
    elif user.rol_nombre == 'Repartidor':
        emp = _employee_for(user, 'Repartidor')
        driver = Driver.query.filter_by(id_empleado=emp.id).first()
        if not driver:
            driver = Driver(id_empleado=emp.id)
            db.session.add(driver)
        driver.tipo_vehiculo = request.form.get('tipo_vehiculo', driver.tipo_vehiculo or 'moto')
        driver.placa = request.form.get('placa', driver.placa or '')
        driver.disponible = request.form.get('disponible', '1') == '1'
        driver.porcentaje_comision = _decimal_form('porcentaje_comision', str(driver.porcentaje_comision or 60))
        driver.id_zona_actual = int(request.form['id_zona_actual']) if request.form.get('id_zona_actual') else None


def _delete_or_block(item, redirect_endpoint, label):
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'{label} eliminado definitivamente.', 'success')
    except Exception:
        db.session.rollback()
        flash(f'No se puede eliminar {label} porque tiene relaciones. Puedes desactivarlo.', 'warning')
    return redirect(url_for(redirect_endpoint))


# ─── DASHBOARD ───────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@require_admin
def dashboard():
    from datetime import date
    from sqlalchemy import func
    hoy = date.today()

    try:
        pedidos_hoy = Order.query.filter(
            db.func.date(Order.fecha_pedido) == hoy
        ).count()
        pagos_confirmados = Payment.query.filter_by(estado='pagado').count()
        total_vendido = db.session.query(
            db.func.sum(Payment.monto)
        ).filter_by(estado='pagado').scalar() or 0
        pizzas_activas = Pizza.query.filter_by(estado='activa').count()
        zonas_activas = DeliveryZone.query.filter_by(estado='activa').count()
        correos_generados = OutboxEmail.query.count()
        json_generados = JsonLog.query.count()
        pedidos_recientes = Order.query.order_by(Order.fecha_pedido.desc()).limit(10).all()
    except Exception as e:
        pedidos_hoy = pagos_confirmados = pizzas_activas = zonas_activas = 0
        total_vendido = correos_generados = json_generados = 0
        pedidos_recientes = []

    return render_template('admin/dashboard.html',
                           pedidos_hoy=pedidos_hoy,
                           pagos_confirmados=pagos_confirmados,
                           total_vendido=float(total_vendido),
                           pizzas_activas=pizzas_activas,
                           zonas_activas=zonas_activas,
                           correos_generados=correos_generados,
                           json_generados=json_generados,
                           pedidos_recientes=pedidos_recientes)


# ─── PIZZAS ──────────────────────────────────────────────────────────────────
@admin_bp.route('/pizzas')
@login_required
@require_admin
def pizzas():
    items = Pizza.query.order_by(Pizza.id.desc()).all()
    return render_template('admin/pizzas.html', pizzas=items)


@admin_bp.route('/pizzas/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_pizza():
    ingredientes = Ingredient.query.filter_by(estado='activo').all()
    if request.method == 'POST':
        try:
            p = Pizza(
                nombre=request.form['nombre'],
                descripcion=request.form.get('descripcion', ''),
                tipo_masa=request.form.get('tipo_masa', ''),
                tipo_salsa=request.form.get('tipo_salsa', ''),
                tipo_queso=request.form.get('tipo_queso', ''),
                precio_base=Decimal(request.form['precio_base']),
                estado=request.form.get('estado', 'activa'),
            )
            imagen = save_catalog_image(request.files.get('imagen'), 'pizza', 'pizza')
            if imagen:
                p.imagen = imagen
            db.session.add(p)
            db.session.commit()
            flash('Pizza creada exitosamente.', 'success')
            return redirect(url_for('admin.pizzas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_pizza.html', ingredientes=ingredientes)


@admin_bp.route('/pizzas/editar/<int:pid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_pizza(pid):
    p = Pizza.query.get_or_404(pid)
    if request.method == 'POST':
        try:
            p.nombre = request.form['nombre']
            p.descripcion = request.form.get('descripcion', '')
            p.tipo_masa = request.form.get('tipo_masa', '')
            p.tipo_salsa = request.form.get('tipo_salsa', '')
            p.tipo_queso = request.form.get('tipo_queso', '')
            p.precio_base = Decimal(request.form['precio_base'])
            p.estado = request.form.get('estado', 'activa')
            imagen = save_catalog_image(request.files.get('imagen'), 'pizza', f'pizza_{pid}')
            if imagen:
                p.imagen = imagen
            db.session.commit()
            flash('Pizza actualizada.', 'success')
            return redirect(url_for('admin.pizzas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/editar_pizza.html', pizza=p)


@admin_bp.route('/pizzas/eliminar/<int:pid>', methods=['POST'])
@login_required
@require_admin
def eliminar_pizza(pid):
    p = Pizza.query.get_or_404(pid)
    try:
        p.estado = 'inactiva'
        db.session.commit()
        flash('Pizza desactivada.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin.pizzas'))


@admin_bp.route('/pizzas/eliminar-definitivo/<int:pid>', methods=['POST'])
@login_required
@require_admin
def eliminar_pizza_definitivo(pid):
    return _delete_or_block(Pizza.query.get_or_404(pid), 'admin.pizzas', 'pizza')


# ─── INGREDIENTES ────────────────────────────────────────────────────────────
@admin_bp.route('/ingredientes')
@login_required
@require_admin
def ingredientes():
    items = Ingredient.query.order_by(Ingredient.categoria, Ingredient.nombre).all()
    return render_template('admin/ingredientes.html', ingredientes=items)


@admin_bp.route('/ingredientes/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_ingrediente():
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'ingrediente', 'ingrediente')
            i = Ingredient(
                nombre=request.form['nombre'],
                categoria=request.form.get('categoria', ''),
                precio_extra=Decimal(request.form.get('precio_extra', '0')),
                stock=int(request.form.get('stock', 100)),
                imagen=imagen,
                icono=request.form.get('icono', '🧀'),
            )
            db.session.add(i)
            db.session.commit()
            flash('Ingrediente creado.', 'success')
            return redirect(url_for('admin.ingredientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_ingrediente.html')


@admin_bp.route('/ingredientes/editar/<int:iid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_ingrediente(iid):
    item = Ingredient.query.get_or_404(iid)
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'ingrediente', f'ingrediente_{iid}')
            item.nombre = request.form['nombre']
            item.categoria = request.form.get('categoria', '')
            item.precio_extra = Decimal(request.form.get('precio_extra', '0'))
            item.stock = int(request.form.get('stock', 100))
            item.icono = request.form.get('icono', '🧀')
            if imagen:
                item.imagen = imagen
            item.estado = request.form.get('estado', 'activo')
            db.session.commit()
            flash('Ingrediente actualizado.', 'success')
            return redirect(url_for('admin.ingredientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/editar_ingrediente.html', ingrediente=item)


# ─── REFRESCOS ───────────────────────────────────────────────────────────────
@admin_bp.route('/ingredientes/toggle/<int:iid>', methods=['POST'])
@login_required
@require_admin
def toggle_ingrediente(iid):
    item = Ingredient.query.get_or_404(iid)
    item.estado = 'inactivo' if item.estado == 'activo' else 'activo'
    db.session.commit()
    flash('Ingrediente actualizado.', 'info')
    return redirect(url_for('admin.ingredientes'))


@admin_bp.route('/ingredientes/eliminar/<int:iid>', methods=['POST'])
@login_required
@require_admin
def eliminar_ingrediente(iid):
    return _delete_or_block(Ingredient.query.get_or_404(iid), 'admin.ingredientes', 'ingrediente')


@admin_bp.route('/masas')
@login_required
@require_admin
def masas():
    items = PizzaCrust.query.order_by(PizzaCrust.nombre).all()
    return render_template('admin/catalogo_visual.html', items=items, tipo='masas',
                           titulo='Masas', crear_endpoint='admin.crear_masa')


@admin_bp.route('/masas/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_masa():
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'masa', 'masa')
            item = PizzaCrust(
                nombre=request.form['nombre'],
                codigo=request.form['codigo'],
                precio_adicional=_decimal_form('precio_adicional'),
                imagen=imagen,
                estado=request.form.get('estado', 'activa'),
            )
            db.session.add(item)
            db.session.commit()
            flash('Masa guardada.', 'success')
            return redirect(url_for('admin.masas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/catalogo_visual_form.html', item=None, tipo='masa',
                           volver='admin.masas')


@admin_bp.route('/masas/editar/<int:item_id>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_masa(item_id):
    item = PizzaCrust.query.get_or_404(item_id)
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'masa', f'masa_{item_id}')
            item.nombre = request.form['nombre']
            item.codigo = request.form['codigo']
            item.precio_adicional = _decimal_form('precio_adicional')
            item.estado = request.form.get('estado', 'activa')
            if imagen:
                item.imagen = imagen
            db.session.commit()
            flash('Masa actualizada.', 'success')
            return redirect(url_for('admin.masas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/catalogo_visual_form.html', item=item, tipo='masa',
                           volver='admin.masas')


@admin_bp.route('/masas/toggle/<int:item_id>', methods=['POST'])
@login_required
@require_admin
def toggle_masa(item_id):
    item = PizzaCrust.query.get_or_404(item_id)
    item.estado = 'inactiva' if item.estado == 'activa' else 'activa'
    db.session.commit()
    flash('Masa actualizada.', 'info')
    return redirect(url_for('admin.masas'))


@admin_bp.route('/masas/eliminar/<int:item_id>', methods=['POST'])
@login_required
@require_admin
def eliminar_masa(item_id):
    return _delete_or_block(PizzaCrust.query.get_or_404(item_id), 'admin.masas', 'masa')


@admin_bp.route('/salsas')
@login_required
@require_admin
def salsas():
    items = PizzaSauce.query.order_by(PizzaSauce.nombre).all()
    return render_template('admin/catalogo_visual.html', items=items, tipo='salsas',
                           titulo='Salsas', crear_endpoint='admin.crear_salsa')


@admin_bp.route('/salsas/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_salsa():
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'salsa', 'salsa')
            item = PizzaSauce(
                nombre=request.form['nombre'],
                codigo=request.form['codigo'],
                precio_adicional=_decimal_form('precio_adicional'),
                imagen=imagen,
                estado=request.form.get('estado', 'activa'),
            )
            db.session.add(item)
            db.session.commit()
            flash('Salsa guardada.', 'success')
            return redirect(url_for('admin.salsas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/catalogo_visual_form.html', item=None, tipo='salsa',
                           volver='admin.salsas')


@admin_bp.route('/salsas/editar/<int:item_id>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_salsa(item_id):
    item = PizzaSauce.query.get_or_404(item_id)
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'salsa', f'salsa_{item_id}')
            item.nombre = request.form['nombre']
            item.codigo = request.form['codigo']
            item.precio_adicional = _decimal_form('precio_adicional')
            item.estado = request.form.get('estado', 'activa')
            if imagen:
                item.imagen = imagen
            db.session.commit()
            flash('Salsa actualizada.', 'success')
            return redirect(url_for('admin.salsas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/catalogo_visual_form.html', item=item, tipo='salsa',
                           volver='admin.salsas')


@admin_bp.route('/salsas/toggle/<int:item_id>', methods=['POST'])
@login_required
@require_admin
def toggle_salsa(item_id):
    item = PizzaSauce.query.get_or_404(item_id)
    item.estado = 'inactiva' if item.estado == 'activa' else 'activa'
    db.session.commit()
    flash('Salsa actualizada.', 'info')
    return redirect(url_for('admin.salsas'))


@admin_bp.route('/salsas/eliminar/<int:item_id>', methods=['POST'])
@login_required
@require_admin
def eliminar_salsa(item_id):
    return _delete_or_block(PizzaSauce.query.get_or_404(item_id), 'admin.salsas', 'salsa')


@admin_bp.route('/refrescos')
@login_required
@require_admin
def refrescos():
    items = Drink.query.order_by(Drink.nombre).all()
    return render_template('admin/refrescos.html', refrescos=items)


@admin_bp.route('/refrescos/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_refresco():
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'refresco', 'refresco')
            r = Drink(
                nombre=request.form['nombre'],
                tamano=request.form.get('tamano', ''),
                precio=Decimal(request.form['precio']),
                stock=int(request.form.get('stock', 50)),
                imagen=imagen,
            )
            db.session.add(r)
            db.session.commit()
            flash('Refresco creado.', 'success')
            return redirect(url_for('admin.refrescos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_refresco.html')


@admin_bp.route('/refrescos/editar/<int:rid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_refresco(rid):
    item = Drink.query.get_or_404(rid)
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'refresco', f'refresco_{rid}')
            item.nombre = request.form['nombre']
            item.tamano = request.form.get('tamano', '')
            item.precio = _decimal_form('precio')
            item.stock = int(request.form.get('stock', 50))
            item.estado = request.form.get('estado', 'activo')
            if imagen:
                item.imagen = imagen
            db.session.commit()
            flash('Refresco actualizado.', 'success')
            return redirect(url_for('admin.refrescos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/editar_refresco.html', refresco=item)


@admin_bp.route('/refrescos/toggle/<int:rid>', methods=['POST'])
@login_required
@require_admin
def toggle_refresco(rid):
    item = Drink.query.get_or_404(rid)
    item.estado = 'inactivo' if item.estado == 'activo' else 'activo'
    db.session.commit()
    flash('Refresco actualizado.', 'info')
    return redirect(url_for('admin.refrescos'))


@admin_bp.route('/refrescos/eliminar/<int:rid>', methods=['POST'])
@login_required
@require_admin
def eliminar_refresco(rid):
    return _delete_or_block(Drink.query.get_or_404(rid), 'admin.refrescos', 'refresco')


# ─── ADICIONALES ─────────────────────────────────────────────────────────────
@admin_bp.route('/adicionales')
@login_required
@require_admin
def adicionales():
    items = Extra.query.order_by(Extra.nombre).all()
    return render_template('admin/adicionales.html', adicionales=items)


@admin_bp.route('/adicionales/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_adicional():
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'adicional', 'adicional')
            a = Extra(
                nombre=request.form['nombre'],
                descripcion=request.form.get('descripcion', ''),
                categoria=request.form.get('categoria', ''),
                precio=Decimal(request.form['precio']),
                stock=int(request.form.get('stock', 50)),
                imagen=imagen,
            )
            db.session.add(a)
            db.session.commit()
            flash('Adicional creado.', 'success')
            return redirect(url_for('admin.adicionales'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_adicional.html')


@admin_bp.route('/adicionales/editar/<int:aid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_adicional(aid):
    item = Extra.query.get_or_404(aid)
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'adicional', f'adicional_{aid}')
            item.nombre = request.form['nombre']
            item.descripcion = request.form.get('descripcion', '')
            item.categoria = request.form.get('categoria', '')
            item.precio = _decimal_form('precio')
            item.stock = int(request.form.get('stock', 50))
            item.estado = request.form.get('estado', 'activo')
            if imagen:
                item.imagen = imagen
            db.session.commit()
            flash('Adicional actualizado.', 'success')
            return redirect(url_for('admin.adicionales'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/editar_adicional.html', adicional=item)


@admin_bp.route('/adicionales/toggle/<int:aid>', methods=['POST'])
@login_required
@require_admin
def toggle_adicional(aid):
    item = Extra.query.get_or_404(aid)
    item.estado = 'inactivo' if item.estado == 'activo' else 'activo'
    db.session.commit()
    flash('Adicional actualizado.', 'info')
    return redirect(url_for('admin.adicionales'))


@admin_bp.route('/adicionales/eliminar/<int:aid>', methods=['POST'])
@login_required
@require_admin
def eliminar_adicional(aid):
    return _delete_or_block(Extra.query.get_or_404(aid), 'admin.adicionales', 'adicional')


# ─── COMBOS ──────────────────────────────────────────────────────────────────
@admin_bp.route('/combos')
@login_required
@require_admin
def combos():
    items = Combo.query.order_by(Combo.id.desc()).all()
    return render_template('admin/combos.html', combos=items)


@admin_bp.route('/combos/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_combo():
    pizzas = Pizza.query.filter_by(estado='activa').all()
    bebidas = Drink.query.filter_by(estado='activo').all()
    adicionales = Extra.query.filter_by(estado='activo').all()
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'combo', 'combo')
            c = Combo(
                nombre=request.form['nombre'],
                descripcion=request.form.get('descripcion', ''),
                precio=Decimal(request.form['precio']),
                imagen=imagen or 'combo_default.png',
            )
            db.session.add(c)
            db.session.commit()
            flash('Combo creado.', 'success')
            return redirect(url_for('admin.combos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_combo.html',
                           pizzas=pizzas, bebidas=bebidas, adicionales=adicionales)


@admin_bp.route('/combos/editar/<int:cid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_combo(cid):
    item = Combo.query.get_or_404(cid)
    pizzas = Pizza.query.filter_by(estado='activa').all()
    bebidas = Drink.query.filter_by(estado='activo').all()
    adicionales = Extra.query.filter_by(estado='activo').all()
    if request.method == 'POST':
        try:
            imagen = save_catalog_image(request.files.get('imagen'), 'combo', f'combo_{cid}')
            item.nombre = request.form['nombre']
            item.descripcion = request.form.get('descripcion', '')
            item.precio = _decimal_form('precio')
            item.estado = request.form.get('estado', 'activo')
            if imagen:
                item.imagen = imagen
            db.session.commit()
            flash('Combo actualizado.', 'success')
            return redirect(url_for('admin.combos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/editar_combo.html', combo=item,
                           pizzas=pizzas, bebidas=bebidas, adicionales=adicionales)


@admin_bp.route('/combos/toggle/<int:cid>', methods=['POST'])
@login_required
@require_admin
def toggle_combo(cid):
    item = Combo.query.get_or_404(cid)
    item.estado = 'inactivo' if item.estado == 'activo' else 'activo'
    db.session.commit()
    flash('Combo actualizado.', 'info')
    return redirect(url_for('admin.combos'))


@admin_bp.route('/combos/eliminar/<int:cid>', methods=['POST'])
@login_required
@require_admin
def eliminar_combo(cid):
    return _delete_or_block(Combo.query.get_or_404(cid), 'admin.combos', 'combo')


# ─── ZONAS ───────────────────────────────────────────────────────────────────
@admin_bp.route('/zonas')
@login_required
@require_admin
def zonas():
    items = DeliveryZone.query.join(Township).join(District).order_by(
        District.nombre, Township.nombre, DeliveryZone.nombre_zona
    ).all()
    return render_template('admin/zonas.html', zonas=items)


@admin_bp.route('/zonas/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_zona():
    corregimientos = Township.query.filter_by(estado='activo').all()
    if request.method == 'POST':
        try:
            z = DeliveryZone(
                id_corregimiento=int(request.form['id_corregimiento']),
                nombre_zona=request.form['nombre_zona'],
                descripcion=request.form.get('descripcion', ''),
                costo_delivery=Decimal(request.form['costo_delivery']),
                tiempo_estimado_min=int(request.form.get('tiempo_estimado_min', 30)),
            )
            db.session.add(z)
            db.session.commit()
            flash('Zona creada.', 'success')
            return redirect(url_for('admin.zonas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_zona.html', corregimientos=corregimientos)


@admin_bp.route('/zonas/editar/<int:zid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_zona(zid):
    zona = DeliveryZone.query.get_or_404(zid)
    corregimientos = Township.query.filter_by(estado='activo').all()
    if request.method == 'POST':
        try:
            zona.nombre_zona = request.form['nombre_zona']
            zona.costo_delivery = Decimal(request.form['costo_delivery'])
            zona.tiempo_estimado_min = int(request.form.get('tiempo_estimado_min', 30))
            zona.estado = request.form.get('estado', 'activa')
            db.session.commit()
            flash('Zona actualizada.', 'success')
            return redirect(url_for('admin.zonas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/editar_zona.html', zona=zona, corregimientos=corregimientos)


@admin_bp.route('/zonas/eliminar/<int:zid>', methods=['POST'])
@login_required
@require_admin
def eliminar_zona(zid):
    return _delete_or_block(DeliveryZone.query.get_or_404(zid), 'admin.zonas', 'zona')


# ─── PEDIDOS ─────────────────────────────────────────────────────────────────
@admin_bp.route('/pedidos')
@login_required
@require_admin
def pedidos():
    estado = request.args.get('estado', '')
    q = Order.query.order_by(Order.fecha_pedido.desc())
    if estado:
        q = q.filter_by(estado_actual=estado)
    items = q.limit(100).all()
    return render_template('admin/pedidos.html', pedidos=items, estado_filtro=estado)


@admin_bp.route('/pedidos/<int:pid>')
@login_required
@require_admin
def ver_pedido(pid):
    pedido = Order.query.get_or_404(pid)
    from app.models import OrderStatusHistory
    historial = OrderStatusHistory.query.filter_by(id_pedido=pid)\
                    .order_by(OrderStatusHistory.fecha_estado).all()
    drivers = Driver.query.filter_by(disponible=True).all()
    return render_template('admin/ver_pedido.html', pedido=pedido, historial=historial, drivers=drivers)


# ─── PAGOS ───────────────────────────────────────────────────────────────────
@admin_bp.route('/pagos')
@login_required
@require_admin
def pagos():
    items = Payment.query.order_by(Payment.fecha_pago.desc()).limit(100).all()
    return render_template('admin/pagos.html', pagos=items)


# ─── USUARIOS ────────────────────────────────────────────────────────────────
@admin_bp.route('/usuarios')
@login_required
@require_admin
def usuarios():
    items = User.query.order_by(User.id.desc()).all()
    roles = Role.query.all()
    return render_template('admin/usuarios.html', usuarios=items, roles=roles)


def _usuarios_por_rol(nombre_rol, titulo):
    rol = Role.query.filter_by(nombre=nombre_rol).first_or_404()
    items = User.query.filter_by(id_rol=rol.id).order_by(User.id.desc()).all()
    return render_template('admin/usuarios.html', usuarios=items, roles=Role.query.all(), titulo=titulo)


@admin_bp.route('/clientes')
@login_required
@require_admin
def clientes():
    return _usuarios_por_rol('Cliente', 'Clientes')


@admin_bp.route('/repartidores')
@login_required
@require_admin
def repartidores():
    return _usuarios_por_rol('Repartidor', 'Repartidores')


@admin_bp.route('/cocina-personal')
@login_required
@require_admin
def cocina_personal():
    return _usuarios_por_rol('Operario/Cocina', 'Personal de cocina')


@admin_bp.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
@require_admin
def crear_usuario():
    roles = Role.query.all()
    zonas = DeliveryZone.query.filter_by(estado='activa').all()
    if request.method == 'POST':
        try:
            u = User(
                id_rol=int(request.form['id_rol']),
                nombre=request.form['nombre'],
                correo=request.form.get('correo', ''),
                telefono=request.form.get('telefono', ''),
                direccion=request.form.get('direccion', ''),
                id_zona_preferida=int(request.form['id_zona_preferida']) if request.form.get('id_zona_preferida') else None,
                usuario=request.form['usuario'],
            )
            if len(request.form['password']) < 6:
                raise ValueError('La contrasena debe tener minimo 6 caracteres.')
            u.set_password(request.form['password'])
            _validate_unique_user(u)
            db.session.add(u)
            db.session.flush()
            _sync_staff_profile(u)
            db.session.commit()
            flash('Usuario creado.', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    return render_template('admin/crear_usuario.html', roles=roles, zonas=zonas)


@admin_bp.route('/usuarios/editar/<int:uid>', methods=['GET', 'POST'])
@login_required
@require_admin
def editar_usuario(uid):
    user = User.query.get_or_404(uid)
    roles = Role.query.all()
    zonas = DeliveryZone.query.filter_by(estado='activa').all()
    if request.method == 'POST':
        try:
            old_is_admin = user.is_admin()
            user.id_rol = int(request.form['id_rol'])
            user.nombre = request.form['nombre']
            user.correo = request.form.get('correo', '')
            user.telefono = request.form.get('telefono', '')
            user.direccion = request.form.get('direccion', '')
            user.id_zona_preferida = int(request.form['id_zona_preferida']) if request.form.get('id_zona_preferida') else None
            user.usuario = request.form['usuario']
            user.estado = request.form.get('estado', 'activo')
            if old_is_admin and not user.is_admin() and _admin_count() <= 1:
                raise ValueError('No puedes quitar el ultimo administrador activo.')
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')
            if password or password_confirm:
                if password != password_confirm:
                    raise ValueError('La nueva contrasena y su confirmacion no coinciden.')
                if len(password) < 6:
                    raise ValueError('La contrasena debe tener minimo 6 caracteres.')
                user.set_password(password)
            _validate_unique_user(user)
            _sync_staff_profile(user)
            db.session.commit()
            flash('Usuario actualizado.', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
    driver = None
    if user.empleado_ref:
        driver = user.empleado_ref.repartidor
    return render_template('admin/editar_usuario.html', usuario=user, roles=roles,
                           zonas=zonas, driver=driver)


@admin_bp.route('/usuarios/toggle/<int:uid>', methods=['POST'])
@login_required
@require_admin
def toggle_usuario(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'warning')
        return redirect(url_for('admin.usuarios'))
    if user.is_admin() and user.estado == 'activo' and _admin_count() <= 1:
        flash('No puedes desactivar el ultimo administrador activo.', 'danger')
        return redirect(url_for('admin.usuarios'))
    user.estado = 'inactivo' if user.estado == 'activo' else 'activo'
    db.session.commit()
    flash('Usuario actualizado.', 'info')
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuarios/eliminar/<int:uid>', methods=['POST'])
@login_required
@require_admin
def eliminar_usuario(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'warning')
        return redirect(url_for('admin.usuarios'))
    if user.is_admin() and _admin_count() <= 1:
        flash('No puedes eliminar el ultimo administrador activo.', 'danger')
        return redirect(url_for('admin.usuarios'))
    return _delete_or_block(user, 'admin.usuarios', 'usuario')


@admin_bp.route('/repartidores/solicitudes', methods=['GET', 'POST'])
@login_required
@require_admin
def solicitudes_zona():
    if request.method == 'POST':
        solicitud = ZoneChangeRequest.query.get_or_404(int(request.form['solicitud_id']))
        accion = request.form.get('accion')
        solicitud.estado = 'aprobada' if accion == 'aprobar' else 'rechazada'
        solicitud.respuesta_admin = request.form.get('respuesta_admin', '')
        solicitud.fecha_respuesta = datetime.utcnow()
        solicitud.id_admin_responde = current_user.id
        if solicitud.estado == 'aprobada':
            solicitud.repartidor.id_zona_actual = solicitud.id_zona_nueva
        db.session.commit()
        flash('Solicitud procesada.', 'success')
        return redirect(url_for('admin.solicitudes_zona'))
    solicitudes = ZoneChangeRequest.query.order_by(
        ZoneChangeRequest.fecha_solicitud.desc()
    ).limit(100).all()
    return render_template('admin/solicitudes_zona.html', solicitudes=solicitudes)


# ─── OUTBOX / CORREOS ────────────────────────────────────────────────────────
@admin_bp.route('/outbox')
@login_required
@require_admin
def outbox():
    correos = OutboxEmail.query.order_by(OutboxEmail.fecha_generado.desc()).limit(100).all()
    jsons = JsonLog.query.order_by(JsonLog.fecha_creacion.desc()).limit(50).all()
    return render_template('admin/outbox.html', correos=correos, jsons=jsons)


@admin_bp.route('/correos')
@login_required
@require_admin
def correos():
    correos = OutboxEmail.query.order_by(OutboxEmail.fecha_generado.desc()).limit(150).all()
    pendientes = OutboxEmail.query.filter(OutboxEmail.estado_envio.in_(['pendiente', 'fallido'])).count()
    return render_template('admin/correos.html',
                           estado=smtp_status(), correos=correos, pendientes=pendientes)


@admin_bp.route('/correos/prueba', methods=['POST'])
@login_required
@require_admin
def correo_prueba():
    destinatario = request.form.get('destinatario') or None
    result = send_test_email(destinatario)
    if result['ok']:
        flash('Correo de prueba enviado por SMTP real.', 'success')
    else:
        flash(f'Error SMTP: {result["error"]}', 'danger')
    return redirect(url_for('admin.correos'))


@admin_bp.route('/correos/reintentar/<int:correo_id>', methods=['POST'])
@login_required
@require_admin
def reintentar_correo(correo_id):
    correo = OutboxEmail.query.get_or_404(correo_id)
    result = retry_email(correo)
    if result['ok']:
        flash('Correo reenviado correctamente.', 'success')
    else:
        flash(f'No se pudo reenviar: {result["error"]}', 'danger')
    return redirect(url_for('admin.correos'))


# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────
@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@require_admin
def configuracion():
    claves = [
        'nombre_empresa', 'yappy_numero', 'correo_empresa', 'correo_operario',
        'min_ingredientes', 'max_ingredientes', 'porcentaje_comision', 'impuesto',
        'modo_offline', 'mail_server', 'mail_port', 'mail_use_tls', 'mail_username',
        'mail_default_sender', 'costo_base_delivery', 'color_primario', 'home_titulo',
    ]
    if request.method == 'POST':
        try:
            min_ing = max(1, int(request.form.get('min_ingredientes', '2') or 2))
            max_ing = max(min_ing, int(request.form.get('max_ingredientes', '10') or 10))
            for clave in claves:
                if clave == 'min_ingredientes':
                    valor = min_ing
                elif clave == 'max_ingredientes':
                    valor = max_ing
                else:
                    valor = request.form.get(clave, '')
                SystemConfig.set(clave, valor)
            flash('Configuración guardada.', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'danger')

    config_items = {c.clave: c.valor for c in SystemConfig.query.all()}
    return render_template('admin/configuracion.html',
                           config=config_items, claves=claves)


# ─── CHATBOT ─────────────────────────────────────────────────────────────────
@admin_bp.route('/chatbot')
@login_required
@require_admin
def chatbot():
    respuestas = ChatbotResponse.query.order_by(ChatbotResponse.categoria).all()
    return render_template('admin/chatbot.html', respuestas=respuestas)


@admin_bp.route('/chatbot/crear', methods=['POST'])
@login_required
@require_admin
def crear_respuesta_chatbot():
    try:
        r = ChatbotResponse(
            pregunta_clave=request.form['pregunta_clave'],
            respuesta=request.form['respuesta'],
            categoria=request.form.get('categoria', 'general'),
        )
        db.session.add(r)
        db.session.commit()
        flash('Respuesta creada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin.chatbot'))


@admin_bp.route('/pagos/<int:pago_id>/confirmar', methods=['POST'])
@login_required
@require_admin
def confirmar_pago(pago_id):
    pago = Payment.query.get_or_404(pago_id)
    try:
        pago.estado = 'pagado'
        db.session.add(OrderStatusHistory(
            id_pedido=pago.id_pedido,
            estado='pago_confirmado',
            descripcion='Pago confirmado por administrador.',
            actualizado_por=current_user.id,
        ))
        db.session.commit()
        flash('Pago confirmado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error confirmando pago: {e}', 'danger')
    return redirect(url_for('admin.pagos'))


@admin_bp.route('/pedidos/<int:pid>/asignar-repartidor', methods=['POST'])
@login_required
@require_admin
def asignar_repartidor(pid):
    pedido = Order.query.get_or_404(pid)
    driver_id = request.form.get('driver_id')
    try:
        if not pedido.metodo_entrega or pedido.metodo_entrega.nombre != 'delivery':
            flash('Los pedidos de retiro en local no requieren repartidor.', 'warning')
            return redirect(url_for('admin.ver_pedido', pid=pid))
        if pedido.estado_actual != 'listo':
            flash('Solo se puede asignar repartidor cuando cocina marco el pedido como listo.', 'warning')
            return redirect(url_for('admin.ver_pedido', pid=pid))
        pago_pagado = pedido.pagos.filter_by(estado='pagado').first()
        pago_efectivo = pedido.pagos.filter_by(metodo='efectivo').first()
        if not pago_pagado and not pago_efectivo:
            flash('No se puede asignar repartidor sin pago confirmado, salvo efectivo.', 'warning')
            return redirect(url_for('admin.ver_pedido', pid=pid))
        if pedido.asignacion:
            flash('Este pedido ya tiene repartidor asignado.', 'info')
            return redirect(url_for('admin.ver_pedido', pid=pid))
        driver = Driver.query.get_or_404(int(driver_id))
        pct = float(driver.porcentaje_comision)
        calc = calcular_delivery(float(pedido.monto_delivery), pct)
        asig = DeliveryAssignment(
            id_pedido=pedido.id,
            id_repartidor=driver.id,
            monto_flete=pedido.monto_delivery,
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
            descripcion=f'Repartidor asignado: {driver.empleado.usuario.nombre}',
            actualizado_por=current_user.id,
        ))
        db.session.commit()
        flash('Repartidor asignado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error asignando repartidor: {e}', 'danger')
    return redirect(url_for('admin.ver_pedido', pid=pid))


@admin_bp.route('/pedidos/<int:pid>/cancelar', methods=['POST'])
@login_required
@require_admin
def cancelar_pedido_admin(pid):
    pedido = Order.query.get_or_404(pid)
    motivo = request.form.get('motivo', 'Cancelado por administrador')
    try:
        pagado = pedido.pagos.filter_by(estado='pagado').first() is not None
        pedido.estado_actual = 'cancelado'
        pedido.motivo_cancelacion = motivo
        pedido.cancelado_por = current_user.id
        from datetime import datetime
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
            id_usuario=pedido.id_cliente,
            titulo='Pedido cancelado',
            mensaje=f'Tu pedido {pedido.numero} fue cancelado. Motivo: {motivo}',
            tipo='pedido',
        ))
        db.session.commit()
        simular_correo_cancelacion(pedido, motivo, reembolso=pagado)
        flash('Pedido cancelado por administrador.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelando pedido: {e}', 'danger')
    return redirect(url_for('admin.ver_pedido', pid=pid))


@admin_bp.route('/json')
@login_required
@require_admin
def json_viewer():
    tipo = request.args.get('tipo', '')
    pedido = request.args.get('pedido', '')
    selected_id = request.args.get('json_id', type=int)
    q = JsonLog.query.order_by(JsonLog.fecha_creacion.desc())
    if tipo:
        q = q.filter(JsonLog.tipo_json.contains(tipo))
    if pedido:
        try:
            q = q.filter_by(id_pedido=int(pedido))
        except ValueError:
            flash('El filtro de pedido debe ser numerico.', 'warning')
    jsons = q.limit(200).all()
    selected = None
    pretty_json = ''
    if jsons:
        selected = next((item for item in jsons if item.id == selected_id), jsons[0])
        try:
            pretty_json = json.dumps(json.loads(selected.contenido_json), ensure_ascii=False, indent=2)
        except Exception:
            pretty_json = selected.contenido_json
    return render_template(
        'admin/json_viewer.html',
        jsons=jsons,
        selected=selected,
        pretty_json=pretty_json,
        tipo=tipo,
        pedido=pedido,
    )


@admin_bp.route('/json/descargar/<path:filename>')
@login_required
@require_admin
def descargar_json(filename):
    return send_from_directory(current_app.config['OUTBOX_FOLDER'], filename, as_attachment=True)
