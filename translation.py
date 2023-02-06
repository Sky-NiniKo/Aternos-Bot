# Auto generate embed from i18n files
from pathlib import Path
from typing import Any

from discord import Embed, Colour

embeds: dict[str, dict[str, Any]] = {}
i18n_dir = Path("i18n")
universal_colour = Colour(0x386cbc)
translation = {}  # translation is never reset but that should give auto fallback, kinda because not consistent
exposed = (
    "launch_bot",
    "bot_ready",
    "start_server_name",
    "start_server_description",
    "get_countdown_name",
    "get_countdown_description",
    "players_name",
    "players_description",
    "tps_title",
    "tps_description",
    "ping_name",
    "ping_description",
    "server_ip_name",
    "server_ip_description",
    "get_code_name",
    "get_code_description",
)


def expose(name: str):
    embeds[language][name] = translation.get(name)


def embed_builder(name: str, **embed_kwargs):
    title = translation.get(f"{name}_title")
    primary_description = translation.get(f"{name}_description")
    other_description = translation.get(f"{name}_description_other") or primary_description

    def build(set_other_description=False, **kwargs) -> Embed:
        description = other_description if set_other_description else primary_description
        thumbnail = kwargs.pop("thumbnail", None) or embed_kwargs.pop("thumbnail", None)
        author = kwargs.pop("author", None) or embed_kwargs.pop("author", None)
        footer = kwargs.pop("footer", None) or embed_kwargs.pop("footer", None)
        colour = kwargs.pop("colour", None) or embed_kwargs.pop("colour", None)
        timestamp = kwargs.pop("timestamp", None)

        embed = Embed(
            title=title.format(**kwargs) if title else None,
            description=description.format(**kwargs) if description else None,
            timestamp=timestamp,
            colour=colour,
        )

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if author:
            embed.set_author(**author)
        if footer:
            if isinstance(footer, dict):
                embed.set_footer(**footer)
            else:
                embed.set_footer(text=footer)

        return embed

    embeds[language][name] = build


for folder in i18n_dir.glob("*"):
    if not folder.is_dir():
        continue

    language = folder.name
    embeds[language] = {}

    with open(folder / "translation.txt", "r+") as file:
        for line in file:
            if line.find("=") == -1 or line.startswith("#"):
                continue
            key, *text = line.split("=")
            translation[key] = "=".join(text).replace("\\n", "\n")[:-1]

    for value in exposed:
        expose(value)

    embed_builder("starting", colour=universal_colour,
                  thumbnail="https://cdn.dribbble.com/users/1092116/screenshots/2857934/loading-indicator-dribbble2.gif")
    embed_builder("already_starting", colour=universal_colour,
                  thumbnail="https://icon-icons.com/icons2/1283/PNG/512/1497619898-jd24_85173.png")
    embed_builder("started_already", colour=universal_colour)
    embed_builder("countdown", colour=universal_colour)
    embed_builder("no_countdown", colour=universal_colour)
    embed_builder("present_players", colour=universal_colour, thumbnail="https://aternos.org/favicon.ico")
    embed_builder("no_players", colour=universal_colour,
                  thumbnail="https://whatemoji.org/wp-content/uploads/2020/07/Desert-Emoji.png")
    embed_builder("current_tps", colour=universal_colour, thumbnail="https://aternos.org/favicon.ico")
    embed_builder("no_tps_info", colour=universal_colour,
                  thumbnail="https://cdn.shopify.com/s/files/1/1061/1924/products/Emoji_Icon_-_Sad_Emoji_large.png")
    embed_builder("ping", colour=universal_colour, thumbnail="https://freesvg.org/img/paddle.png")
    embed_builder("server_ip", colour=universal_colour)
    embed_builder("server_has_started", colour=universal_colour,
                  thumbnail="https://openclipart.org/image/800px/svg_to_png/219326/1432343177.png")

if __name__ == '__main__':
    from pprint import pprint

    """embeds = {
        lang: {key: embed()
               for key, embed in trans.items()}
        for lang, trans in embeds.items()
    }"""
    pprint(embeds)
