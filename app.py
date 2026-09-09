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
        "id": id}

#ELIMINAR UN AHOJA DE VIDA POR ID

@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminar_hv(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute("SELECT id_HV FROM HOJAS_VIDA WHERE id_HV =%s",(id,))
    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()
        return{"mensaje":"No se encontro la hoja de vida"}

    sql = """DELETE FROM hojas_vida WHERE id_HV=%s"""

    cursor.execute(sql,(id,))
    conec.commit()
    cursor.close()
    conec.close()
    return {"mensaje":"Hoja de vida eliminada"}



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


#Consultar todos los estudios asociados a una hoja de vida.

@app.route("/api/HOJAS_VIDA/<int:id>/estudios", methods=["GET"])
def consultar_estudios(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """SELECT id_EST, id_HV, nivel, institucion, titulo, anio_graduacion FROM ESTUDIOS WHERE id_hv = %s"""

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

#Concultar un estudio especifico

@app.route("/api/estudios/<int:id>", methods=["GET"])
def consultar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = "SELECT * FROM estudios WHERE id_EST = %s"
    cursor.execute(sql, (id,))
    estudio = cursor.fetchone()

    cursor.close()
    conec.close()

    if estudio:
        return {"mensaje": "Estudio encontrado", "estudio": estudio}
    else:
        return {"mensaje": "Estudio no encontrado"}, 404

#

if __name__ == "__main__":
    app.run(debug=True)