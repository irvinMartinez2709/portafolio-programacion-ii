import os
from uuid import uuid4
from flask import current_app
from werkzeug.utils import secure_filename


PAYMENT_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
CATALOG_IMAGE_FOLDERS = {
    'pizza': 'img/pizzas/destacadas',
    'combo': 'img/pizzas/combos',
    'refresco': 'img/menu/refrescos',
    'adicional': 'img/menu/adicionales',
    'masa': 'img/pizza/masas',
    'salsa': 'img/pizza/salsas',
    'ingrediente': 'img/pizza/ingredientes',
}


def allowed_payment_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PAYMENT_EXTENSIONS


def save_payment_receipt(file_storage, pedido_id):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_payment_file(file_storage.filename):
        raise ValueError('Formato no permitido. Usa PNG, JPG, JPEG o PDF.')

    original = secure_filename(file_storage.filename)
    ext = original.rsplit('.', 1)[1].lower()
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'payments')
    os.makedirs(folder, exist_ok=True)
    filename = f'pedido_{pedido_id}_{uuid4().hex}.{ext}'
    file_storage.save(os.path.join(folder, filename))
    return f'payments/{filename}'


def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS


def save_image_upload(file_storage, subfolder, prefix):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image_file(file_storage.filename):
        raise ValueError('Formato no permitido. Usa PNG, JPG, JPEG o WEBP.')
    original = secure_filename(file_storage.filename)
    ext = original.rsplit('.', 1)[1].lower()
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder, exist_ok=True)
    filename = f'{secure_filename(prefix)}_{uuid4().hex}.{ext}'
    file_storage.save(os.path.join(folder, filename))
    return f'{subfolder}/{filename}'


def save_catalog_image(file_storage, item_type, prefix):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image_file(file_storage.filename):
        raise ValueError('Formato no permitido. Usa PNG, JPG, JPEG o WEBP.')
    relative_folder = CATALOG_IMAGE_FOLDERS[item_type]
    original = secure_filename(file_storage.filename)
    ext = original.rsplit('.', 1)[1].lower()
    folder = os.path.join(current_app.root_path, 'static', *relative_folder.split('/'))
    os.makedirs(folder, exist_ok=True)
    filename = f'{secure_filename(prefix)}_{uuid4().hex}.{ext}'
    file_storage.save(os.path.join(folder, filename))
    return f'{relative_folder}/{filename}'


def static_image_url(path):
    if not path:
        return None
    normalized = path.replace('\\', '/').lstrip('/')
    if '/' not in normalized and normalized in ('pizza_default.png', 'combo_default.png', 'default.png'):
        return None
    if normalized.startswith('static/'):
        normalized = normalized[len('static/'):]
    if normalized.startswith('uploads/'):
        normalized = normalized[len('uploads/'):]
    return normalized
