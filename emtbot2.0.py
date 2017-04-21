#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
To-Do:
    /guarda : función de guardar parada favorita
        Paso 1: Almacenar número de parada
        Paso 2: Almacenar descripción
        Paso 3: Confirmar operación
    /elimina : función de eliminar parada favorita
        Paso 1: Almacenar número de parada
        Paso 2: Confirmar operación
    /favoritos: Consultar paradas favoritas
        Paso 1: Ofrecer paradas favoritas al usuario
        Paso 2: Devolver información de parada favorita
"""

import datetime
import time
import MySQLdb as MySQL
import telepot
from pyemtmad import Wrapper
import sys
import os

reload(sys)
sys.setdefaultencoding("utf-8")

"""
arrival_parser(arrivals)
    Convierte los datos del objeto "Arrivals" ofrecido por el wrapper pyemtmad
    en un string legible para ser enviado como mensaje
BUGS:
    en ocasiones devuelve los minutos como float y no como integer
"""


def arrival_parser(arrivals):
    string = ''
    for Arrival in arrivals[1]:
        string += 'Linea ' + Arrival.line_id + ': '
        tiempo = Arrival.time_left
        if tiempo >= 1200:
            string += 'Faltan 20+ minutos'
        elif tiempo <= 60:
            string += 'Llegando'
        else:
            tiempo /= 60
            string += 'Faltan ' + str(int(tiempo)) + ' minuto/s'
        string += '\n'
    return string


''' Funciones desactivadas
def map_parser(mapa):
    string = ''
    i = 1
    for Stop in mapa[1]:
        string += str(i) + ' - ' + Stop.name + '\n'
        i += 1
    return string

def hor_parser(horario):
    string = ''
    for TimesLinesItem in horario[1]:
        string += 'Primera salida en sentido ida: ' + TimesLinesItem.first_forward + '\n'
        string += 'Primera salida en sentido vuelta: ' + TimesLinesItem.first_backward + '\n'
        string += 'Ultima salida en sentido ida: ' + TimesLinesItem.last_forward + '\n'
        string += 'Ultima salida en sentido ida: ' + TimesLinesItem.last_backward + '\n'
    return string
'''

"""
send_parada(numparada,chat_id)
    Manda la información de los tiempos de espera en una parada
    Si la API de la EMT no devuelve datos, se manda un mensaje avisando de esta situación
ARGUMENTOS:
    numparada: número de la parada de la que se desea información
    chat_id: identificador del chat destinatario del mensaje
"""


def send_parada(numparada, chat_id):
    arrivals = emt.geo.get_arrive_stop(stop_number=int(numparada), lang='es')
    if arrivals[0]:
        bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
        submit_parada(chat_id, numparada)
    else:
        bot.sendMessage(chat_id, 'No encuentro datos para ese número de parada. Puede ser por dos razones\n'
                        + ' - No existe ese número de parada.\n'
                        + ' - No hay servicio de bus en este momento.')


"""
get_texto(nombre)
    consulta uno de los textos predefinidos de la base de datos y lo devuelve como string.
    nombre: identificador del texto
"""


def get_texto(nombre):
    c = db.cursor()
    c.execute("""SELECT Texto FROM Texto WHERE Nombre = %s""", (nombre,))
    texto = make_unicode(
        c.fetchone()[0])  # fetchone devuelve una tupla, al elegir '0' te devuelve el string de texto deseado
    return texto


"""
get_estado(usuario)
    consulta el estado de la conversación con el usuario en la base de datos
ARGUMENTOS:
    usuario: identificador del usuario
"""


def get_estado(usuario):  # FUCNCION COMPLETA
    c = db.cursor()
    c.execute("""SELECT Estado FROM Estado_Conversacion WHERE ID_Usuario = %s""", (usuario,))
    estado = c.fetchone()[0]  # fetchone devuelve una tupla, al elegir '0' te devuelve el string de texto deseado
    c.close()
    return estado


"""
submit_parada(chat_id, numparada)
    Guarda en la base de datos la consulta de espera de una parada realizada por un usuario determinado.
    Realizado como control estadístico.
