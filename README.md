# Mercury

A Telegram client for Sailfish OS based on the [Telethon](https://github.com/LonamiWebs/Telethon) API

### License

Licensed under GNU GPLv3

### Prerequirements

1. Telethon is not included (yet), so you need to [install](https://github.com/LonamiWebs/Telethon#installing-telethon) it on your Sailfish device. Telethon is under active development and occasionally breaks backward compatibility, so make sure to use the correct version:

```bash
devel-su
pip3 install telethon=0.15.5
exit
```

2. [Obtain](https://core.telegram.org/api/obtaining_api_id#obtaining-api-id) an API ID from Telegram
3. Create a file `/home/nemo/.local/share/harbour-mercury/apikey` on the Sailfish device and insert your API ID and API HASH, without the tags
`<>` (Avoid being root here!):

```bash
mkdir -p /home/nemo/.local/share/harbour-mercury
cat <<EOF > /home/nemo/.local/share/harbour-mercury/apikey
api_id <ID>
api_hash <HASH>
EOF
```

4. Run Mercury using SailfishOS SDK, or copy and run manually:

- Copy the folders `TgClient` and `qml` to `/usr/share/harbour-mercury/` on your SFOS device (requires root)

```bash
cd /home/nemo/Downloads
git clone https://github.com/chstem/harbour-mercury.git
devel-su
mkdir /usr/share/harbour-mercury
cd /home/nemo/Downloads/harbour-mercury/
cp -r TgClient qml /usr/share/harbour-mercury/
exit
```

- Run Mercury:

```bash
sailfish-qml harbour-mercury
```

- Optionally, install `harbour-mercury_noarch.desktop` as `/usr/share/applications/harbour-mercury.desktop` and install the `icons` under `/usr/share/icons/hicolor/<resolution>/apps/`

### Performance Issues

- The connection to the Telegram servers is AES encrypted. If available, `libssl.so` will be used, otherwise a pure Python AES implementation serves as fallback. However, on mobile processors, this severely slows down network speed. If you experience slow download speed, make sure OpenSSL is installed:

```bash
devel-su
pkcon install openssl
```

### Why the Name?

I choose the name because it nicely connects a couple of things:

- Mercury is a **messenger** in roman mythology
- Mercurial is a version control system written in **Python**
- being a scientist, I like the connection to the **chemical element** and **planet**
