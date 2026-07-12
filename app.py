from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import random
import base64
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'web_project_secret_key_2024')

mongo_uri=os.getenv('MONGO_URI','mongodb+srv://brenda_profesional:legionboss31@proyectop1.7mxjnaa.mongodb.net/')
client = MongoClient(mongo_uri)
db = client.web_project_db

users_collection = db.users
courses_collection = db.courses
videos_collection = db.videos
images_collection = db.images
puzzles_collection = db.puzzles

def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('user_type') == 'admin'

def create_grid(size):
    grid = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(i * size + j)
        grid.append(row)
    return grid

def shuffle_puzzle(grid, size):
    shuffled = create_grid(size)
    for _ in range(100):
        temp = create_grid(size)
        flat = []
        for row in temp:
            flat.extend(row)
        random.shuffle(flat)
        for i in range(size):
            for j in range(size):
                temp[i][j] = flat[i * size + j]
        if temp != shuffled:
            shuffled = temp
    return shuffled

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if users_collection.find_one({'username': data['username']}):
        return jsonify({'error': 'El usuario ya existe'}), 400
    users_collection.insert_one({
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'user_type': data['user_type'],
        'activo': True,
        'created_at': datetime.now()
    })
    return jsonify({'message': 'Usuario creado con éxito'})

@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    user = users_collection.find_one({
        'username': data['username'],
        'user_type': data['user_type']
    })
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'error': 'Usuario o password incorrectos'}), 401
    session['user_id'] = str(user['_id'])
    session['username'] = user['username']
    session['user_type'] = user['user_type']
    if user['user_type'] == 'admin':
        return jsonify({'username': user['username'], 'user_type': user['user_type'], 'redirect': '/admin/home'})
    else:
        return jsonify({'username': user['username'], 'user_type': user['user_type'], 'redirect': '/user_home'})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada'})

@app.route('/user_home')
def user_home():
    if not is_logged_in():
        return redirect('/login')
    if is_admin():
        return redirect('/admin/home')
    return render_template('user_home.html', username=session.get('username'))

@app.route('/cursos')
def cursos():
    if not is_logged_in():
        return redirect('/login')
    if is_admin():
        return redirect('/admin/home')
    courses = list(courses_collection.find({'activo': True}))
    videos = list(videos_collection.find({'activo': True}))
    return render_template('cursos.html', courses=courses, videos=videos, username=session.get('username'))

@app.route('/rompecabezas')
def rompecabezas():
    if not is_logged_in():
        return redirect('/login')
    if is_admin():
        return redirect('/admin/home')
    images = list(images_collection.find({'activo': True}))
    return render_template('rompecabezas.html', images=images, username=session.get('username'))

@app.route('/explicacion')
def explicacion():
    if not is_logged_in():
        return redirect('/login')
    if is_admin():
        return redirect('/admin/home')
    contenido = "Esta plataforma es un sistema educativo interactivo con Flask y MongoDB."
    return render_template('explicacion.html', contenido=contenido, username=session.get('username'))

@app.route('/admin/home')
def admin_home():
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    return render_template('admin_home.html',
        usuarios_count=users_collection.count_documents({}),
        puzzles_count=puzzles_collection.count_documents({}),
        cursos_count=courses_collection.count_documents({}),
        videos_count=videos_collection.count_documents({}),
        images_count=images_collection.count_documents({}),
        username=session.get('username'))

@app.route('/admin/usuarios')
def admin_usuarios():
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    usuarios_list = []
    for usuario in users_collection.find():
        usuario_dict = dict(usuario)
        usuario_dict['_id_str'] = str(usuario['_id'])
        usuarios_list.append(usuario_dict)
    return render_template('admin_usuarios.html', usuarios=usuarios_list, username=session.get('username'))

@app.route('/admin/usuarios', methods=['POST'])
def create_usuario():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    data = request.json
    if users_collection.find_one({'username': data['username']}):
        return jsonify({'error': 'El usuario ya existe'}), 400
    users_collection.insert_one({
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'user_type': data['user_type'],
        'activo': True,
        'created_at': datetime.now()
    })
    return jsonify({'message': 'Usuario creado con éxito'})

@app.route('/admin/usuarios/<id>', methods=['DELETE'])
def delete_usuario(id):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    users_collection.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Usuario eliminado'})

@app.route('/admin/cursos')
def admin_cursos():
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    cursos = list(courses_collection.find())
    return render_template('admin_cursos.html', cursos=cursos, username=session.get('username'))

@app.route('/admin/cursos', methods=['POST'])
def create_curso():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    data = request.json
    courses_collection.insert_one({
        'titulo': data['titulo'],
        'descripcion': data['descripcion'],
        'contenido': data.get('contenido', ''),
        'infografia': data.get('infografia', ''),
        'esquema': data.get('esquema', ''),
        'activo': True,
        'created_at': datetime.now()
    })
    return jsonify({'message': 'Curso creado con éxito'})

