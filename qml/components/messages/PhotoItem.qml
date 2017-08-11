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
    property real downloaded: mdata.downloaded
    property string media_id: mdata.media_id
    width: parent.width
    contentHeight: column.height

    Column {
        id: column
        width: parent.width - 2*Theme.paddingLarge
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        spacing: Theme.paddingSmall
        x: Theme.paddingLarge

        // Name and Time
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            text: mdata.name + " " + new Date(mdata.time).toLocaleTimeString(Qt.locale(), "HH:mm")
            font.bold: true
            font.pixelSize: Screen.sizeCategory >= Screen.Large ? Theme.fontSizeMedium : Theme.fontSizeNormal
        }

        // Photo
        MouseArea {
            width: parent.width
            height: image.height
            Image {
                id: image
                asynchronous: true
                width: Math.min(parent.width, sourceSize.width)
                height: sourceSize.height / sourceSize.width * width
            }
            ProgressCircle {
                id: progressCircle
                anchors.fill: image
                value: downloaded
                visible: value > 0 & value < 1
            }
            onClicked: {
                if (downloaded == 1) {
                    pageStack.push(Qt.resolvedUrl("../../pages/ImagePage.qml"), {source:mdata.filename})
                } else {
                    downloaded = 0.0001
                    backend.fcall("download", [mdata.media_id])
                }
            }
        }

        // Caption
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            visible: mdata.caption.length > 0
            text: qsTr("Photo") + ": " + mdata.caption
            wrapMode: Text.Wrap
            font.pixelSize: Screen.sizeCategory >= Screen.Large ? Theme.fontSizeMedium : Theme.fontSizeNormal
        }
    }

    onDownloadedChanged: {
        if (downloaded === 1.0) {
            delayPhoto.start()
        }
    }

    Timer {
        id: delayPhoto
        interval: 500
        onTriggered: {
            if (downloaded === 1.0) {
                image.source = mdata.filename
            } else {
                image.source = "image://theme/icon-m-cloud-download"
            }
        }
    }

    Component.onCompleted: {
        backend.registerProgressHandler(media_id, function (progress) {
            downloaded = progress
        })
        delayPhoto.start()
    }
}
