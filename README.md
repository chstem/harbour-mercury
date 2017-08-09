# Mercury

A Telegram client for Sailfish OS based on the [Telethon](https://github.com/LonamiWebs/Telethon) API

### License

Licensed under GNU GPLv3

### Prerequirements

1. Telethon is not included (yet), so you need to [install](https://github.com/LonamiWebs/Telethon#installing-telethon) it on your Sailfish device:

```bash
devel-su
pip3 install telethon
exit
```

2. [Obtain](https://core.telegram.org/api/obtaining_api_id#obtaining-api-id) an API ID from Telegram
3. Create a file `/home/nemo/.local/share/harbour-mercury/apikey` on the Sailfish device and insert your API ID and API HASH, without the tags
`<>` (Avoid being root here!):

```bash
cat <<EOF > /home/nemo/.local/share/harbour-mercury/apikey 
api_id <ID>
api_hash <HASH>
EOF
```

4. Run Mercury using SailfishOS SDK, or copy and run manually:

- Copy the folders `TgClient` and `qml` to `/usr/share/harbour-mercury/` on your SFOS device (requires root)

```bash
cd /home/nemo/Downloads
git clone https://github.com/feodoran/harbour-mercury.git
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

### Why the Name?

I choose the name because it nicely connects a couple of things:

- Mercury is a **messenger** in roman mythology
- Mercurial is a version control system written in **Python**
- being a scientist, I like the connection to the **chemical element** and **planet**
