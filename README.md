[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c1dfefa74f484845974c03b186c4fb84)](https://www.codacy.com/gh/Sky-NiniKo/Aternos-Bot/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Sky-NiniKo/Aternos-Bot&amp;utm_campaign=Badge_Grade)
![License](https://img.shields.io/github/license/Sky-NiniKo/Aternos-Bot)
![Code size in bytes](https://img.shields.io/github/languages/code-size/Sky-NiniKo/Aternos-Bot)
![Repo size](https://img.shields.io/github/repo-size/Sky-NiniKo/Aternos-Bot)
![Lines of code](https://img.shields.io/tokei/lines/github/Sky-NiniKo/Aternos-Bot)
![Last commit](https://img.shields.io/github/last-commit/Sky-NiniKo/Aternos-Bot)

## Aternos-Bot
 Python Discord bot for [Aternos](https://aternos.org/) minecraft servers

### Installation
```bash
git clone https://github.com/Sky-NiniKo/Aternos-Bot.git
cd Aternos-Bot
pipenv sync
```

### Configuration
Create a `.env` file in Aternos-Bot folder.
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

-   **ATERNOS_USER**: Required. Aternos account user.

-   **ATERNOS_PASSWORD**: Required. Aternos account password.

-   **OWNER**: Optional. ID of your Discord account for sending notifications thought Discord.

-   **CURSEFORGE_API_KEY**: No utility for now. API key for Curseforge.
[Get one](https://console.curseforge.com/?#/api-keys).
### Run
```bash
# pipenv shell
python main.py
```


### Possible future improvements
- Multiple servers
- Console channel
- Real support for translation
- Send in a discord channel update changelog of the sowftware running on Aternos
