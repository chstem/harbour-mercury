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
import "../components/messages"
import "../utils.js" as Utils


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

            SilicaListView {
                id: messagesView
                height: page.height //- header.height - (2*Theme.paddingLarge)
                contentHeight: parent.height
                width: parent.width
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Theme.paddingLarge
                verticalLayoutDirection: ListView.BottomToTop
                model: dialogModel

                // footer and header are switched due to ListView.BottomToTop
                footer: Rectangle {
                    width: parent.width
                    height: Theme.itemSizeMedium + 2*Theme.paddingSmall
                    color: Theme.rgba(Theme.secondaryHighlightColor, 1)
                    opacity: 1
                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        x: Theme.paddingLarge
                        spacing: Theme.paddingMedium
                        PeerIcon {
                            id: icon
                            iconSource: currentDialog.icon
                            peerName: currentDialog.title
                            height: Theme.itemSizeMedium
                        }
                        Column {
                            Label {
                                id: label
                                text: currentDialog.title
                                font.bold: true
                            }
                            Label {
                                id: onlineIndicator
                                text: backend.connected ? "connected" : "disconnected"
                                color: backend.connected ? "green" : "red"
                            }
                        }
                   }
                }
                footerPositioning: ListView.OverlayFooter

                delegate: ListItem {
                    z: -1
                    id: delegate
                    contentHeight: item.height
                    Column {
                        id: item
                        height: itemLoader.height + separator.height
                        width: parent.width
                        spacing: Theme.paddingMedium
                        Loader {
                            property alias delegate: delegate
                            id: itemLoader
                            width: parent.width
                        }
                        Separator {
                            id: separator
                            width: parent.width
                            color: Theme.primaryColor
                            horizontalAlignment: Qt.AlignHCenter
                        }
                    }
                    Component.onCompleted: {
                        itemLoader.source = "../components/messages/" + Utils.capitalize(model.type) + "Item.qml"
                    }
                }

                VerticalScrollDecorator { flickable: messagesView }
                onContentYChanged: {
                    if (dialogModel.count > 0 && !requestTimer.running && (dialogModel.count - indexAt(0, contentY) < 10)) {
                        requestTimer.start()
                        backend.fcall('request_messages', [currentDialog.entityID, dialogModel.get(dialogModel.count-1).id])
                    }
                }
            }
        }
    }

    Timer {
        id: requestTimer
        interval: 500
    }

    Component.onCompleted: {
        backend.fcall('request_messages', [currentDialog.entityID])
    }

}

