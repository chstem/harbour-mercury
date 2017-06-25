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
*/

import QtQuick 2.0
import Sailfish.Silica 1.0

ListItem {
    id: delegate

    property alias mediaItem: mediaLoader.item

    contentHeight: dialog.height + Theme.paddingMedium
    contentWidth: parent.width

    Column {
        id: dialog
        width: parent.width - 2*Theme.paddingLarge
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        spacing: Theme.paddingMedium
        x: Theme.paddingLarge

        // Name and Time
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            text: name + " " + new Date(time).toLocaleTimeString(Qt.locale(), "HH:mm")
            font.bold: true
        }

        // Message
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            visible: message.length > 0
            text: message
            wrapMode: Text.Wrap
        }

        // Media
        Loader {
            id: mediaLoader
            width: parent.width
        }

        // Photo
        Component {
            id: photoItem
            Column {
                property real downloaded: media_data.downloaded
                MouseArea {
                    width: parent.width
                    height: image.height
                    Image {
                        id: image
                        asynchronous: true
                        width: Math.min(parent.width, sourceSize.width)
                        height: sourceSize.height / sourceSize.width * width
                        source: downloaded == 1 ? media_data.filename : "image://theme/icon-m-cloud-download"
                    }
                    ProgressCircle {
                        id: progressCircle
                        anchors.fill: image
                        value: downloaded
                        visible: value > 0 & value < 1
                    }
                    onClicked: {
                        if (downloaded == 1) {
                            pageStack.push(Qt.resolvedUrl("../pages/ImagePage.qml"), {source:media_data.filename})
                        } else {
                            downloaded = 0.0001
                            telegram.fcall("download", [media_data.media_id])
                        }
                    }
                }
                Text {
                    width: parent.width
                    color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
                    text: qsTr("Photo") + ": " + media_data.caption
                    wrapMode: Text.Wrap
                }
            }
        }

        Component {
            id: docItem
            Column {
                property real downloaded: media_data.downloaded
                IconButton {
                    id: iconButton
                    icon.source: downloaded == 1 ? "image://theme/icon-m-document" : "image://theme/icon-m-cloud-download"
                    onClicked: {
                        if (downloaded == 1) {
                            Qt.openUrlExternally(media_data.filename)
                        } else {
                            downloaded = 0.0001
                            telegram.fcall("download", [media_data.media_id])
                        }
                    }
                    ProgressCircle {
                        id: progressCircle
                        anchors.fill: iconButton
                        value: downloaded
                        visible: value > 0 & value < 1
                    }
                }
                Text {
                    width: parent.width
                    color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
                    text: qsTr("File") + ": " + media_data.caption
                    wrapMode: Text.Wrap
                }
            }
        }
    }

    Component.onCompleted: {
        if (model.media === "document") {
            mediaLoader.sourceComponent = docItem
        } else if (model.media === "photo") {
            mediaLoader.sourceComponent = photoItem
        }
    }
}
