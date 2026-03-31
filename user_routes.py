from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import mysql.connector
import bcrypt
import string
import secrets
from config import Config

users_bp = Blueprint('users', __name__)

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + '@#$%&*'
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_password(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def get_auth_connection():
    return mysql.connector.connect(**Config.AUTH_DB_CONFIG)

@users_bp.route('/list', methods=['GET'])
@login_required
def get_users():
    if current_user.privilege != 'administrador' and current_user.name_business != 'Camet':
        return jsonify({'error': 'No autorizado'}), 403

    try:
        conn = get_auth_connection()
        cursor = conn.cursor(dictionary=True)
        
        # El superusuario Camet ve todos o su empresa? 
        # "El usuario que accede bajo el nombre de la empresa Camet, tiene todos los privilegios."
        # Lo haremos que vea a todos por si acaso, o podemos restringir a Camet si queremos ser conservadores,
        # pero para el caso comun un administrador solo ve los de su empresa.
        if current_user.name_business == 'Camet':
            query = "SELECT user_id, username, privilege, name_business FROM usuarios ORDER BY name_business, username"
            cursor.execute(query)
        else:
            query = "SELECT user_id, username, privilege, name_business FROM usuarios WHERE name_business = %s ORDER BY username"
            cursor.execute(query, (current_user.name_business,))
            
        users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@users_bp.route('/add', methods=['POST'])
@login_required
def add_user():
    if current_user.privilege != 'administrador' and current_user.name_business != 'Camet':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.json
    username = data.get('username')
    
    # Solo Camet puede elegir privilegio, el resto crea siempre como 'cliente'
    if current_user.name_business != 'Camet':
        privilege = 'cliente'
    else:
        privilege = data.get('privilege', 'cliente')

    # Default al negocio del admin actual
    name_business = current_user.name_business
    
    password = data.get('password')
    auto_generated = False
    if not password:
        password = generate_random_password()
        auto_generated = True

    try:
        conn = get_auth_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        query = """
            INSERT INTO usuarios (username, password, privilege, name_business)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (username, password_hash, privilege, name_business))
        conn.commit()
        
        return jsonify({
            'message': 'Usuario creado con éxito',
            'username': username,
            'password': password if auto_generated else None,
            'auto_generated': auto_generated
        }), 201
    except mysql.connector.IntegrityError:
        return jsonify({'error': f'El usuario "{username}" ya existe.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@users_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.privilege != 'administrador' and current_user.name_business != 'Camet':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.json
    new_username = data.get('username')
    new_password = data.get('password')

    try:
        conn = get_auth_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Primero verificar que el usuario pertenece a la misma empresa (o es Camet)
        cursor.execute("SELECT name_business FROM usuarios WHERE user_id = %s", (user_id,))
        user_to_edit = cursor.fetchone()
        
        if not user_to_edit:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        if current_user.name_business != 'Camet' and user_to_edit['name_business'] != current_user.name_business:
            return jsonify({'error': 'No puedes editar usuarios de otras empresas'}), 403

        updates = []
        params = []
        
        if new_username:
            updates.append("username = %s")
            params.append(new_username)
            
        hashed_pw = None
        if new_password:
            hashed_pw = hash_password(new_password)
            updates.append("password = %s")
            params.append(hashed_pw)
            
        if not updates:
            return jsonify({'message': 'No hay datos para actualizar'}), 200
            
        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE user_id = %s"
        params.append(user_id)
        
        cursor.execute(query, tuple(params))
        conn.commit()
        
        return jsonify({
            'message': 'Usuario modificado con éxito',
            'password_changed': bool(new_password)
        }), 200
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'El nombre de usuario ya está en uso'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.privilege != 'administrador' and current_user.name_business != 'Camet':
        return jsonify({'error': 'No autorizado'}), 403

    try:
        conn = get_auth_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar empresa
        cursor.execute("SELECT name_business FROM usuarios WHERE user_id = %s", (user_id,))
        user_to_delete = cursor.fetchone()
        
        if not user_to_delete:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        if current_user.name_business != 'Camet' and user_to_delete['name_business'] != current_user.name_business:
            return jsonify({'error': 'No puedes eliminar usuarios de otras empresas'}), 403
            
        # No permitir borrar a uno mismo (?) Aunque no lo pide explícitamente, es buena práctica
        if str(user_id) == str(current_user.id):
            return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400

        cursor.execute("DELETE FROM usuarios WHERE user_id = %s", (user_id,))
        conn.commit()
        
        return jsonify({'message': 'Usuario eliminado con éxito'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
