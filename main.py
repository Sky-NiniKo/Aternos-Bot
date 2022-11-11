import asyncio
import time
import os
from random import randint

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from colour import Color

from aternos.aternos import Aternos
from curseforge.curseforge_basic_api import CurseForgeAPI

start = time.time()

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_KEY = os.getenv("CURSEFORGE_API_KEY")
ATERNOS_USER = os.getenv("ATERNOS_USER")
ATERNOS_PASSWORD = os.getenv("ATERNOS_PASSWORD")
MODPACK = os.getenv("MODPACK")
CHANNEL_MODPACK_UPDATE = os.getenv("CHANNEL_MODPACK_UPDATE")
OWNER = os.getenv("OWNER")


aternos = Aternos(user=ATERNOS_USER, password=ATERNOS_PASSWORD)
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

if MODPACK:
    curseforge = CurseForgeAPI(api_key=API_KEY)
    curseforge.track_mod(MODPACK)

if OWNER:
    bot.owner_id = OWNER

to_notify = {}
updater_start_activity = None


@bot.tree.command(
    name="start",
    description="Démarre le serveur Minecraft",
)
@app_commands.describe(send_message="Vous envoie un message quand le serveur a terminer de démarrer")
async def start_server(interaction: discord.Interaction, send_message: bool = True):
    current_status = (await aternos.get_info())["status"]

    if current_status != 0:
        if current_status == 2 or current_status >= 6 and send_message:
            embed = discord.Embed(title="Le serveur démarre déjà !", colour=discord.Colour(0x386cbc),
                                  description="On vous rajoute à la liste des gens à prévenir\n quand il aura démarrer")

            embed.set_thumbnail(url="https://icon-icons.com/icons2/1283/PNG/512/1497619898-jd24_85173.png")

            await interaction.response.send_message(embed=embed)

            if send_message and interaction.user not in to_notify.get(interaction.channel.id, []):
                to_notify.get(interaction.channel.id, []).append(interaction.user)
        else:
            embed = discord.Embed(title="Impossible de démarrer le serveur", colour=discord.Colour(0x386cbc),
                                  description="Il faut qu'il soit éteint")

            await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(title="Démarrage du serveur en cours", colour=discord.Colour(0x386cbc),
                          description="Cela peut prendre un moment" +
                                      ' mais on vous\nenverra un message quand ce sera fini 😉' if send_message else ''
                          )

    embed.set_thumbnail(
        url="https://cdn.dribbble.com/users/1092116/screenshots/2857934/loading-indicator-dribbble2.gif")

    await interaction.response.send_message(embed=embed)
    if send_message:
        to_notify[interaction.channel.id] = [interaction.user]
    await aternos.start()


@bot.tree.command(
    name="timer",
    description="Donne le nombre exacte de secondes avant le fermeture automatique du serveur",
)
async def get_countdown(interaction: discord.Interaction):
    info = await aternos.get_info()
    seconds = await aternos.get_countdown()
    if seconds:
        embed = discord.Embed(title=f"Le serveur va se fermer dans {seconds // 60}:{seconds % 60:02}",
                              colour=discord.Colour(0x386cbc), description="Si personne ne se connecte bien sûr")

        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.set_author(name=info['name'])
    else:
        embed = discord.Embed(title="Pas de fermeture automatique prévue", colour=discord.Colour(0x386cbc))
        embed.set_author(name=info['name'], icon_url=bot.user.avatar_url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="joueurs",
    description="Renvoie les joueurs qui sont connecter sur le serveur",
)
async def players(interaction: discord.Interaction):
    info = await aternos.get_info()
    if info['playerlist']:
        embed = discord.Embed(title="Joueurs présents", colour=discord.Colour(0x386cbc),
                              description="\n".join(info['playerlist']))

        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.set_author(name=info['name'])
        embed.set_footer(text=f"{info['players']['current']}/{info['players']['max']}")
    else:
        embed = discord.Embed(title="C'est le desert", colour=discord.Colour(0x386cbc),
                              description="Aucun joueur n'est connecter")

        embed.set_thumbnail(url="https://whatemoji.org/wp-content/uploads/2020/07/Desert-Emoji.png")
        embed.set_author(name=info['name'], icon_url=bot.user.display_avatar)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="tps",
    description="Renvoie le nombre de tps actuelle du serveur",
)
async def tps(interaction: discord.Interaction):
    info = await aternos.get_info()

    if tps_number := await aternos.get_tps():
        if tps_number > 20:
            color = 0x27b938
        else:
            def interpolation(start_value, end_value, current, max_value):
                return (end_value - start_value) * current / max_value + start_value

            red = Color("#B93127")
            green = Color("#27B938")

            color = int(
                Color(hsl=[interpolation(r, g, tps_number, 20) for r, g in zip(red.hsl, green.hsl)]).hex[1:], 16)

        embed = discord.Embed(title=f"Le serveur tourne a {tps_number} tps", colour=color,
                              description="L'objectif c'est 20")
        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.set_author(name=info['name'])
    else:
        embed = discord.Embed(title="Les tps ne sont pas disponible.", colour=discord.Colour(0x386cbc),
                              description="Réessayer quand le serveur est allumer")

        embed.set_thumbnail(url="https://cdn.shopify.com/s/files/1/1061/1924/products/Emoji_Icon_-_Sad_Emoji_large.png")
        embed.set_author(name=info['name'], icon_url=bot.user.avatar_url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="ping",
    description="Donne le ping que a le bot avec les serveurs Discord",
)
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(title="Pong !", colour=discord.Colour(0x386cbc),
                          description=f"Latence :\n{round(bot.latency * 1000, 2)} ms")

    embed.set_thumbnail(url="https://freesvg.org/img/paddle.png")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="ip",
    description="Donne l'IP pour se connecter au serveur",
)
async def ip(interaction: discord.Interaction):
    info = await aternos.get_info()
    embed = discord.Embed(title=f"Pour vous connecter utiliser {info['ip']}:{info['port']}",
                          colour=discord.Colour(0x386cbc))

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="code",
    description="Donne le lien du GitHub",
)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message("https://github.com/Sky-NiniKo/LAG-Bot")


