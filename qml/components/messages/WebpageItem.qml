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

        // Title
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            text: mdata.title
            wrapMode: Text.Wrap
            font.pixelSize: Screen.sizeCategory >= Screen.Large ? Theme.fontSizeMedium : Theme.fontSizeNormal
        }

        // URL
        Text {
            width: parent.width
            color: delegate.highlighted ? Theme.highlightColor : Theme.primaryColor
            text: mdata.url
            wrapMode: Text.Wrap
            font.pixelSize: Screen.sizeCategory >= Screen.Large ? Theme.fontSizeMedium : Theme.fontSizeNormal
        }
    }

}
