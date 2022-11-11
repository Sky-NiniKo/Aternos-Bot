[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c1dfefa74f484845974c03b186c4fb84)](https://www.codacy.com/gh/Sky-NiniKo/LAG-Bot/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Sky-NiniKo/LAG-Bot&amp;utm_campaign=Badge_Grade)
![License](https://img.shields.io/github/license/Sky-NiniKo/LAG-Bot)
![Code size in bytes](https://img.shields.io/github/languages/code-size/Sky-NiniKo/LAG-Bot)
![Repo size](https://img.shields.io/github/repo-size/Sky-NiniKo/LAG-Bot)
![Lines of code](https://img.shields.io/tokei/lines/github/Sky-NiniKo/LAG-Bot)
![Last commit](https://img.shields.io/github/last-commit/Sky-NiniKo/LAG-Bot)

## LAG-Bot
 Python Discord bot for [Aternos](https://aternos.org/) minecraft servers

### Installation
```bash
git clone https://github.com/Sky-NiniKo/Aternos-Bot.git
cd LAG-Bot
pipenv sync
playwright install
```
-   Download [uBlock Origin](https://github.com/gorhill/uBlock/releases/download/1.40.8/uBlock0_1.40.8.chromium.zip) 
unzip it and place uBlock0.chromium in aternos folder. Or you can use the start.sh.

### Configuration
Create a `.env` file in LAG-Bot folder.
```dotenv
DISCORD_BOT_TOKEN=your_token
OWNER=your_discord_id
ATERNOS_USER=your_aternos_user
ATERNOS_PASSWORD=your_aternos_password
MODPACK=server_modpack
CURSEFORGE_API_KEY=your_curseforge_key
CHANNEL_MODPACK_UPDATE=channel_id
```
-   **DISCORD_BOT_TOKEN**: Required. Token of your Discord bot.
[Get one](https://discord.com/developers/applications).

-   **OWNER**: ID of your Discord account for sending notifications thought Discord.

-   **ATERNOS_USER**: Required. Aternos account user.

-   **ATERNOS_PASSWORD**: Required. Aternos account password.

-   **MODPACK**: Curseforge ID of the modpack installed on your server.

-   **CURSEFORGE_API_KEY**: Required if you set MODPACK. API key for Curseforge.
[Get one](https://console.curseforge.com/?#/api-keys).

-   **CHANNEL_MODPACK_UPDATE**: Required if you set MODPACK.
Discord channel ID where the bot send notification of modpack update.

### Run
```bash
python main.py
```
You need to delete `aternos/tmp/test-user-data-dir` every time its start. If you are on linux you can also use 
`bash start.sh` to do that automatically
