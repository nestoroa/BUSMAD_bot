#!/usr/bin/env python
# -*- coding: utf-8 -*-


def loadToken():
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
    return token
