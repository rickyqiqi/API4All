#coding=utf-8

import os
import sys
from flask import Flask, session, request
from flask_socketio import SocketIO, Namespace, send, emit
import logging
import logging.config
from pysqlcipher3 import dbapi2 as sqlite

from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

#imp.reload(sys)
#sys.setdefaultencoding('utf-8')

logging.config.fileConfig("/var/www/appserver/logger.conf")
logger = logging.getLogger("main")
telegramlogger = logging.getLogger("telegram")

class AppSocketIO(Namespace):
    numUsers = 0

    def on_connect(self):
        logger.info('#=> An app client connected')
        session['addedUser'] = False

    def on_disconnect(self):
        logger.info('#=> An app client disconnected')
        if session['addedUser']:
            self.numUsers -= 1
            emit('user_left', {"username": session['username'], "numUsers": self.numUsers}, broadcast=True)

    def on_add_user(self, username):
        logger.info('#=> Add a user: %s %d' %(username, session['addedUser']))
        if session['addedUser']: return

        session['username'] = username
        self.numUsers += 1
        session['addedUser'] = True
        emit('login', {"numUsers": self.numUsers})

        emit('user_joined', {"username": session['username'], "numUsers": self.numUsers}, broadcast=True)

    def on_new_message(self, data):
        logger.info('#=> New message: %s' %(data))
        emit('new_message', {"username": session['username'], "message": data}, broadcast=True)

    def on_typing(self):
        logger.info('#=> Typing')
        emit('typing', {"username": session['username']}, broadcast=True)

    def on_stop_typing(self):
        logger.info('#=> Stop typing')
        emit('stop_typing', {"username": session['username']}, broadcast=True)

socketio.on_namespace(AppSocketIO('/'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')