@app.route('/admin/cursos/<id>', methods=['DELETE'])
def delete_curso(id):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    courses_collection.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Curso eliminado'})

@app.route('/admin/videos')
def admin_videos():
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    videos = list(videos_collection.find())
    return render_template('admin_videos.html', videos=videos, username=session.get('username'))

@app.route('/admin/videos', methods=['POST'])
def create_video():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    data = request.json
    videos_collection.insert_one({
        'titulo': data['titulo'],
        'url_embed': data['url_embed'],
        'descripcion': data.get('descripcion', ''),
        'activo': True,
        'created_at': datetime.now()
    })
    return jsonify({'message': 'Video creado con éxito'})

@app.route('/admin/videos/<id>', methods=['DELETE'])
def delete_video(id):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    videos_collection.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Video eliminado'})

@app.route('/admin/imagenes')
def admin_imagenes():
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    imagenes = list(images_collection.find())
    return render_template('admin_imagenes.html', imagenes=imagenes, username=session.get('username'))

@app.route('/admin/imagenes', methods=['POST'])
def create_imagen():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    data = request.json
    images_collection.insert_one({
        'nombre': data['nombre'],
        'descripcion': data.get('descripcion', ''),
        'imagen_base64': data['imagen_base64'],
        'activo': True,
        'created_at': datetime.now()
    })
    return jsonify({'message': 'Imagen creada con éxito'})

@app.route('/admin/imagenes/<id>', methods=['DELETE'])
def delete_imagen(id):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    images_collection.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Imagen eliminada'})

@app.route('/admin/rompecabezas')
def admin_rompecabezas():
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    rompecabezas = list(puzzles_collection.find())
    return render_template('admin_rompecabezas.html', rompecabezas=rompecabezas, username=session.get('username'))

@app.route('/admin/rompecabezas/<id>', methods=['DELETE'])
def delete_rompecabeza(id):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    puzzles_collection.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Rompecabeza eliminado'})

@app.route('/puzzle/new', methods=['POST'])
def new_puzzle():
    if not is_logged_in():
        return jsonify({'error': 'Debes estar logueado'}), 401
    data = request.json
    img = images_collection.find_one({'_id': ObjectId(data.get('image_id'))})
    if not img:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    puzzle_state = create_grid(data.get('grid_size', 3))
    shuffled_state = shuffle_puzzle(puzzle_state, data.get('grid_size', 3))
    puzzle = {
        'user_id': session['user_id'],
        'image_id': data.get('image_id'),
        'imagen_base64': img.get('imagen_base64', ''),
        'grid_size': data.get('grid_size', 3),
        'current_state': shuffled_state,
        'original_state': puzzle_state,
        'status': 'in_progress',
        'created_at': datetime.now()
    }
    result = puzzles_collection.insert_one(puzzle)
    return jsonify({
        'puzzle_id': str(result.inserted_id),
        'grid_size': puzzle['grid_size'],
        'current_state': shuffled_state,
        'imagen_base64': img.get('imagen_base64', '')
    })

@app.route('/puzzle/<id>/save', methods=['POST'])
def save_puzzle(id):
    if not is_logged_in():
        return jsonify({'error': 'Debes estar logueado'}), 401
    data = request.json
    puzzles_collection.update_one(
        {'_id': ObjectId(id), 'user_id': session['user_id']},
        {'$set': {'current_state': data['current_state']}}
    )
    return jsonify({'message': 'Progreso guardado'})

@app.route('/puzzle/<id>/load')
def load_puzzle(id):
    if not is_logged_in():
        return jsonify({'error': 'Debes estar logueado'}), 401
    puzzle = puzzles_collection.find_one({'_id': ObjectId(id), 'user_id': session['user_id']})
    if not puzzle:
        return jsonify({'error': 'Puzzle no encontrado'}), 404
    return jsonify({
        'puzzle_id': str(puzzle['_id']),
        'grid_size': puzzle['grid_size'],
        'current_state': puzzle['current_state']
    })

# ========== RUTAS DE EDITAR/ELIMINAR CORRECTAS ==========

