# Mercury
A Telegram client for Sailfish OS based on the [Telethon](https://github.com/LonamiWebs/Telethon) API

### License

Licensed under GNU GPLv3

### Prerequirements
1. Telethon is not included (yet), so you need to [install](https://github.com/LonamiWebs/Telethon#installing-telethon) it on your Sailfish device:
```
   devel-su
   pip3 install telethon
```
2. [Obtain](https://core.telegram.org/api/obtaining_api_id#obtaining-api-id) an API ID from Telegram
3. Create a file `/home/nemo/.local/share/harbour-mercury/apikey` on the Sailfish device and insert your API ID and API HASH, without the tags `<>`. Avoid using root here.

```
   api_id <ID>
   api_hash <HASH>
```
4. run Mercury using SailfishOS SDK, or copy and run manually:
 - copy the folders `TgClient` and `qml` to `/usr/share/harbour-mercury/` on your SFOS device (requires root)
 - execute `sailfish-qml harbour-mercury` to run
 - optionally, install `harbour-mercury_noarch.desktop` as `/usr/share/applications/harbour-mercury.desktop` and install the `icons` under `/usr/share/icons/hicolor/<resolution>/apps/`

### Why the Name?
I choose the name because it nicely connects a couple of things:

- Mercury is a **messenger** in roman mythology
- Mercurial is a version control system written in **Python**
- being a scientist, I like the connection to the **chemical element** and **planet**
