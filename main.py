import asyncio
import json
import time
import os
from random import randint

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from colour import Color

from aternos.aternos import AternosAccount, AvailableTypes, enum2condition
from translation import embeds

start = time.time()

load_dotenv()

LANGUAGE = "fr_FR"
translation = embeds.get(LANGUAGE)
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_KEY = os.getenv("CURSEFORGE_API_KEY")
ATERNOS_USER = os.getenv("ATERNOS_USER")
ATERNOS_PASSWORD = os.getenv("ATERNOS_PASSWORD")
OWNER = os.getenv("OWNER")

aternos = AternosAccount(user=ATERNOS_USER, password=ATERNOS_PASSWORD)
server = aternos.servers[0]
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

if OWNER:
    bot.owner_id = OWNER

to_notify = {}
updater_start_activity = None


@bot.tree.command(
    name=translation["start_server_name"],
    description=translation["start_server_description"],
)
@app_commands.describe(send_message="Vous envoie un message quand le serveur a terminer de démarrer")
async def start_server(interaction: discord.Interaction, send_message: bool = True):
    current_status = server.get_info()["status"]

    if current_status != 0:
        if current_status == 2 or current_status >= 6 and send_message:
            embed_builder = translation["already_starting"]

            if send_message and interaction.user not in to_notify.get(interaction.channel.id, []):
                to_notify.get(interaction.channel.id).append(interaction.user)
        else:
            embed_builder = translation["started_already"]

        return await interaction.response.send_message(embed=embed_builder())

    embed_builder = translation["starting"]
    await interaction.response.send_message(embed=embed_builder(set_other_description=send_message))
    if send_message:
        to_notify[interaction.channel.id] = [interaction.user]
    server.start()


@bot.tree.command(
    name=translation["get_countdown_name"],
    description=translation["get_countdown_description"],
)
async def get_countdown(interaction: discord.Interaction):
    info = server.get_info()
    seconds = server.get_countdown()
    embed_builder = translation["countdown"] if seconds else translation["no_countdown"]
    seconds -= bot.latency

    await interaction.response.send_message(
        embed=embed_builder(
            minutes=seconds // 60,
            seconds=seconds % 60,
            author=dict(name=info['name'], icon_url="https://aternos.org/favicon.ico")
        )
    )


@bot.tree.command(
    name=translation["players_name"],
    description=translation["players_description"],
)
async def players(interaction: discord.Interaction):
    info = server.get_info()
    if info['playerlist']:
        embed = translation["present_players"](
            present_players="\n".join(info['playerlist']),
            author=dict(name=info['name']),
            footer=f"{info['players']['current']}/{info['players']['max']}"
        )
    else:
        embed = translation["no_players"](
            author=dict(name=info['name'], icon_url=bot.user.display_avatar)
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name=translation["tps_name"],
    description=translation["tps_description"],
)
async def tps(interaction: discord.Interaction):
    info = server.get_info()

    if tick_info := server.get_tps():
        tps_number = tick_info["tps"]

        def interpolation(start_value, end_value, current, max_value):
            return (end_value - start_value) * current / max_value + start_value

        red = Color("#B93127")
        green = Color("#27B938")

        color = int(
            Color(
                hsl=[interpolation(r, g, min(tps_number, 20), 20) for r, g in zip(red.hsl, green.hsl)]
            ).hex[1:], 16  # convert back in int
        )

        embed = translation["current_tps"](
            tps_number=round(tps_number, 1),
            mspt=round(tick_info["mspt"], 1),
            colour=color,
            author=dict(name=info['name'])
        )
    else:
        embed = translation["no_tps_info"](
            author=dict(name=info['name'], icon_url=bot.user.display_avatar.url)
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name=translation["tps_title"],
    description=translation["tps_description"],
)
async def ping(interaction: discord.Interaction):
    embed = translation["ping"](
        latency=round(bot.latency * 1000, 2)
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name=translation["server_ip_name"],
    description=translation["server_ip_description"],
)
async def ip(interaction: discord.Interaction):
    info = server.get_info()
    embed = translation["server_ip"](
        ip=info['ip'],
        port=info['port']
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name=translation["get_code_name"],
    description=translation["get_code_description"],
)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message("https://github.com/Sky-NiniKo/Aternos-Bot")


@bot.command()
async def broadcast(ctx, *text):
    if not await bot.is_owner(ctx.author):
        return

    def changes(arg):
        return "\n" if arg == r"\n" else arg

    await ctx.send(" ".join(map(changes, text)))


@tasks.loop(minutes=30)
async def check_new_version():
    # send message for updated modpack in discord
    # currently not implemented
    pass


async def activity(status):
    global to_notify
    global updater_start_activity

    if updater_start_activity:
        updater_start_activity.cancel()

    info = json.loads(status["message"])

    match info['status']:
        case 0:
            await bot.change_presence(activity=discord.Activity(type=3, name="si quelqu'un démarre le serveur"))
        case 1:
            if server.get_countdown() is None:
                await bot.change_presence(activity=discord.Game(name=info['name']))
            else:
                updater_start_activity = asyncio.get_event_loop().create_task(
                    update_start_activity(info, server.get_countdown())
                )

            if not to_notify:
                return

            for channel_id in to_notify:
                channel = await bot.fetch_channel(channel_id)
                await channel.send(
                    content=' '.join(map(lambda user: user.mention, to_notify[channel_id])),
                    embed=translation['server_has_started']()
                )
            to_notify = {}
        case 2:
            await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur qui démarre"))
        case 3:
            await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur qui s'arrête"))
        case 5:
            await bot.change_presence(activity=discord.Activity(type=3, name="le monde se sauvegarder"))
        case 6:
            await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur crasher"))
        case 7:
            await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur crasher"))
            server.start()
        case 10:
            await bot.change_presence(activity=discord.Activity(type=3, name="les préparatifs se finir"))
        case _:
            print(info)
            if bot.owner_id:
                owner = await bot.fetch_user(bot.owner_id)
                await owner.send(content=f"Nouveau cas détecter {info['status']}: {info['label']}")


def synchronous_activity(*args, **kwargs):
    return asyncio.run(activity(*args, **kwargs))


async def update_start_activity(info: dict, countdown_seconds: int):
    await asyncio.sleep(countdown_seconds % 30)
    for countdown in reversed(range(30, countdown_seconds, 30)):
        await asyncio.gather(
            asyncio.sleep(30),
            bot.change_presence(
                activity=discord.Game(name=f"{info['name']} {countdown // 60}:{countdown % 60:02} avant arrêt")),
        )


@bot.event
async def on_ready():
    print(translation["bot_ready"].format(
        name=bot.user.name,
        start_time=round(time.time() - chrono, 3),
        total_time=round(time.time() - start, 3))
    )

    server.subscribe(synchronous_activity, enum2condition(AvailableTypes.STATUS))

    """try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)"""


chrono = time.time()
print(translation["launch_bot"].format(
    pre_start_time=round(time.time() - start, 3))
)
bot.run(TOKEN)