@bot.command()
async def broadcast(ctx, *text):
    if not await bot.is_owner(ctx.author):
        return

    def changes(arg):
        return "\n" if arg == r"\n" else arg

    await ctx.send(" ".join(map(changes, text)))


@tasks.loop(minutes=30)
async def check_new_version():
    if not MODPACK:
        return

    if curseforge.is_a_new_version():
        channel = bot.fetch_channel(CHANNEL_MODPACK_UPDATE)
        await channel.send(
            f"Une nouvelle version du modpack est sortie : **{curseforge.get_last_file()['displayName']}** !\n"
            f"{curseforge.get_file_changelog(curseforge.get_last_file()['id'])}")


async def activity(info):
    global to_notify
    global updater_start_activity

    if updater_start_activity:
        updater_start_activity.cancel()

    if info['status'] == 0:
        await bot.change_presence(activity=discord.Activity(type=3, name="si quelqu'un démarre le serveur"))
    elif info['status'] == 1:
        if to_notify:
            embed = discord.Embed(title="Le serveur a démarrer !", colour=discord.Colour(0x386cbc),
                                  description="Qu'est que vous attendez ?\nConnecter vous !")
            embed.set_thumbnail(url="https://openclipart.org/image/800px/svg_to_png/219326/1432343177.png")

            for channel_id in to_notify:
                channel = await bot.fetch_channel(channel_id)
                await channel.send(content=' '.join(map(lambda user: user.mention, to_notify[channel_id])), embed=embed)
            to_notify = {}

        if info['countdown'] is None:
            await bot.change_presence(activity=discord.Game(name=info['name']))
        else:
            updater_start_activity = asyncio.get_event_loop().create_task(update_start_activity(info))
    elif info['status'] == 2:
        await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur qui démarre"))
    elif info['status'] == 3:
        await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur qui s'arrête"))
    elif info['status'] == 5:
        await bot.change_presence(activity=discord.Activity(type=3, name="le monde se sauvegarder"))
    elif info['status'] == 6:
        await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le chargement"))
    elif info['status'] == 7:
        await bot.change_presence(activity=discord.Activity(type=randint(2, 3), name="le serveur crasher"))
        await aternos.start()
    elif info['status'] == 10:
        await bot.change_presence(activity=discord.Activity(type=3, name="les préparatifs se finir"))
    else:
        print(info)
        if bot.owner_id:
            owner = bot.fetch_user(bot.owner_id)
            await owner.send(content=f"Nouveau cas détecter {info['status']}: {info['label']}")


async def update_start_activity(info):
    for countdown in reversed(range(30, info['countdown'], 30)):
        await asyncio.gather(
            asyncio.sleep(30),
            bot.change_presence(
                activity=discord.Game(name=f"{info['name']} {countdown // 60}:{countdown % 60:02} avant arrêt")),
        )


@bot.event
async def on_ready():
    print(f"{bot.user.name} prêt en {round(time.time() - chrono, 3)}s\nTotal : {round(time.time() - start, 3)}s\n")
    print(await aternos.connect(bot.loop))
    aternos.on_update(activity, bot.loop)

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


chrono = time.time()
print(f"Lancement du bot après {round(time.time() - start, 3)}s")
bot.run(TOKEN)
