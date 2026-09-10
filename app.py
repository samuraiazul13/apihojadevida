from flask import Flask, request
from database import conectar_bd
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

@app.route("/probar")
def probar_data():
    conec = conectar_bd()
    if conec.is_connected(): 
        conec.close()
    return {"mensaje": "Conexion ok"}

#________________________________________________ HOJA DE VIDA

#ACTUALIZAR HV DE VIDA POR MEDIO DE ID 

@app.route("/api/actualizarhv/<int:id>",methods=["PUT"])
def actualizar_hv(id):

    #recibir los datos enviados

    datos = request.get_json()

    conec = conectar_bd()
    cursor=conec.cursor(buffered=True)

    buscar = """SELECT id_HV FROM HOJAS_VIDA WHERE id_HV=%s"""
    cursor.execute(buscar,(id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conec.close()
        return {"mensaje":"No se encontro la hoja de vida"}

    #verificar que el correo electronico no este asociado a otra hoja de vida

    sql_correo = """SELECT id_HV FROM HOJAS_VIDA WHERE correo=%s AND id_HV!=%s"""
    cursor.execute(sql_correo,(datos["correo"], id))
    result = cursor.fetchone()
    if result is not None:

        cursor.close()
        conec.close()

        return {"mensaje":"El correo ya está registrado con otra hoja de vida"}

    #ACTUALIZAR HOJAS DE VIDA

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
    cursor.close()
    conec.close()

    return{
        "Mensaje":"Hoja de vida actualizada",
        "id": id
    }

#ELIMINAR UN AHOJA DE VIDA POR ID

@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminar_hv(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    buscar = "SELECT id_HV FROM HOJAS_VIDA WHERE id_HV =%s"
    cursor.execute(buscar,(id,))
    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()
        return{"mensaje":"No se encontro la hoja de vida"}

    sql_eliminar = """DELETE FROM HOJAS_VIDA WHERE id_HV=%s"""

    cursor.execute(sql_eliminar,(id,))

    conec.commit()
    cursor.close()
    conec.close()
    return {"mensaje":"Hoja de vida eliminada",
            "id": id
    }


#CONSULTAR HV por id 

@app.route("/api/consultahv/<int:id>", methods=["GET"])
def obtener_hvida(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)


    sql = """SELECT * FROM HOJAS_VIDA WHERE id_HV= %s"""
    cursor.execute (sql,(id,))

    datos = cursor.fetchone()

    cursor.close()
    conec.close()

    if datos is None:
        return {"mensaje":"No se encontro la hoja de vida"}

    return datos

@app.route("/api/registrohv", methods=["POST"])
def registrohvida():
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.get_json() 

    # Consultar si el correo ya existe en la base de datos
    cursor.execute("SELECT * FROM HOJAS_VIDA WHERE correo = %s", (datos['correo'],))

    
    resultado = cursor.fetchone()

    if resultado:
        cursor.close()
        conec.close()
        return {"mensaje": "El correo ya está registrado"}

    sql = """INSERT INTO HOJAS_VIDA (nombre, edad, ciudad, correo, fotografia, programa, ficha, jornada) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
             
    cursor.execute(sql, (
        datos["nombre"],
        datos["edad"],
        datos["ciudad"],
        datos["correo"],
        datos.get("fotografia"),
        datos["programa"],
        datos["ficha"],
        datos["jornada"]
    ))

    
    id_generado = cursor.lastrowid

    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Hoja de vida creada", "id": id_generado}

@app.route("/")
def inicio():
    return "Api hoja de vida funcionando"

@app.route("/api/hojasdevida/<int:id>")
def obtener_hojasvidaid(id):
    return {
        "mensaje": "Hoja de vida encontrada",
        "id": id
    }

@app.route("/api/hojasdevida")
def obtener_hojasvida():
    hojasdevida = [
        {
            "id": 1,
            "nombre": "Johanna Cifuentes",
            "edad": 50,
            "ciudad": "Bogota",
            "correo": "johanna.cifuentes@example.com",
            "fotografia": "foto",
            "programa": "adso",
            "ficha": 2323,
            "jornada": "diurna"
        },
        {
            "id": 2,
            "nombre": "Leydy Diaz",
            "edad": 18,
            "ciudad": "Cali",
            "correo": "leydy.diaz@example.com",
            "fotografia": "foto",
            "programa": "Fotografia",
            "ficha": 1010,
            "jornada": "Nocturna"
        }
    ]
    return hojasdevida

#________________________________________________ ESTUDIOS

#Consultar todos los estudios asociados a una hoja de vida.

@app.route("/api/HOJAS_VIDA/<int:id>/estudios", methods=["GET"])
def consultar_estudios(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT id_EST, id_HV, nivel, institucion, titulo, anio_graduacion FROM ESTUDIOS WHERE id_HV = %s"""

    cursor.execute(sql, (id,))
    estudios = cursor.fetchall()

    cursor.close()
    conec.close()

    return {"hoja_de_vida_id": id, "estudios": estudios

    }

#Registrar un nuevo estudio para una hoja de vida.

@app.route("/api/estudios/<int:id>/estudios", methods=["POST"])
def registrar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor() 
    datos = request.json

    nivel = datos.get("nivel")
    institucion = datos.get("institucion")
    titulo = datos.get("titulo")
    anio_graduacion = datos.get("anio_graduacion")

    sql = """INSERT INTO estudios (nivel, institucion, titulo, anio_graduacion, id_HV)
        VALUES (%s, %s, %s, %s, %s)"""

    cursor.execute(sql, (nivel, institucion, titulo, anio_graduacion, id))

    conec.commit()

    id_estudio = cursor.lastrowid

    cursor.close()
    conec.close()

    return {"mensaje": "Estudio registrado para la hoja de vida",
             "id_EST": id_estudio
    }

#Consultar un estudio especifico

@app.route("/api/estudios/<int:id>", methods=["GET"])
def consultar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = "SELECT id_EST, nivel, institucion, titulo, anio_graduacion FROM ESTUDIOS WHERE id_EST = %s"""
    cursor.execute(sql, (id,))
    estudio = cursor.fetchone()

    cursor.close()
    conec.close()

    if estudio is None:
        return {"mensaje": "Estudio no encontrado"}, 404

    return estudio, 200

#actualizar un estudio con su id

@app.route("/api/estudios/<int:id>/estudios", methods=["PUT"])
def actualizar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    # Actualizar el estudio
    sql = """UPDATE estudios SET nivel = %s, institucion = %s, titulo = %s, anio_graduacion = %s WHERE id_EST = %s"""
    cursor.execute(sql, (datos.get("nivel"), datos.get("institucion"), datos.get("titulo"), datos.get("anio_graduacion"), id))

    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Estudio actualizado", "id_EST": id}

#eliminar un estudio 

@app.route("/api/estudios/<int:id>", methods=["DELETE"])
def eliminar_estudio(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM ESTUDIOS WHERE id_EST = %s"

    cursor.execute(sql, (id,))

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Estudio eliminado",
        "id_EST": id
    }, 200



#________________________________________________ EXPERIENCIA LABORAL 

#REGISTRAR UNA EXPERIENCIA LABORAL 

@app.route("/api/EXPERIENCIAS/<int:id>/EXPERIENCIAS", methods=["POST"])
def registrar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor() 
    datos = request.json

    empresa = datos.get("empresa")
    cargo = datos.get("cargo")
    tiempo = datos.get("tiempo")
    funciones = datos.get("funciones")

    sql = """INSERT INTO EXPERIENCIAS (empresa, cargo, tiempo, funciones, id_HV)
        VALUES (%s, %s, %s, %s, %s)"""

    cursor.execute(sql, (empresa, cargo, tiempo, funciones, id))

    conec.commit()

    id_experiencia = cursor.lastrowid

    cursor.close()
    conec.close()

    return {"mensaje": "Experiencia registrada para la hoja de vida",
             "id_exp": id_experiencia
    }

#Consultar las experiencias asociadas a una hoja de vida.

@app.route("/api/HOJAS_VIDA/<int:id>/EXPERIENCIAS", methods=["GET"])
def consultar_experienciashv(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT id_exp, id_HV, empresa, cargo, tiempo, funciones FROM EXPERIENCIAS WHERE id_HV = %s"""

    cursor.execute(sql, (id,))
    experiencias = cursor.fetchall()

    cursor.close()
    conec.close()

    return {"hoja_de_vida_id": id, "experiencias": experiencias}

#consultar una experiencia especifica

@app.route("/api/EXPERIENCIAS/<int:id>", methods=["GET"])
def consultar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT * FROM EXPERIENCIAS WHERE id_exp = %s"""
    cursor.execute(sql, (id,))
    experiencia = cursor.fetchone()

    cursor.close()
    conec.close()

    if experiencia is None:
        return {"mensaje": "Experiencia no encontrada"}, 404

    return experiencia, 200

#actualizar una experiencia laboral de una hoja de vida especifica por medio de su id

@app.route("/api/EXPERIENCIAS/<int:id_hv>/<int:id_exp>", methods=["PUT"])
def actualizar_experiencia(id_hv, id_exp):

    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    # Actualizar la experiencia
    sql = """UPDATE EXPERIENCIAS SET empresa = %s, cargo = %s, tiempo = %s, funciones = %s WHERE id_exp = %s AND id_HV = %s"""
    cursor.execute(sql, (datos.get("empresa"), datos.get("cargo"), datos.get("tiempo"), datos.get("funciones"), id_exp, id_hv))

    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Experiencia actualizada", "id_exp": id_exp, "id_HV": id_hv}

#eliminar una experiencia laboral de una hoja de vida especifica por medio su id

@app.route("/api/EXPERIENCIAS/<int:id_hv>/<int:id_exp>", methods=["DELETE"])
def eliminar_experiencia(id_hv, id_exp):

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM EXPERIENCIAS WHERE id_exp = %s AND id_HV = %s"""

    cursor.execute(sql, (id_exp, id_hv))

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Experiencia eliminada",
        "id_exp": id_exp,
        "id_HV": id_hv
    }, 200

#________________________________________________ HABILIDADES 

#registrar una habilidad a una experiencia laboral 

@app.route("/api/HABILIDADES/<int:id_exp>", methods=["POST"])
def registrar_habilidad(id_exp):
    conec = conectar_bd()
    cursor = conec.cursor() 
    datos = request.json

    nombre = datos.get("nombre")

    sql = """INSERT INTO HABILIDADES (id_exp, nombre)VALUES (%s, %s)"""

    cursor.execute(sql, (id_exp, nombre))

    conec.commit()

    id_habilidades = cursor.lastrowid

    cursor.close()
    conec.close()

    return {"mensaje": "Habilidad registrada en la experiencia laboral",
             "id_habi": id_habilidades,
             "id_exp": id_exp}

#Consultar habilidades de una experiencia.

@app.route("/api/HABILIDADES/<int:id_exp>", methods=["GET"])
def consultar_habilidades(id_exp):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT id_habi, id_exp, nombre FROM HABILIDADES WHERE id_exp = %s"""

    cursor.execute(sql, (id_exp,))
    habilidades = cursor.fetchall()

    cursor.close()
    conec.close()

    return {"habilidades": habilidades}

# Actualizar una habilidad

@app.route("/api/HABILIDADES/<int:id_habi>", methods=["PUT"])
def actualizar_habilidad(id_habi):

    conec = conectar_bd()
    cursor = conec.cursor()

    datos = request.json

    nombre = datos.get("nombre")

    sql = """UPDATE HABILIDADES
             SET nombre = %s
             WHERE id_habi = %s"""

    cursor.execute(sql, (nombre, id_habi))

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Habilidad actualizada",
        "id_habi": id_habi
    }, 200

#Eliminar una habilidad 

@app.route("/api/HABILIDADES/<int:id_habi>", methods=["DELETE"])
def eliminar_habilidad(id_habi):

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = """DELETE FROM HABILIDADES
             WHERE id_habi = %s"""

    cursor.execute(sql, (id_habi,))

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Habilidad Eliminada",
        "id_habi": id_habi
    }, 200

#________________________________________________ CURSOS

#Registrar un curso 

@app.route("/api/CURSOS/<int:id_hv>", methods=["POST"])
def registrar_cursos(id_hv):

    conec = conectar_bd()
    cursor = conec.cursor() 
    datos = request.json

    nombre = datos.get("nombre")

    sql = """INSERT INTO CURSOS (id_HV, nombre)VALUES (%s, %s)"""

    cursor.execute(sql, (id_hv, nombre))

    conec.commit()

    id_curso = cursor.lastrowid

    cursor.close()
    conec.close()

    return {"mensaje": "Curso registrado en la hoja de vida",
             "id_CUR": id_curso,
             "id_hv": id_hv}

#Consultar cursos asociadas a una hoja de vida.

@app.route("/api/HOJAS_VIDA/<int:id>/CURSOS", methods=["GET"])
def consultar_cursoshv(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT id_CUR, id_HV, nombre FROM CURSOS WHERE id_HV = %s"""

    cursor.execute(sql, (id,))
    cursos = cursor.fetchall()

    cursor.close()
    conec.close()

    return {"hoja_de_vida_id": id, "CURSOS": cursos }

#consultar un curso especifico

@app.route("/api/CURSOS/<int:id>", methods=["GET"])
def consultar_curso(id):
    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT * FROM CURSOS WHERE id_CUR = %s"""
    cursor.execute(sql, (id,))
    curso = cursor.fetchone()

    cursor.close()
    conec.close()

    if curso is None:
        return {"mensaje": "Curso no encontrada"}, 404

    return curso, 200

# Actualizar un curso

@app.route("/api/CURSOS/<int:id_CUR>", methods=["PUT"])
def actualizar_curso(id_CUR):

    conec = conectar_bd()
    cursor = conec.cursor()

    datos = request.json

    nombre = datos.get("nombre")

    sql = """UPDATE CURSOS
             SET nombre = %s
             WHERE id_CUR = %s"""

    cursor.execute(sql, (nombre, id_CUR))

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Curso actualizado",
        "id_CUR": id_CUR
    }, 200

#Eliminar un curso

@app.route("/api/CURSOS/<int:id_CUR>", methods=["DELETE"])
def eliminar_curso(id_CUR):

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = """DELETE FROM CURSOS
             WHERE id_CUR = %s"""

    cursor.execute(sql, (id_CUR,))

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Curso Eliminado",
        "id_CUR": id_CUR
    }, 200

#consultar hoja de vida completa 

@app.route("/api/HOJAS_VIDA/<int:id>", methods=["GET"])
def consultar_hoja_vida_completa(id):
    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    # Consultar la hoja de vida
    sql_hv = """SELECT * FROM HOJAS_VIDA WHERE id_HV = %s"""
    cursor.execute(sql_hv, (id,))
    hoja_vida = cursor.fetchone()

    if hoja_vida is None:
        cursor.close()
        conec.close()
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

    cursor.close()
    conec.close()

    respuesta_completa = {
        "hoja_de_vida": hoja_vida,
        "estudios": estudios,
        "experiencias": experiencias,
        "cursos": cursos
    }

    return respuesta_completa, 200


if __name__ == "__main__":
    app.run(debug=True)