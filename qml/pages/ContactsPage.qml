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
                    backend.fcall('log_out', [])
                    pageStack.replace(Qt.resolvedUrl("StartPage.qml"), {}, PageStackAction.Immediate)
                }
            }
            MenuItem {
                text: qsTr("Show Chats")
                onClicked: {
                    pageStack.replace(Qt.resolvedUrl("DialogsPage.qml"), {})
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
                title: qsTr("Contacts")
            }

            SilicaListView {

                id: contactsView
                height: page.height - header.height - (2*Theme.paddingLarge)
                width: parent.width
                anchors.left: parent.left
                anchors.right: parent.right

                VerticalScrollDecorator { flickable: contactsView }

                model: contactsModel

                delegate: ListItem {
                    id: delegate

                    contentHeight: contact.height + Theme.paddingMedium
                    contentWidth: parent.width

                    Row {
                        id: contact
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
                        console.log(name)
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        backend.fcall('request_contacts', [])
    }
}

