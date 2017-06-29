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


Page {
    id: page
    signal error

    allowedOrientations: Orientation.All

    SilicaFlickable {
        anchors.fill: parent
        contentHeight: column.height

        Column {
            id: column

            width: parent.width
            spacing: Theme.paddingLarge
            PageHeader {
                title: qsTr("Log In")
            }

            Text {
                width: parent.width - 2*Theme.paddingMedium
                x: Theme.paddingMedium
                color: Theme.primaryColor
                text: qsTr("Please enter your phone number in international format.")
                wrapMode: Text.Wrap
            }

            TextField {
                id: number
                width: parent.width
                focus: true
                label: qsTr("phone number")
                placeholderText: label
                color: Theme.secondaryHighlightColor
                font.pixelSize: Theme.fontSizeExtraLarge
                inputMethodHints: Qt.ImhDigitsOnly
                EnterKey.iconSource: "image://theme/icon-m-enter-next"
                EnterKey.onClicked: connect()
            }

            Button {
                text : "Connect"
                anchors.horizontalCenter: parent.horizontalCenter
                onClicked: connect()
            }
        }
    }

    function connect() {
        backend.fcall('request_code', [number.text])
        pageStack.replace(Qt.resolvedUrl("CodePage.qml"))
    }

}

