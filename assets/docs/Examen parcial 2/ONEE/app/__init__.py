import os
from flask import Flask, render_template
from config import config
from app.extensions import db, login_manager, csrf


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        if app.debug:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    @app.context_processor
    def utility_processor():
        from flask import url_for
        from app.utils.file_uploads import static_image_url

        def img_url(path, placeholder='img/branding/logo.png'):
            normalized = static_image_url(path) or placeholder
            return url_for('static', filename=normalized)

        return dict(img_url=img_url)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Blueprints
    from app.routes.public     import public_bp
    from app.routes.auth       import auth_bp
    from app.routes.cliente    import cliente_bp
    from app.routes.admin      import admin_bp
    from app.routes.cocina     import cocina_bp
    from app.routes.repartidor import repartidor_bp
    from app.routes.chatbot    import chatbot_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cocina_bp)
    app.register_blueprint(repartidor_bp)
    app.register_blueprint(chatbot_bp)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Create tables and seed on first run
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        _ensure_sqlite_parent(app)
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), exist_ok=True)
        os.makedirs(os.path.join(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'payments'), exist_ok=True)
        os.makedirs(os.path.join(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'profiles'), exist_ok=True)
        os.makedirs(os.path.join(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'catalog'), exist_ok=True)
        for folder in (
            'img/pizzas/destacadas', 'img/pizzas/combos', 'img/menu/refrescos',
            'img/menu/adicionales', 'img/pizza/masas', 'img/pizza/salsas',
            'img/pizza/ingredientes',
        ):
            os.makedirs(os.path.join(app.root_path, 'static', *folder.split('/')), exist_ok=True)
        os.makedirs(app.config.get('OUTBOX_FOLDER', 'outbox'), exist_ok=True)
        db.create_all()
        _ensure_runtime_columns()
        _auto_seed()

    return app


def _ensure_sqlite_parent(app):
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    prefix = 'sqlite:///'
    if not db_uri.startswith(prefix):
        return
    db_path = db_uri[len(prefix):]
    if not db_path or db_path == ':memory:':
        return
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.instance_path, db_path)
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _auto_seed():
    from app.models import Role
    try:
        if Role.query.count() == 0:
            from app.seed import seed_all
            seed_all()
    except Exception as e:
        print(f"Seed error: {e}")


def _ensure_runtime_columns():
    from sqlalchemy import text
    required = {
        'correos_outbox': {
            'estado_envio': "ALTER TABLE correos_outbox ADD COLUMN estado_envio VARCHAR(20) DEFAULT 'pendiente'",
            'error_envio': "ALTER TABLE correos_outbox ADD COLUMN error_envio TEXT",
            'fecha_envio': "ALTER TABLE correos_outbox ADD COLUMN fecha_envio DATETIME",
            'cuerpo': "ALTER TABLE correos_outbox ADD COLUMN cuerpo TEXT",
        }
    }
    try:
        for table, columns in required.items():
            existing = {row[1] for row in db.session.execute(text(f'PRAGMA table_info({table})')).fetchall()}
            for column, ddl in columns.items():
                if column not in existing:
                    db.session.execute(text(ddl))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f"Schema compatibility error: {exc}")
