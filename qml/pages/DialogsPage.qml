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

    allowedOrientations: Orientation.All

    SilicaFlickable {

        PullDownMenu {
            MenuItem {
                text: qsTr("Log Out")
                onClicked: {
                    telegram.fcall('log_out', [])
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

        anchors.fill: parent
        contentHeight: column.height

        Column {
            id: column

            width: parent.width
            spacing: Theme.paddingLarge
            
            PageHeader {
                id: header
                title: qsTr("Chats")
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
                        Label {
                            text: model.name
                            anchors.verticalCenter: parent.verticalCenter
                            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
                        }
                    }

                    onClicked: {
                        currentDialog.entityID = entity_id
                        currentDialog.title = name
                        pageStack.push(Qt.resolvedUrl("DialogPage.qml"))
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        currentDialog.entityID = ""
        currentDialog.title = ""
        telegram.fcall('request_dialogs', [])
    }
}

