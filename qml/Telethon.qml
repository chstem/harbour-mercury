/*
    Copyright (C) 2017 Christian Stemmle

    This file is part of Mercury.

    Mercury is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Mercury is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Mercury. If not, see <http://www.gnu.org/licenses/>.
*/

import QtQuick 2.0
import Sailfish.Silica 1.0
import io.thp.pyotherside 1.4


Python {

    onError: console.log('Error: ' + traceback)

    Component.onCompleted: {

        addImportPath(Qt.resolvedUrl('../'))
        importModule('TgClient', function () {})
        // importNames requires io.thp.pyotherside 1.5
        // importNames('TgClient', ['connect', 'client'], function () {})

        setHandler('log', function(message) {
            console.log(message)
        })

        // accept data from telegram
        setHandler('update_dialogs', function(dialogs) {
            dialogsModel.clear()
            for (var i=0; i<dialogs.length; i++) {
                dialogsModel.append(dialogs[i])
            }
        })

        setHandler('update_messages', function(messages) {
            dialogModel.clear()
            for (var i=0; i<messages.length; i++) {
                dialogModel.append(messages[i])
            }
        })

    }

     // set up connection to Telegram
    function connect() {
        call('TgClient.connect', [], function(status) {
            if (status === 'flood_error') {
                // TODO: error message
                console.log('FloodError: too many requests')
            } else if (status === 'enter_number') {
                pageStack.replace(Qt.resolvedUrl("pages/ConnectPage.qml"))
            } else if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            }
        });
    }

    function send_code(code) {
        call('TgClient.client.send_code', [code], function(status) {
            if (status === 'pass_required') {
                pageStack.replace(Qt.resolvedUrl("pages/PasswordPage.qml"))
            } else if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else {
                // TODO: display error message
                console.log("error validating code")
            }
        })
    }

    function send_pass(password) {
        call('TgClient.client.send_pass', [password], function(status) {
            if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else {
                // TODO: display error message
                console.log("error validating code")
            }
        })
    }

    // generic call function
    function fcall(method, args) {
        call('TgClient.call', [method, args], function() {})
    }
}
