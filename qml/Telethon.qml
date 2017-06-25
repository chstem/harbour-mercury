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
import io.thp.pyotherside 1.3


Python {

    onError: {
        console.log("Error: " + traceback)
        errorNotification.show(traceback)
    }

    Component.onCompleted: {

        addImportPath(Qt.resolvedUrl("../"))
        importModule("TgClient", function () {})
        // importNames requires io.thp.pyotherside 1.5
        // importNames("TgClient", ["connect", "client"], function () {})

        setHandler("log", function(message) {
            console.log(message)
        })

        // accept data from telegram
        setHandler("update_dialogs", function(dialogs) {
            dialogsModel.clear()
            for (var i=0; i<dialogs.length; i++) {
                dialogsModel.append(dialogs[i])
            }
        })

        setHandler("update_messages", function(messages) {
            dialogModel.clear()
            for (var i=0; i<messages.length; i++) {
                dialogModel.append(messages[i])
            }
            pageStack.currentPage.jumpToBottom()
        })

        setHandler("new_message", function(entityID, message) {
            if (currentDialog.entityID === entityID) {
                dialogModel.append(message)
                pageStack.currentPage.jumpToBottom()
            }
        })

        setHandler("contacts_list", function(contacts) {
            contactsModel.clear()
            for (var i=0; i<contacts.length; i++) {
                contactsModel.append(contacts[i])
            }
        })

        setHandler("progress", function(media_id, value) {
            for (var i=0; i<dialogModel.count; i++) {
                var mdict = dialogModel.get(i)
                if (mdict.media !== "") {
                    if (mdict.media_data.media_id === media_id) {
                        pageStack.currentPage.getDelegateInstanceAt(i).mediaItem.downloaded = value
                        break
                    }
                }
            }
        })

    }

     // set up connection to Telegram
    function connect() {
        call("TgClient.connect", [], function(status) {
            if (status === "enter_number") {
                pageStack.replace(Qt.resolvedUrl("pages/ConnectPage.qml"))
            } else if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else {
                errorNotification.show("Unexpected Error")
            }
        });
    }

    function send_code(code) {
        call("TgClient.client.send_code", [code], function(status) {
            if (status === "pass_required") {
                pageStack.replace(Qt.resolvedUrl("pages/PasswordPage.qml"))
            } else if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else if (status === "invalid") {
                errorNotification.show("Invalid login code");
            } else {
                errorNotification.show("Unexpected Error")
            }
        })
    }

    function send_pass(password) {
        call("TgClient.client.send_pass", [password], function(status) {
            if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else if (status === "invalid") {
                errorNotification.show("Invalid password");
            } else {

            }
        })
    }

    // generic call function
    function fcall(method, args) {
        call("TgClient.call", [method, args], function() {})
    }

    // file operations
    function file_copy(source, target) {
        call("TgClient.file_copy", [source, target])
    }

    function file_remove(path) {
        call_sync("TgClient.file_remove", [path])
    }
}
