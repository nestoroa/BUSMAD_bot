#!/usr/bin/env python
# -*- coding: utf-8 -*-

import databaseConnector as dbc
import datetime
import time
import telepot
from pyemtmad import Wrapper
import sys

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
        time = Arrival.time_left
        if time >= 1200:
            string += 'Faltan 20+ minutos'
        elif time <= 60:
            string += 'Llegando'
        else:
            time /= 60
            string += 'Faltan ' + str(int(time)) + ' minuto/s'
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


def send_stop(numparada, chat_id):
    arrivals = emt.geo.get_arrive_stop(stop_number=int(numparada), lang='es')
    if arrivals[0]:
        bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
        dbc.submit_stop(chat_id, numparada)
    else:
        bot.sendMessage(chat_id, 'No encuentro datos para ese número de parada. Puede ser por dos razones\n'
                        + ' - No existe ese número de parada.\n'
                        + ' - No hay servicio de bus en este momento.')


def handle(msg):
    helpstr = dbc.get_texto('help')
    chat_id = msg['chat']['id']
    command = msg['text']
    try:
        username = msg['from']['username']
        username = '@' + username
    except KeyError:
        username = 'desconocido'

    now = datetime.datetime.now()

    logstring = (
        '[' + str(now)[:19] + "] He recibido: " + command + " de " + username + " [ID: " + str(chat_id) + "]")
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
        status = dbc.get_status(chat_id)
    except:
        dbc.submit_user(username=username, id_usuario=chat_id)
        dbc.submit_status(chat_id, 0)
        status = 0

    # PRIMERA EJECUCION - Se registra el usuario en la base de datos
    if '/start' in command:
        bot.sendMessage(chat_id, helpstr)
        dbc.submit_user(username=username, id_usuario=chat_id)
        dbc.submit_status(chat_id, 0)
        status = 0

    if '/help' in command or '/ayuda' in command:
        bot.sendMessage(chat_id, helpstr)
        dbc.submit_status(chat_id, 0)
        status = 0

    if status == 1:  # ESPERA - Eserando un número de parada
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            dbc.submit_status(chat_id, 0)
        else:
            stop_number = command.replace('/', '')
            try:
                arrivals = emt.geo.get_arrive_stop(stop_number=int(stop_number), lang='es')
                if arrivals[0]:
                    bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
                    dbc.submit_stop(chat_id, int(stop_number))
                    dbc.submit_status(chat_id, 0)
                else:
                    bot.sendMessage(chat_id, 'No encuentro datos para ese número parada.\n'
                                    + 'Puede ser porque no existe o porque no hay servicio ahora mismo\n'
                                    + 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
                pass

    elif status == 2:  # GUARDAR - Esperando número de parada
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            dbc.submit_status(chat_id, 0)
        else:
            try:
                stop_number = int(command)
                dbc.submit_fav(chat_id, stop_number)
                dbc.set_status_stop(stop_number, chat_id)
                bot.sendMessage(chat_id, 'Por favor, indícame una descripción para esta parada')
                dbc.submit_status(chat_id, 3)
                # guardar numero de parada
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
                pass

    elif status == 3:  # GUARDAR - Esperando descripcion
        stop_number = dbc.get_status_stop(chat_id)
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            dbc.delete_fav(chat_id, stop_number)
            dbc.submit_status(chat_id, 0)
        else:
            dbc.submit_fav_descripcion(chat_id, stop_number, command)
            bot.sendMessage(chat_id, 'Has elegido guardar el siguiente favorito.'
                            + '\n\nNúmero de parada:  ' + str(stop_number)
                            + '\nDescripción:  ' + command
                            + '\n\n¿Confirmas la operación?'
                            + '\n /SI o /NO')
            dbc.submit_status(chat_id, 4)

    elif status == 4:  # Guardar - Esperando confirmación de guardado
        stop_number = dbc.get_status_stop(chat_id)
        if command == '/SI':
            bot.sendMessage(chat_id, 'Tu favorito se ha añadido satisfactoriamente')
            dbc.submit_status(chat_id, 0)
        if command == '/NO':
            bot.sendMessage(chat_id, 'Operación cancelada')
            dbc.delete_fav(chat_id, stop_number)
            dbc.submit_status(chat_id, 0)

    elif status == 5:  # ELIMINAR - Esperando numero de parada
        if '/cancelar' in command:
            bot.sendMessage(chat_id, 'Operación cancelada')
            dbc.submit_status(chat_id, 0)
        else:
            stop_number = int(command.replace('/', ''))
            try:
                if dbc.fav_exists(chat_id, stop_number):
                    dbc.set_status_stop(stop_number, chat_id)
                    dbc.submit_status(chat_id, 6)
                    bot.sendMessage(chat_id, 'Has decidido borrar la parada nº ' + str(stop_number)
                                    + ' de tus favoritos.\n\n¿Confirmas esta operación?'
                                    + '\n   /SI  o  /NO')
                else:
                    bot.sendMessage(chat_id, 'Parece que la parada nº ' + str(stop_number)
                                    + 'no está entre tus favoritos.\n\nPrueba de nuevo.'
                                    + '\nTambién puedes /cancelar la operación si quieres.')
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un número de parada.'
                                + '\nPuedes /cancelar la operación si quieres')
                pass

    elif status == 6:  # ELIMINAR - Esperando confirmación
        stop_number = dbc.get_status_stop(chat_id)
        if command == '/SI':
            dbc.delete_fav(chat_id, stop_number)
            bot.sendMessage(chat_id, 'Tu favorito se ha borrado satisfactoriamente')
            dbc.submit_status(chat_id, 0)
        if command == '/NO':
            bot.sendMessage(chat_id, 'Operación cancelada')
            dbc.delete_fav(chat_id, stop_number)
            dbc.submit_status(chat_id, 0)

    else:  # ESTADO == 0  ESTADO INICIAL
        # Devuelve los tiempos de espera de un numero de parada
        if '/espera' in command and len(command) > 7:
            stop_number = int(command[7:])
            send_stop(stop_number, chat_id)
            dbc.submit_status(chat_id, 0)

        elif '/espera' in command and len(command) == 7:
            bot.sendMessage(chat_id, 'Por favor, indícame el número de parada')
            dbc.submit_status(chat_id, 1)

        elif '/guardar' in command:
            bot.sendMessage(chat_id, 'Vamos a guardar una parada en tus favoritos.\n'
                            + 'Por favor, indícame el número de parada')
            dbc.submit_status(chat_id, 2)

        elif '/favoritos' in command:
            favourites = dbc.get_favs(chat_id)
            string = 'Esta es tu lista de paradas favoritas. Haz click en aquella de la que' \
                     + ' quieras saber los tiempos de espera:\n\n'
            bot.sendMessage(chat_id, string + favourites)
            dbc.submit_status(chat_id, 1)

        elif '/eliminar' in command:
            favourites = dbc.get_favs(chat_id)
            string = 'Esta es tu lista de paradas favoritas. Haz click en aquella de la que' \
                     + ' quieras eliminar:\n\n'
            bot.sendMessage(chat_id, string + favourites)
            dbc.submit_status(chat_id, 5)

        elif '/difusion' in command and username == "@nestoroa":
            print("prueba")
            users_list = dbc.get_users()
            print(users_list)
            for user in users_list:
                try:
                    bot.sendMessage(user, "MENSAJE DE DIFUSIÓN:\n" + command.split("/difusion "))
                except:
                    pass

        elif '/start' not in command and '/help' not in command and '/ayuda' not in command:
            stop_number = int(command.replace('/', ''))
            try:
                arrivals = emt.geo.get_arrive_stop(stop_number=int(stop_number), lang='es')
                if arrivals[0]:
                    bot.sendMessage(chat_id, arrival_parser(arrivals) + '\nPowered by EMT de Madrid')
                    dbc.submit_stop(chat_id, int(stop_number))
                    dbc.submit_status(chat_id, 0)
                else:
                    bot.sendMessage(chat_id, 'No encuentro datos para ese número parada.\n'
                                    + 'Puede ser porque no existe o porque no hay servicio ahora mismo\n'
                                    + 'Por favor, introduce un número de parada.\nPuedes /cancelar si quieres')
            except ValueError:
                bot.sendMessage(chat_id, 'Por favor, introduce un comando o un número de parada.')
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


credentials = {"EMTMail": sys.argv[1], "EMToken": sys.argv[2], "Telegram": sys.argv[3], "DBHost": sys.argv[4],
               "DBPort": sys.argv[5], "DBUser": sys.argv[6], "DBPswd": sys.argv[7], "DBdb": sys.argv[8]}
emt = Wrapper(credentials['EMTMail'], credentials["EMToken"])
bot = telepot.Bot(credentials["Telegram"])
print("EMT_Bot: Estoy escuchando")
bot.message_loop(handle)

while 1:
    time.sleep(10)
