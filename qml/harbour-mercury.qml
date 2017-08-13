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
import "pages"
import "components"


ApplicationWindow
{
    initialPage: Component { StartPage {} }
    cover: Qt.resolvedUrl("cover/CoverPage.qml")
    allowedOrientations: defaultAllowedOrientations
    _defaultPageOrientations: Orientation.All

    // Telegram API
    Telethon { id: backend }

    // global properties
    ListModel {
        id: dialogsModel
    }
    ListModel {
        id: contactsModel
    }

    Item {
        id: currentDialog
        property string entityID: ""
        property string title: ""
        property string icon: ""
    }
    ListModel {
        id: dialogModel
    }

    AppNotification {
        id: errorNotification
    }

    Python {
        id: logger
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl("."))
            importModule("logger", function () {})
        }

        function log(message){
            call("logger.logger.info", [message])
        }

        function error(message){
            call("logger.logger.error", [message])
        }
    }
}
