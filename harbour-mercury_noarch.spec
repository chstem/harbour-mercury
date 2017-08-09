# Prevent brp-python-bytecompile from running
%define __os_install_post %{___build_post}

Name:       harbour-mercury
Summary:    Python based Telegram client for Sailfish OS
Version:    0.1
Release:    1
Group:      Qt/Qt
License:    GPLv3 / MIT
URL:        https://github.com/feodoran/harbour-mercury
Source0:    %{name}-%{version}.tar.bz2
BuildArch:  noarch
Requires:   sailfishsilica-qt5 >= 0.10.9
Requires:   pyotherside-qml-plugin-python3-qt5 >= 1.3.0
Requires:   libsailfishapp-launcher
%description
Mercury is Telegram client for Sailfish OS, based on the Telethon library.

%prep
%setup -q

%build
# Nothing to do

%install
TARGET=%{buildroot}/%{_datadir}/%{name}
rm -rf $TARGET
mkdir -p $TARGET
cp -rpv qml $TARGET/
mkdir -p $TARGET/TgClient
cp -rpv TgClient/*.py $TARGET/TgClient/

if [ -f apikey.a ]; then
    id=`sed -n '1p' < apikey.a`
    hash=`sed -n '2p' < apikey.a`
    sed -i "s/api_id = None/$id/" $TARGET/TgClient/__init__.py
    sed -i "s/api_hash = None/$hash/" $TARGET/TgClient/__init__.py
fi

TARGET=%{buildroot}/%{_datadir}/applications
mkdir -p $TARGET
cp -rpv %{name}_noarch.desktop $TARGET/%{name}.desktop

TARGET=%{buildroot}/%{_datadir}/icons/hicolor/
for res in 86x86 108x108 128x128 256x256; do
    mkdir -p $TARGET/$res/apps/
    cp -rpv icons/$res/%{name}.png $TARGET/$res/apps/
done

%files
%defattr(-,root,root,-)
%{_datadir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
