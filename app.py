from flask import Flask, request
from database import conectar_bd
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import jsonify
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
# Configurar llave secreta
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("NO SE ENCONTRO LA LLAVE JWT")
jwt = JWTManager(app)
CORS(app)

def rol_requerido(rol):
    def decorador(funcion):
        @wraps(funcion)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("rol") != rol:
                return jsonify({
                    "mensaje": "No tienes permisos para acceder"
                }), 403
            return funcion(*args, **kwargs)
        return wrapper
    return decorador

@app.route("/")
def inicio():
    return "Api hoja de vida funcionando"

@app.route("/probar")
def probar_data():
    conec = conectar_bd()
    if conec and conec.is_connected():
        conec.close()
        return {"mensaje": "Conexion ok"}
    return {"mensaje": "Error de conexión"}, 500

# ________________________________________________ HOJA DE VIDA
# ____ Autenticacion de usuarios 

@app.route("/api/registro-usuario", methods=["POST"])
def registro_usuario():
    datos = request.get_json()

    if not datos or not datos.get("correo") or not datos.get("password") or not datos.get("nombre"):
        return {"mensaje": "Los campos no pueden estar vacios"}, 400
    
    nombre = datos["nombre"]
    correo = datos["correo"].strip()
    password = datos["password"]

    if not (8 <= len(password) <= 15):
        return {"mensaje": "La contraseña debe tener 8 a 15 caracteres"}, 400

    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión con la base de datos"}, 500
        
    cursor = conec.cursor(dictionary=True)

    try:
        # Validar que el correo no este registrado 
        cursor.execute("SELECT * FROM USUARIOS WHERE correo = %s", (correo,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            return {"mensaje": "El correo electronico ya esta registrado"}, 400

        # Encriptar la contraseña
        password_hash = generate_password_hash(password)
        rol = datos.get("rol", "aprendiz")

        # Guardar en la base de datos
        sql = """INSERT INTO USUARIOS (nombre, correo, password, rol) VALUES (%s, %s, %s, 'aprendiz')"""
        cursor.execute(sql, (nombre, correo, password_hash))
        conec.commit()

        id_usuario = cursor.lastrowid

        return {
            "mensaje": "Cuenta de usuario creada con éxito",
            "id_usuario": id_usuario
        }, 201

    finally:
        cursor.close()
        conec.close()

@app.route("/api/login", methods=["POST"])
def login():
    datos = request.get_json()

    if not datos: 
        return jsonify({"mensaje": "Datos incompletos"}), 400

    correo = datos.get("correo", "").strip().lower()
    password = datos.get("password", "")

    if not correo or not password:
        return jsonify({"Mensaje": "Ingrese correo y contraseña"}), 400

    conec = conectar_bd()
    if not conec:
        return jsonify({"Mensaje": "Error de conexión con la base de datos"}), 500

    cursor = conec.cursor(dictionary=True)

    try: 
        sql = "SELECT id, nombre, correo, password, rol, estado FROM USUARIOS WHERE correo = %s"
        cursor.execute(sql, (correo,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"Mensaje": "Correo y/o contraseña incorrecta"}), 401

        if not usuario.get("estado", True):
            return jsonify({"Mensaje": "La cuenta está desactivada"}), 403

        if not check_password_hash(usuario["password"], password):
            return jsonify({"Mensaje": "Correo y/o contraseña incorrecta"}), 401

        token = create_access_token(
            identity=str(usuario["id"]),
            additional_claims={"rol": usuario["rol"]}
        )

        return jsonify({
            "Mensaje": "Inicio de sesión correcto",
            "token": token,
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "correo": usuario["correo"],
                "rol": usuario["rol"]
            }
        }), 200

    except Exception as e:
        return jsonify({"Mensaje": f"Ocurrió un error en el servidor: {str(e)}"}), 500

    finally:
        cursor.close()
        conec.close()

@app.route("/api/actualizarhv/<int:id>", methods=["PUT"])
def actualizar_hv(id):
    datos = request.get_json()
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
        
    cursor = conec.cursor(buffered=True)

    try:
        buscar = """SELECT id_HV FROM HOJAS_VIDA WHERE id_HV=%s"""
        cursor.execute(buscar, (id,))
        result = cursor.fetchone()

        if result is None:
            return {"mensaje": "No se encontro la hoja de vida"}, 404

        sql_correo = """SELECT id_HV FROM HOJAS_VIDA WHERE correo=%s AND id_HV!=%s"""
        cursor.execute(sql_correo, (datos["correo"], id))
        result = cursor.fetchone()
        if result is not None:
            return {"mensaje": "El correo ya está registrado con otra hoja de vida"}, 400

        sql_actualizar = """UPDATE HOJAS_VIDA SET nombre=%s, edad=%s, ciudad=%s, correo=%s, fotografia=%s, programa=%s, ficha=%s, jornada=%s WHERE id_HV=%s"""

        valores = (
            datos["nombre"],
            datos["edad"],
            datos["ciudad"],
            datos["correo"],
            datos.get("fotografia"),
            datos["programa"],
            datos["ficha"],
            datos["jornada"],
            id
        )

        cursor.execute(sql_actualizar, valores)
        conec.commit() 

        return {
            "Mensaje": "Hoja de vida actualizada",
            "id": id
        }, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminar_hv(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
        
    cursor = conec.cursor()

    try:
        buscar = "SELECT id_HV FROM HOJAS_VIDA WHERE id_HV =%s"
        cursor.execute(buscar, (id,))
        existe = cursor.fetchone()

        if existe is None:
            return {"mensaje": "No se encontro la hoja de vida"}, 404

        sql_eliminar = """DELETE FROM HOJAS_VIDA WHERE id_HV=%s"""
        cursor.execute(sql_eliminar, (id,))
        conec.commit()

        return {
            "mensaje": "Hoja de vida eliminada",
            "id": id
        }, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/consultahv/<int:id>", methods=["GET"])
def obtener_hvida(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
        
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT * FROM HOJAS_VIDA WHERE id_HV= %s"""
        cursor.execute(sql, (id,))
        datos = cursor.fetchone()

        if datos is None:
            return {"mensaje": "No se encontro la hoja de vida"}, 404

        return datos, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/registrohv", methods=["POST"])
@jwt_required()
def registrar_hojavida():
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
        
    cursor = conec.cursor()
    datos = request.get_json() 

    try:
        cursor.execute("SELECT * FROM HOJAS_VIDA WHERE correo = %s", (datos['correo'],))
        resultado = cursor.fetchone()

        if resultado:
            return {"mensaje": "El correo ya está registrado"}, 400

        sql = """INSERT INTO HOJAS_VIDA (nombre, edad, ciudad, correo, fotografia, programa, ficha, jornada,usuario_id) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)"""
                 
        cursor.execute(sql, (
            datos["nombre"],
            datos["edad"],
            datos["ciudad"],
            datos["correo"],
            datos.get("fotografia"),
            datos["programa"],
            datos["ficha"],
            datos["jornada"],
            datos["usuario_id"]
        ))

        conec.commit()
        id_generado = cursor.lastrowid

        return {"mensaje": "Hoja de vida creada", "id": id_generado}, 201
    finally:
        cursor.close()
        conec.close()

@app.route("/api/hojasdevida", methods=["GET"])
@rol_requerido('reclutador')
def obtener_todas_hojasdevida():
    conec = conectar_bd()
    if not conec:
        return jsonify({"error": "Error de conexión"}), 500
        
    cursor = conec.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM HOJAS_VIDA")
        hojasdevida = cursor.fetchall()
        return jsonify(hojasdevida), 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/hojasdevida/<int:id>", methods=["GET"])
@jwt_required()
def obtener_hojasvida_por_id(id):
    conec = conectar_bd()
    if not conec:
        return jsonify({"error": "Error de conexión"}), 500
        
    cursor = conec.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM HOJAS_VIDA WHERE id_HV = %s", (id,))
        hoja_vida = cursor.fetchone()

        if not hoja_vida:
            return jsonify({"error": "Hoja de vida no encontrada"}), 404

        return jsonify(hoja_vida), 200
    finally:
        cursor.close()
        conec.close()

# ________________________________________________ ESTUDIOS

@app.route("/api/HOJAS_VIDA/<int:id>/estudios", methods=["GET"])
@jwt_required()
def consultar_estudios(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT id_EST, id_HV, nivel, institucion, titulo, anio_graduacion FROM ESTUDIOS WHERE id_HV = %s"""
        cursor.execute(sql, (id,))
        estudios = cursor.fetchall()

        return {"hoja_de_vida_id": id, "estudios": estudios}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/estudios/<int:id>/estudios", methods=["POST"])
@jwt_required()
def registrar_estudio(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor() 
    datos = request.json

    try:
        nivel = datos.get("nivel")
        institucion = datos.get("institucion")
        titulo = datos.get("titulo")
        anio_graduacion = datos.get("anio_graduacion")

        sql = """INSERT INTO ESTUDIOS (nivel, institucion, titulo, anio_graduacion, id_HV)
            VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (nivel, institucion, titulo, anio_graduacion, id))

        conec.commit()
        id_estudio = cursor.lastrowid

        return {"mensaje": "Estudio registrado para la hoja de vida", "id_EST": id_estudio}, 201
    finally:
        cursor.close()
        conec.close()

@app.route("/api/estudios/<int:id>", methods=["GET"])
@jwt_required()
def consultar_estudio(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = "SELECT id_EST, nivel, institucion, titulo, anio_graduacion FROM ESTUDIOS WHERE id_EST = %s"
        cursor.execute(sql, (id,))
        estudio = cursor.fetchone()

        if estudio is None:
            return {"mensaje": "Estudio no encontrado"}, 404

        return estudio, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/estudios/<int:id>/estudios", methods=["PUT"])
@jwt_required()
def actualizar_estudio(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()
    datos = request.json

    try:
        sql = """UPDATE ESTUDIOS SET nivel = %s, institucion = %s, titulo = %s, anio_graduacion = %s WHERE id_EST = %s"""
        cursor.execute(sql, (datos.get("nivel"), datos.get("institucion"), datos.get("titulo"), datos.get("anio_graduacion"), id))

        conec.commit()
        return {"mensaje": "Estudio actualizado", "id_EST": id}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/estudios/<int:id>", methods=["DELETE"])
@jwt_required()
def eliminar_estudio(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()

    try:
        sql = "DELETE FROM ESTUDIOS WHERE id_EST = %s"
        cursor.execute(sql, (id,))
        conec.commit()

        return {"mensaje": "Estudio eliminado", "id_EST": id}, 200
    finally:
        cursor.close()
        conec.close()

# ________________________________________________ EXPERIENCIA LABORAL 

@app.route("/api/EXPERIENCIAS/<int:id>/EXPERIENCIAS", methods=["POST"])
@jwt_required()
def registrar_experiencia(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor() 
    datos = request.json

    try:
        sql = """INSERT INTO EXPERIENCIAS (empresa, cargo, tiempo, funciones, id_HV)
            VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (datos.get("empresa"), datos.get("cargo"), datos.get("tiempo"), datos.get("funciones"), id))

        conec.commit()
        id_experiencia = cursor.lastrowid

        return {"mensaje": "Experiencia registrada para la hoja de vida", "id_exp": id_experiencia}, 201
    finally:
        cursor.close()
        conec.close()

@app.route("/api/HOJAS_VIDA/<int:id>/EXPERIENCIAS", methods=["GET"])
@jwt_required()
def consultar_experienciashv(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT id_exp, id_HV, empresa, cargo, tiempo, funciones FROM EXPERIENCIAS WHERE id_HV = %s"""
        cursor.execute(sql, (id,))
        experiencias = cursor.fetchall()

        return {"hoja_de_vida_id": id, "experiencias": experiencias}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/EXPERIENCIAS/<int:id>", methods=["GET"])
@jwt_required()
def consultar_experiencia(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT * FROM EXPERIENCIAS WHERE id_exp = %s"""
        cursor.execute(sql, (id,))
        experiencia = cursor.fetchone()

        if experiencia is None:
            return {"mensaje": "Experiencia no encontrada"}, 404

        return experiencia, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/EXPERIENCIAS/<int:id_hv>/<int:id_exp>", methods=["PUT"])
@jwt_required()
def actualizar_experiencia(id_hv, id_exp):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()
    datos = request.json

    try:
        sql = """UPDATE EXPERIENCIAS SET empresa = %s, cargo = %s, tiempo = %s, funciones = %s WHERE id_exp = %s AND id_HV = %s"""
        cursor.execute(sql, (datos.get("empresa"), datos.get("cargo"), datos.get("tiempo"), datos.get("funciones"), id_exp, id_hv))

        conec.commit()
        return {"mensaje": "Experiencia actualizada", "id_exp": id_exp, "id_HV": id_hv}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/EXPERIENCIAS/<int:id_hv>/<int:id_exp>", methods=["DELETE"])
@jwt_required()
def eliminar_experiencia(id_hv, id_exp):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()

    try:
        sql = "DELETE FROM EXPERIENCIAS WHERE id_exp = %s AND id_HV = %s"
        cursor.execute(sql, (id_exp, id_hv))
        conec.commit()

        return {"mensaje": "Experiencia eliminada", "id_exp": id_exp, "id_HV": id_hv}, 200
    finally:
        cursor.close()
        conec.close()

# ________________________________________________ HABILIDADES 

@app.route("/api/HABILIDADES/<int:id_exp>", methods=["POST"])
@jwt_required()
def registrar_habilidad(id_exp):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor() 
    datos = request.json

    try:
        sql = """INSERT INTO HABILIDADES (id_exp, nombre) VALUES (%s, %s)"""
        cursor.execute(sql, (id_exp, datos.get("nombre")))

        conec.commit()
        id_habilidades = cursor.lastrowid

        return {"mensaje": "Habilidad registrada en la experiencia laboral", "id_habi": id_habilidades, "id_exp": id_exp}, 201
    finally:
        cursor.close()
        conec.close()

@app.route("/api/HABILIDADES/<int:id_exp>", methods=["GET"])
@jwt_required()
def consultar_habilidades(id_exp):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT id_habi, id_exp, nombre FROM HABILIDADES WHERE id_exp = %s"""
        cursor.execute(sql, (id_exp,))
        habilidades = cursor.fetchall()

        return {"habilidades": habilidades}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/HABILIDADES/<int:id_habi>", methods=["PUT"])
@jwt_required()
def actualizar_habilidad(id_habi):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()
    datos = request.json

    try:
        sql = """UPDATE HABILIDADES SET nombre = %s WHERE id_habi = %s"""
        cursor.execute(sql, (datos.get("nombre"), id_habi))

        conec.commit()
        return {"mensaje": "Habilidad actualizada", "id_habi": id_habi}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/HABILIDADES/<int:id_habi>", methods=["DELETE"])
@jwt_required()
def eliminar_habilidad(id_habi):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()

    try:
        sql = """DELETE FROM HABILIDADES WHERE id_habi = %s"""
        cursor.execute(sql, (id_habi,))
        conec.commit()

        return {"mensaje": "Habilidad Eliminada", "id_habi": id_habi}, 200
    finally:
        cursor.close()
        conec.close()

# ________________________________________________ CURSOS

@app.route("/api/CURSOS/<int:id_hv>", methods=["POST"])
@jwt_required()
def registrar_cursos(id_hv):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor() 
    datos = request.json

    try:
        sql = """INSERT INTO CURSOS (id_HV, nombre) VALUES (%s, %s)"""
        cursor.execute(sql, (id_hv, datos.get("nombre")))

        conec.commit()
        id_curso = cursor.lastrowid

        return {"mensaje": "Curso registrado en la hoja de vida", "id_CUR": id_curso, "id_hv": id_hv}, 201
    finally:
        cursor.close()
        conec.close()

@app.route("/api/HOJAS_VIDA/<int:id>/CURSOS", methods=["GET"])
@jwt_required()
def consultar_cursoshv(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT id_CUR, id_HV, nombre FROM CURSOS WHERE id_HV = %s"""
        cursor.execute(sql, (id,))
        cursos = cursor.fetchall()

        return {"hoja_de_vida_id": id, "CURSOS": cursos}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/CURSOS/<int:id>", methods=["GET"])
@jwt_required()
def consultar_curso(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql = """SELECT * FROM CURSOS WHERE id_CUR = %s"""
        cursor.execute(sql, (id,))
        curso = cursor.fetchone()

        if curso is None:
            return {"mensaje": "Curso no encontrado"}, 404

        return curso, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/CURSOS/<int:id_CUR>", methods=["PUT"])
def actualizar_curso(id_CUR):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()
    datos = request.json

    try:
        sql = """UPDATE CURSOS SET nombre = %s WHERE id_CUR = %s"""
        cursor.execute(sql, (datos.get("nombre"), id_CUR))

        conec.commit()
        return {"mensaje": "Curso actualizado", "id_CUR": id_CUR}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/CURSOS/<int:id_CUR>", methods=["DELETE"])
def eliminar_curso(id_CUR):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor()

    try:
        sql = """DELETE FROM CURSOS WHERE id_CUR = %s"""
        cursor.execute(sql, (id_CUR,))
        conec.commit()

        return {"mensaje": "Curso Eliminado", "id_CUR": id_CUR}, 200
    finally:
        cursor.close()
        conec.close()

@app.route("/api/HOJAS_VIDA/<int:id>", methods=["GET"])
def consultar_hoja_vida_completa(id):
    conec = conectar_bd()
    if not conec:
        return {"mensaje": "Error de conexión"}, 500
    cursor = conec.cursor(dictionary=True)

    try:
        sql_hv = """SELECT * FROM HOJAS_VIDA WHERE id_HV = %s"""
        cursor.execute(sql_hv, (id,))
        hoja_vida = cursor.fetchone()

        if hoja_vida is None:
            return {"mensaje": "Hoja de vida no encontrada"}, 404

        sql_estudios = """SELECT * FROM ESTUDIOS WHERE id_HV = %s"""
        cursor.execute(sql_estudios, (id,))
        estudios = cursor.fetchall()

        sql_experiencias = """SELECT * FROM EXPERIENCIAS WHERE id_HV = %s"""
        cursor.execute(sql_experiencias, (id,))
        experiencias = cursor.fetchall()

        sql_cursos = """SELECT * FROM CURSOS WHERE id_HV = %s"""
        cursor.execute(sql_cursos, (id,))
        cursos = cursor.fetchall()

        respuesta_completa = {
            "hoja_de_vida": hoja_vida,
            "estudios": estudios,
            "experiencias": experiencias,
            "cursos": cursos
        }

        return respuesta_completa, 200
    finally:
        cursor.close()
        conec.close()

if __name__ == "__main__":
    app.run(debug=True)