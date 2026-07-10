from flask import Blueprint, render_template
from app.models import Pizza, Combo, SystemConfig

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    try:
        pizzas_destacadas = Pizza.query.filter_by(estado='activa').limit(6).all()
        combos_destacados = Combo.query.filter_by(estado='activo').limit(4).all()
        config = {
            'nombre_empresa': SystemConfig.get('nombre_empresa', 'CHINOS CAFÉ S.A.'),
            'yappy_numero': SystemConfig.get('yappy_numero', '6000-0000'),
        }
    except Exception:
        pizzas_destacadas = []
        combos_destacados = []
        config = {'nombre_empresa': 'CHINOS CAFÉ S.A.', 'yappy_numero': '6000-0000'}

    return render_template('public/index.html',
                           pizzas=pizzas_destacadas,
                           combos=combos_destacados,
                           config=config)


@public_bp.route('/menu')
def menu():
    try:
        pizzas = Pizza.query.filter_by(estado='activa').all()
        combos = Combo.query.filter_by(estado='activo').all()
    except Exception:
        pizzas, combos = [], []
    return render_template('public/menu.html', pizzas=pizzas, combos=combos)
