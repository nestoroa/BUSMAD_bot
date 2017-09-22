#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
get_texto(nombre)
    consulta uno de los textos predefinidos de la base de datos y lo devuelve como string.
    nombre: identificador del texto
"""
import MySQLdb as MySQL
import sys
import credentialsReader as cr

reload(sys)
sys.setdefaultencoding("utf-8")

def get_texto(nombre):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("""SELECT Texto FROM Texto WHERE Nombre = %s""", (nombre,))
    texto = make_unicode(
        c.fetchone()[0])  # fetchone devuelve una tupla, al elegir '0' te devuelve el string de texto deseado
    c.close()
    db.close()
    return texto


"""
get_estado(usuario)
    consulta el estado de la conversación con el usuario en la base de datos
ARGUMENTOS:
    usuario: identificador del usuario
"""


def get_status(usuario):  # FUCNCION COMPLETA
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("""SELECT Estado FROM Estado_Conversacion WHERE ID_Usuario = %s""", (usuario,))
    estado = c.fetchone()[0]  # fetchone devuelve una tupla, al elegir '0' te devuelve el string de texto deseado
    c.close()
    db.close()
    return estado


"""
submit_parada(chat_id, numparada)
    Guarda en la base de datos la consulta de espera de una parada realizada por un usuario determinado.
    Realizado como control estadístico.
"""


def submit_stop(chat_id, numparada):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("INSERT INTO Log_paradas (ID_Usuario, ID_Parada) VALUES (%s, %s)", (chat_id, numparada))
    db.commit()
    c.close()
    db.close()


def submit_user(id_usuario, username):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("INSERT INTO Usuario (ID_Usuario, Username) VALUES (%s, %s)ON DUPLICATE KEY UPDATE  Username= %s",
              (id_usuario, username, username))
    db.commit()
    c.close()
    db.close()


def submit_fav(chat_id, numparada):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("INSERT INTO Favorito (ID_Usuario, ID_Parada) VALUES (%s, %s)", (chat_id, numparada))
    db.commit()
    c.close()
    db.close()


def submit_fav_descripcion(chat_id, numparada, descripcion):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("UPDATE Favorito SET Descripcion = %s WHERE ID_Usuario = %s AND ID_Parada = %s",
              (descripcion, chat_id, numparada))
    db.commit()
    c.close()
    db.close()


def get_favs(usuario):
    db = connect(cr.loadToken())
    c = db.cursor()
    listafavoritos = []
    i = 0
    c.execute("""SELECT ID_Parada, Descripcion FROM Favorito WHERE ID_Usuario = %s""", (usuario,))
    aux = c.fetchone()
    while aux is not None:
        listafavoritos.append(aux)
        aux = c.fetchone()
        i += 1
    string = u''
    for favorito in listafavoritos:
        string += u'\n' + make_unicode(favorito[1]) + u' /' + str(favorito[0])
    if string == u'':
        string = u'No tienes hay paradas en tu lista\nPrueba a /guardar alguna'
        submit_status(usuario, 0)
    c.close()
    db.close()
    return string


def get_users():
    db = connect(cr.loadToken())
    c = db.cursor()
    lista_users = []
    i = 0
    c.execute("""SELECT ID_Usuario FROM Usuario""", )
    aux = c.fetchone()
    while aux is not None:
        lista_users.append(aux[0])
        aux = c.fetchone()
        i += 1
    c.close()
    db.close()
    return lista_users


def submit_status(chat_id, estado):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute(
        "INSERT INTO Estado_Conversacion (ID_Usuario, Estado) VALUES( %s, %s) ON DUPLICATE KEY UPDATE ID_Usuario= %s, Estado= %s",
        (chat_id, estado, chat_id, estado,))
    db.commit()
    c.close()
    db.close()


def get_status_stop(usuario):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("""SELECT ID_Parada FROM Estado_Conversacion WHERE ID_Usuario = %s""", (usuario,))
    numparada = c.fetchone()[0]  # fetchone devuelve una tupla, al elegir '0' te devuelve el string de texto deseado
    c.close()
    db.close()
    return numparada


def set_status_stop(numparada, usuario):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("""UPDATE Estado_Conversacion SET ID_Parada = %s WHERE ID_Usuario = %s""", (numparada, usuario))
    db.commit()
    c.close()
    db.close()


def delete_fav(chat_id, numparada):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("DELETE FROM Favorito WHERE ID_Usuario = %s AND ID_Parada = %s", (chat_id, numparada))
    db.commit()
    c.close()

    db.close()


def fav_exists(usuario, numparada):
    db = connect(cr.loadToken())
    c = db.cursor()
    c.execute("""SELECT ID_Parada FROM Favorito WHERE ID_Usuario = %s AND ID_Parada = %s""", (usuario, numparada))
    aux = c.fetchone()
    if aux is not None:
        c.close()
        db.close()
        return True
    else:
        c.close()
        db.close()
        return False


def connect(token):
    return MySQL.connect(host=token['DBHost'], user=token["DBUser"], passwd=token["DBPswd"], db=token["DBdb"],
                         port=token["DBPort"], charset='utf8')


def make_unicode(str_input):
    if type(str_input) != unicode:
        str_input = str_input.decode('utf-8')
        return str_input
    else:
        return str_input
