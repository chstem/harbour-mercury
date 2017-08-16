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
import QtGraphicalEffects 1.0
import Sailfish.Silica 1.0
import "../utils.js" as Utils

Item {
    property string iconSource
    property string peerName
    width: height

    Loader {
        id: iconLoader
        height: parent.height
        width: height
        sourceComponent: (iconSource === "") ? initials : icon
    }

    Component {
        id: initials
        Rectangle {
            height: iconLoader.height
            width: height
            radius: width*0.5
            color: "steelblue"
            Text {
                anchors.centerIn: parent
                color: "white"
                text: Utils.get_initials(peerName)
                font.bold: true
                font.pixelSize: radius
            }
        }
    }

    Component {
        id: icon
        Image {
            id: image
            height: iconLoader.height
            width: height
            source: iconSource
            layer.enabled: true
            layer.effect: OpacityMask {
                maskSource: Item {
                    width: image.width
                    height: image.height
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width
                        height: parent.height
                        radius: width
                    }
                }
            }
        }
    }

}