@app.route('/admin/usuarios/editar/<user_id>')
def editar_usuario(user_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    user_id = user_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(user_id)
    except:
        return 'ID inválido', 400
    usuario = users_collection.find_one({'_id': obj_id})
    if not usuario:
        return 'Usuario no encontrado', 404
    return render_template('editar_usuario.html', usuario=usuario, username=session.get('username'))

@app.route('/admin/usuarios/editar/<user_id>', methods=['POST'])
def guardar_editar_usuario(user_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    user_id = user_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(user_id)
    except:
        return 'ID inválido', 400
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['user_type']
    activo = request.form.get('activo') == 'true'
    users_collection.update_one(
        {'_id': obj_id},
        {'$set': {
            'username': username,
            'password': generate_password_hash(password),
            'user_type': user_type,
            'activo': activo
        }}
    )
    return redirect('/admin/usuarios')

@app.route('/admin/usuarios/eliminar/<user_id>')
def eliminar_usuario(user_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    user_id = user_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(user_id)
    except:
        return 'ID inválido', 400
    users_collection.delete_one({'_id': obj_id})
    return redirect('/admin/usuarios')

@app.route('/admin/cursos/editar/<curso_id>')
def editar_curso(curso_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    curso_id = curso_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(curso_id)
    except:
        return 'ID inválido', 400
    curso = courses_collection.find_one({'_id': obj_id})
    if not curso:
        return 'Curso no encontrado', 404
    return render_template('editar_curso.html', curso=curso, username=session.get('username'))

@app.route('/admin/cursos/editar/<curso_id>', methods=['POST'])
def guardar_editar_curso(curso_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    curso_id = curso_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(curso_id)
    except:
        return 'ID inválido', 400
    courses_collection.update_one(
        {'_id': obj_id},
        {'$set': {
            'titulo': request.form['titulo'],
            'descripcion': request.form['descripcion'],
            'contenido': request.form.get('contenido', ''),
            'infografia': request.form.get('infografia', ''),
            'esquema': request.form.get('esquema', ''),
            'activo': request.form.get('activo') == 'true'
        }}
    )
    return redirect('/admin/cursos')

@app.route('/admin/cursos/eliminar/<curso_id>')
def eliminar_curso(curso_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    curso_id = curso_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(curso_id)
    except:
        return 'ID inválido', 400
    courses_collection.delete_one({'_id': obj_id})
    return redirect('/admin/cursos')

@app.route('/admin/videos/editar/<video_id>')
def editar_video(video_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    video_id = video_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(video_id)
    except:
        return 'ID inválido', 400
    video = videos_collection.find_one({'_id': obj_id})
    if not video:
        return 'Video no encontrado', 404
    return render_template('editar_video.html', video=video, username=session.get('username'))

@app.route('/admin/videos/editar/<video_id>', methods=['POST'])
def guardar_editar_video(video_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    video_id = video_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(video_id)
    except:
        return 'ID inválido', 400
    videos_collection.update_one(
        {'_id': obj_id},
        {'$set': {
            'titulo': request.form['titulo'],
            'url_embed': request.form['url_embed'],
            'descripcion': request.form.get('descripcion', ''),
            'activo': request.form.get('activo') == 'true'
        }}
    )
    return redirect('/admin/videos')

@app.route('/admin/videos/eliminar/<video_id>')
def eliminar_video(video_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    video_id = video_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(video_id)
    except:
        return 'ID inválido', 400
    videos_collection.delete_one({'_id': obj_id})
    return redirect('/admin/videos')

@app.route('/admin/imagenes/editar/<imagen_id>')
def editar_imagen(imagen_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    imagen_id = imagen_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(imagen_id)
    except:
        return 'ID inválido', 400
    imagen = images_collection.find_one({'_id': obj_id})
    if not imagen:
        return 'Imagen no encontrada', 404
    return render_template('editar_imagen.html', imagen=imagen, username=session.get('username'))

@app.route('/admin/imagenes/editar/<imagen_id>', methods=['POST'])
def guardar_editar_imagen(imagen_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    imagen_id = imagen_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(imagen_id)
    except:
        return 'ID inválido', 400
    images_collection.update_one(
        {'_id': obj_id},
        {'$set': {
            'nombre': request.form['nombre'],
            'descripcion': request.form.get('descripcion', ''),
            'activo': request.form.get('activo') == 'true'
        }}
    )
    return redirect('/admin/imagenes')

@app.route('/admin/imagenes/eliminar/<imagen_id>')
def eliminar_imagen(imagen_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    imagen_id = imagen_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(imagen_id)
    except:
        return 'ID inválido', 400
    images_collection.delete_one({'_id': obj_id})
    return redirect('/admin/imagenes')

@app.route('/admin/rompecabezas/eliminar/<puzzle_id>')
def eliminar_puzzle(puzzle_id):
    if not is_logged_in() or not is_admin():
        return redirect('/login')
    puzzle_id = puzzle_id.strip().replace(' ', '')
    try:
        obj_id = ObjectId(puzzle_id)
    except:
        return 'ID inválido', 400
    puzzles_collection.delete_one({'_id': obj_id})
    return redirect('/admin/rompecabezas')

if __name__ == '__main__':
    app.run(debug=True)
