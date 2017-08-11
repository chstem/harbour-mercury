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
import "../components"

Page {
    id: page
    signal error

    allowedOrientations: Orientation.All

    SilicaFlickable {
        anchors.fill: parent
        contentHeight: column.height

        PullDownMenu {
            MenuItem {
                text: qsTr("Log Out")
                onClicked: {
                    backend.fcall('log_out', [])
                    pageStack.replace(Qt.resolvedUrl("StartPage.qml"), {}, PageStackAction.Immediate)
                }
            }
            MenuItem {
                text: qsTr("Show Contacts")
                onClicked: {
                    pageStack.replace(Qt.resolvedUrl("ContactsPage.qml"))
                }
            }
        }

        Column {
            id: column

            width: parent.width
            spacing: Theme.paddingLarge
            
            PageHeader {
                id: header
                title: qsTr("Chats")
                Label {
                    id: onlineIndicator
                    anchors.verticalCenter: parent.verticalCenter
                    x: Theme.paddingSmall
                    text: backend.connected ? "connected" : "disconnected"
                    color: backend.connected ? "green" : "red"
                }
            }

            SilicaListView {

                id: dialogsView
                height: page.height - header.height - (2*Theme.paddingLarge)
                width: parent.width
                anchors.left: parent.left
                anchors.right: parent.right

                VerticalScrollDecorator { flickable: dialogsView }

                model: dialogsModel

                delegate: ListItem {
                    id: delegate

                    contentHeight: dialog.height + Theme.paddingMedium
                    contentWidth: parent.width

                    Row {

                        id: dialog
                        width: parent.width
                        spacing: Theme.paddingMedium
                        x: Theme.paddingLarge

                        PeerIcon {
                            id: icon
                            iconSource: model.icon
                            peerName: model.name
                            height: 1.5*label.height
                        }

                        Label {
                            id: label
                            anchors.verticalCenter: icon.verticalCenter
                            text: model.name
                            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
                        }

                        Component.onCompleted: {
                            backend.registerIconHandler(entity_id, function(filename) {icon.iconSource = filename})
                        }
                    }

                    onClicked: {
                        currentDialog.entityID = model.entity_id
                        currentDialog.title = model.name
                        currentDialog.icon = model.icon
                        pageStack.push(Qt.resolvedUrl("DialogPage.qml"))
                    }
                }
            }
        }
    }

    onStatusChanged: {
        if (status == PageStatus.Activating) {
            backend.clearDialog()
            backend.fcall('request_dialogs', [])
        }
    }

}

