# NOTICE:
#
# Application name defined in TARGET has a corresponding QML filename.
# If name defined in TARGET is changed, the following needs to be done
# to match new name:
#   - corresponding QML filename must be changed
#   - desktop icon filename must be changed
#   - desktop filename must be changed
#   - icon definition filename in desktop file must be changed
#   - translation filenames have to be changed

# The name of your application
TARGET = harbour-mercury

CONFIG += sailfishapp

SOURCES += src/harbour-mercury.cpp

OTHER_FILES += rpm/harbour-mercury.changes.in \
    rpm/harbour-mercury.spec \
    rpm/harbour-mercury.yaml \
    translations/*.ts \
    harbour-mercury.desktop
+
SAILFISHAPP_ICONS = 86x86 108x108 128x128 256x256

# to disable building translations every time, comment out the
# following CONFIG line
CONFIG += sailfishapp_i18n

# German translation is enabled as an example. If you aren't
# planning to localize your app, remember to comment out the
# following TRANSLATIONS line. And also do not forget to
# modify the localized app name in the the .desktop file.
TRANSLATIONS += translations/harbour-mercury-de.ts

TgClient.path = /usr/share/harbour-mercury/TgClient
TgClient.files = TgClient/*

INSTALLS += TgClient

DISTFILES += \
    qml/harbour-mercury.qml \
    qml/Telethon.qml \
    qml/pages/StartPage.qml \
    qml/pages/ConnectPage.qml \
    qml/pages/CodePage.qml \
    qml/pages/PasswordPage.qml \
    qml/pages/DialogsPage.qml \
    qml/pages/DialogPage.qml \
    qml/pages/ContactsPage.qml \
    qml/pages/ImagePage.qml \
    qml/components/AppNotification.qml \
    qml/components/AppNotificationItem.qml \
    qml/components/MessageItem.qml
