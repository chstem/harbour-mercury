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
            text: model.name + " " + new Date(model.time).toLocaleTimeString(Qt.locale(), "HH:mm")
            font.bold: true
        }

        // Message
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            visible: model.message.length > 0
            text: model.message
            wrapMode: Text.Wrap
        }

        // Photo +  Caption
        Image {
            asynchronous: true
            width: Math.min(parent.width, sourceSize.width)
            height: sourceSize.height / sourceSize.width * width
            visible: model.media === 'photo' ? true : false
            source: visible ? model.filename : ''
        }
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            visible: model.media === 'photo' ? true : false
            text: visible ? model.caption : ''
            wrapMode: Text.Wrap
        }
    }
}
