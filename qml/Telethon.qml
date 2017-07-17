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

    property var progressHandlers: []
    property var iconHandlers: []

    onError: {
        pageStack.currentPage.error()
        console.log("Error: " + traceback)
        errorNotification.show(traceback)
    }

    Component.onCompleted: {

        addImportPath(Qt.resolvedUrl("../"))
        importModule("TgClient", function () {})
        // importNames requires io.thp.pyotherside 1.5
        // importNames("TgClient", ["connect", "client"], function () {})

        setHandler("log", function(message) {
            console.log("Python: " + message)
        })

        // accept data from Telegram
        setHandler("update_dialogs", function(dialogs) {
            dialogsModel.clear()
            for (var i=0; i<dialogs.length; i++) {
                dialogsModel.append(dialogs[i])
            }
        })

        setHandler("new_messages", function(entityID, messages) {
            if (currentDialog.entityID !== entityID) return
            if ((dialogModel.count > 0) && (messages[messages.length-1].id < dialogModel.get(0).id)) {
                // prepend
                for (var i=0; i<messages.length; i++) {
                    dialogModel.insert(i,  messages[i])
                }
            } else {
                // append
                for (var i=0; i<messages.length; i++) {
                    dialogModel.append(messages[i])
                }
                pageStack.currentPage.jumpToBottom()
            }
        })

        setHandler("update_message", function(message) {
            for (var i=0; i<dialogModel.count; i++) {
                if (dialogModel.get(i).id === message.id) {
                    dialogModel.set(i, message)
                    break
                }
            }
        })

        setHandler("delete_messages", function(messages_ids) {
            for (var imsg=0; imsg<messages_ids.length; imsg++) {
                for (var imodel=0; imodel<dialogModel.count; imodel++) {
                    if (dialogModel.get(imodel).id === messages_ids[imsg]) {
                        dialogModel.remove(imodel)
                        break
                    }
                }
            }
        })

        setHandler("contacts_list", function(contacts) {
            contactsModel.clear()
            for (var i=0; i<contacts.length; i++) {
                contactsModel.append(contacts[i])
            }
        })

        setHandler("progress", function(media_id, value) {
            if (progressHandlers.hasOwnProperty(media_id)) {
                for (var i=0; i<progressHandlers[media_id].length; i++) {
                    progressHandlers[media_id][i](value)
                }
            }
        })

        setHandler("icon", function(entity_id, source) {
            if (iconHandlers.hasOwnProperty(entity_id)) iconHandlers[entity_id](source)
        })

    }

     // set up connection to Telegram
    function connect() {
        call("TgClient.connect", [], function(status) {
            if (status === "enter_number") {
                pageStack.replace(Qt.resolvedUrl("pages/ConnectPage.qml"))
            } else if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            }
        });
    }

    function retry() {
        call('TgClient.reset_session')
        connect()
    }

    function send_code(code) {
        call("TgClient.client.send_code", [code], function(status) {
            if (status === "pass_required") {
                pageStack.replace(Qt.resolvedUrl("pages/PasswordPage.qml"))
            } else if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else if (status === "invalid") {
                errorNotification.show("Invalid login code");
            }
        })
    }

    function send_pass(password) {
        call("TgClient.client.send_pass", [password], function(status) {
            if (status === true) {
                pageStack.replace(Qt.resolvedUrl("pages/DialogsPage.qml"))
            } else if (status === "invalid") {
                errorNotification.show("Invalid password");
            }
        })
    }

    // set download progress handler
    function registerProgressHandler(media_id, progress_callback) {
        if (!progressHandlers.hasOwnProperty(media_id)) {
            progressHandlers[media_id] = []
        }
        progressHandlers[media_id].push(progress_callback)
    }

    // set icon update handler
    function registerIconHandler(entity_id, icon_callback) {
        iconHandlers[entity_id] = icon_callback
    }

    // clear dialog data
    function clearDialog() {
        dialogModel.clear()
        currentDialog.entityID = ""
        currentDialog.title = ""
        progressHandlers = []
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