"""


def submit_parada(chat_id, numparada):
    c = db.cursor()
    c.execute("INSERT INTO Log_paradas (ID_Usuario, ID_Parada) VALUES (%s, %s)", (chat_id, numparada))
    db.commit()
    c.close()


def submit_user(id_usuario, username):
    c = db.cursor()
    c.execute("INSERT INTO Usuario (ID_Usuario, Username) VALUES (%s, %s)ON DUPLICATE KEY UPDATE  Username= %s",
              (id_usuario, username, username))
    db.commit()
    c.close()


def submit_favorito(chat_id, numparada):
    c = db.cursor()
    c.execute("INSERT INTO Favorito (ID_Usuario, ID_Parada) VALUES (%s, %s)", (chat_id, numparada))
    db.commit()
    c.close()


def submit_fav_descripcion(chat_id, numparada, descripcion):
    c = db.cursor()
    c.execute("UPDATE Favorito SET Descripcion = %s WHERE ID_Usuario = %s AND ID_Parada = %s",
              (descripcion, chat_id, numparada))
    db.commit()
    c.close()


def get_favoritos(usuario):
    c = db.cursor()
    listafavoritos = []
    i = 0
    c.execute("""SELECT ID_Parada, Descripcion FROM Favorito WHERE ID_Usuario = %s""", (usuario,))
    c.close()
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
        submit_estado(usuario, 0)
    return string


def submit_estado(chat_id, estado):
    c = db.cursor()
    c.execute(
        "INSERT INTO Estado_Conversacion (ID_Usuario, Estado) VALUES( %s, %s) ON DUPLICATE KEY UPDATE ID_Usuario= %s, Estado= %s",
        (chat_id, estado, chat_id, estado,))
    db.commit()
    c.close()


def get_estado_numparada(usuario):
    c = db.cursor()
    c.execute("""SELECT ID_Parada FROM Estado_Conversacion WHERE ID_Usuario = %s""", (usuario,))
    numparada = c.fetchone()[0]  # fetchone devuelve una tupla, al elegir '0' te devuelve el string de texto deseado
    c.close()
    return numparada


def set_estado_numparada(numparada, usuario):
    c = db.cursor()
    c.execute("""UPDATE Estado_Conversacion SET ID_Parada = %s WHERE ID_Usuario = %s""", (numparada, usuario))
    db.commit()
    c.close()


def eliminar_favorito(chat_id, numparada):
    c = db.cursor()
    c.execute("DELETE FROM Favorito WHERE ID_Usuario = %s AND ID_Parada = %s", (chat_id, numparada))
    db.commit()
    c.close()


def existe_favorito(usuario, numparada):
    c = db.cursor()
    c.execute("""SELECT ID_Parada FROM Favorito WHERE ID_Usuario = %s AND ID_Parada = %s""", (usuario, numparada))
    aux = c.fetchone()
    if aux is not None:
        return True
    else:
        return False
    c.close()


def make_unicode(input):
    if type(input) != unicode:
        input = input.decode('ISO-8859-1')
        return input
    else:
        return input


def conectar(token):
    return MySQL.connect(host=token['DBHost'], user=token["DBUser"], passwd=token["DBPswd"], db=token["DBdb"],
                       port=token["DBPort"])


def handle(msg):

    db = conectar(token)
    helpstr = get_texto('help')
    chat_id = msg['chat']['id']
    command = msg['text']
    try:
        username = msg['from']['username']
        username = '@' + username
    except KeyError:
        username = 'desconocido'

    now = datetime.datetime.now()

    logstring = (
        '\n[' + str(now)[:19] + "] He recibido: " + command + " de " + username + " [ID: " + str(chat_id) + "]")
    print(logstring)
    '''
    # Devuelve los tiempos de espera de un numero de parada
    if '/espera' in command and len(command) > 7:
        numparada = int(command[7:])
        arrivals = wrapper.geo.get_arrive_stop(stop_number=int(numparada), lang='es')
        if arrivals[0]:
            bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
            submit_parada(chat_id, numparada)
        else:
            bot.sendMessage(chat_id, 'Oops, no encuentro esa parada. Lo siento')
    '''
    try:
        estado = get_estado(chat_id)
    except:
        submit_user(username=username, id_usuario=chat_id)
        submit_estado(chat_id, 0)
        estado = 0

    # PRIMERA EJECUCION - Se registra el usuario en la base de datos
    if '/start' in command:
        bot.sendMessage(chat_id, helpstr)
        submit_user(username=username, id_usuario=chat_id)
        submit_estado(chat_id, 0)
        estado = 0
        db.close()

    if '/help' in command or '/ayuda' in command:
        bot.sendMessage(chat_id, helpstr)
        submit_estado(chat_id, 0)
        estado = 0
        db.close()

    if estado == 1:  # ESPERA - Eserando un número de parada
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            submit_estado(chat_id, 0)
            db.close()
        else:
            numparada = command.replace('/', '')
            try:
                arrivals = emt.geo.get_arrive_stop(stop_number=int(numparada), lang='es')
                if arrivals[0]:
                    bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
                    submit_parada(chat_id, int(numparada))
                    submit_estado(chat_id, 0)
                    db.close()
                else:
                    bot.sendMessage(chat_id, 'No encuentro datos para ese número parada.\n'
                                    + 'Puede ser porque no existe o porque no hay servicio ahora mismo\n'
                                    + 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
                    db.close()
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
                db.close()
                pass

    elif estado == 2:  # GUARDAR - Esperando número de parada
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            submit_estado(chat_id, 0)
            db.close()
        else:
            try:
                numparada = int(command)
                submit_favorito(chat_id, numparada)
                set_estado_numparada(numparada, chat_id)
                bot.sendMessage(chat_id, 'Por favor, indícame una descripción para esta parada')
                submit_estado(chat_id, 3)
                db.close()
                # guardar numero de parada

            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
                db.close()
                pass

    elif estado == 3:  # GUARDAR - Esperando descripcion
        numparada = get_estado_numparada(chat_id)
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            eliminar_favorito(chat_id, numparada)
            submit_estado(chat_id, 0)
            db.close()
        else:
            submit_fav_descripcion(chat_id, numparada, command)
            bot.sendMessage(chat_id, 'Has elegido guardar el siguiente favorito.'
                            + '\n\nNúmero de parada:  ' + str(numparada)
                            + '\nDescripción:  ' + command
                            + '\n\n¿Confirmas la operación?'
                            + '\n /SI o /NO')
            submit_estado(chat_id, 4)
            db.close()

    elif estado == 4:  # Guardar - Esperando confirmación de guardado
        numparada = get_estado_numparada(chat_id)
        if command == '/SI':
            bot.sendMessage(chat_id, 'Tu favorito se ha añadido satisfactoriamente')
            submit_estado(chat_id, 0)
            db.close()
        if command == '/NO':
            bot.sendMessage(chat_id, 'Operación cancelada')
            eliminar_favorito(chat_id, numparada)
            submit_estado(chat_id, 0)
            db.close()

    elif estado == 5:  # ELIMINAR - Esperando numero de parada
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            submit_estado(chat_id, 0)
            db.close()
        else:
            numparada = int(command.replace('/', ''))
            try:
                if existe_favorito(chat_id, numparada):
                    set_estado_numparada(numparada, chat_id)
                    submit_estado(chat_id, 6)
                    bot.sendMessage(chat_id, 'Has decidido borrar la parada nº ' + str(numparada)
                                    + ' de tus favoritos.\n\n¿Confirmas esta operación?'
                                    + '\n   /SI  o  /NO')
                    db.close()
                else:
                    bot.sendMessage(chat_id, 'Parece que la parada nº ' + str(numparada)
                                    + 'no está entre tus favoritos.\n\nPrueba de nuevo.'
                                    + '\nTambién puedes /cancelar la operación si quieres.')
                    db.close()
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un número de parada.'
                                + '\nPuedes /cancelar la operación si quieres')
                db.close()
                pass

    elif estado == 6:  # ELIMINAR - Esperando confirmación
        numparada = get_estado_numparada(chat_id)
        if command == '/SI':
            eliminar_favorito(chat_id, numparada)
            bot.sendMessage(chat_id, 'Tu favorito se ha borrado satisfactoriamente')
            submit_estado(chat_id, 0)
            db.close()
        if command == '/NO':
            bot.sendMessage(chat_id, 'Operación cancelada')
            eliminar_favorito(chat_id, numparada)
            submit_estado(chat_id, 0)
            db.close()

    else:  # ESTADO == 0  ESTADO INICIAL
        # Devuelve los tiempos de espera de un numero de parada
        if '/espera' in command and len(command) > 7:
            numparada = int(command[7:])
            send_parada(numparada, chat_id)
            submit_estado(chat_id, 0)
            db.close()

        elif '/espera' in command and len(command) == 7:
            bot.sendMessage(chat_id, 'Por favor, indícame el número de parada')
            submit_estado(chat_id, 1)
            db.close()

        elif '/guardar' in command:
            bot.sendMessage(chat_id, 'Vamos a guardar una parada en tus favoritos.\n'
                            + 'Por favor, indícame el número de parada')
            submit_estado(chat_id, 2)
            db.close()

        elif '/favoritos' in command:
            favoritos = get_favoritos(chat_id)
            string = 'Esta es tu lista de paradas favoritas. Haz click en aquella de la que' \
                     + ' quieras saber los tiempos de espera:\n\n'
            bot.sendMessage(chat_id, string + favoritos)
            submit_estado(chat_id, 1)
            db.close()

        elif '/eliminar' in command:
            favoritos = get_favoritos(chat_id)
            string = 'Esta es tu lista de paradas favoritas. Haz click en aquella de la que' \
                     + ' quieras eliminar:\n\n'
            bot.sendMessage(chat_id, string + favoritos)
            submit_estado(chat_id, 5)
            db.close()

        elif '/start' not in command and '/help' not in command and '/ayuda' not in command:
            numparada = int(command.replace('/', ''))
            try:
                arrivals = emt.geo.get_arrive_stop(stop_number=int(numparada), lang='es')
                if arrivals[0]:
                    bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
                    submit_parada(chat_id, int(numparada))
                    submit_estado(chat_id, 0)
                    db.close()
                else:
                    bot.sendMessage(chat_id, 'No encuentro datos para ese número parada.\n'
                                    + 'Puede ser porque no existe o porque no hay servicio ahora mismo\n'
                                    + 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
                    db.close()
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un comando o un número de parada.')
                db.close()
                pass

    '''
    #Devuelve las paradas de una linea determinada sentido ida
    elif '/ida' in command and len(command) > 4:
        numlinea = int(command[4:])
        mapa = wrapper.geo.get_stops_line(lines=numlinea, direction='forward', lang='es')
        if mapa[0]:
            bot.sendMessage(chat_id, 'Ida de la linea ' + str(numlinea) + ':\n' + map_parser(
                mapa) + '\nPowered by EMT de Madrid')
        else:
            bot.sendMessage(chat_id, 'Oops, no encuentro esa l�nea. Lo siento')
    '''
    '''
    # Devuelve las paradas de una linea determinada sentido vuelta
    elif '/vuelta' in command and len(command) > 7:
        numlinea = int(command[7:])
        mapa = wrapper.geo.get_stops_line(lines=numlinea, direction='backward', lang='es')
        if mapa[0]:
            bot.sendMessage(chat_id, 'Ida de la linea ' + str(numlinea) + ':\n' + map_parser(
               mapa) + '\nPowered by EMT de Madrid')
        else:
            bot.sendMessage(chat_id, 'Oops, no encuentro esa l�nea. Lo siento')
    '''


token = {}
tokenfile = open("credenciales.txt", "r")
# esta ñapa del [:-1] es porque readline te crea un '\n' al final de la linea que es caca
token["EMTMail"] = tokenfile.readline()[:-1]
token["EMToken"] = tokenfile.readline()[:-1]
token["Telegram"] = tokenfile.readline()[:-1]
token["DBHost"] = tokenfile.readline()[:-1]
token["DBPort"] = int(tokenfile.readline()[:-1])
token["DBUser"] = tokenfile.readline()[:-1]
token["DBPswd"] = tokenfile.readline()[:-1]
token["DBdb"] = tokenfile.readline()[:-1]
tokenfile.close()
emt = Wrapper(token['EMTMail'], token["EMToken"])

bot = telepot.Bot(token["Telegram"])
print("Estoy escuchando")
bot.message_loop(handle)
db = conectar(token)

while 1:
    time.sleep(10)
