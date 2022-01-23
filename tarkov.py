from datetime import datetime
import pytz
import discord
import uuid
from discord.ext import commands, pages
from discord.commands import Option
import menus
from kill import TarkovKill
from tarkov_db import TarkovDB
from menus import GeneralEmbed
import core

bot = commands.Bot(intents=discord.Intents.all()) # adjust this later
db = TarkovDB('')


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(str(bot.user.id))
    print('------')
    await bot.change_presence(status=None, activity=discord.Game("v2 Update! | see /info"))


@bot.event
async def on_guild_join(guild: discord.Guild):
    db.insert(guild)


@bot.slash_command(name="info")
async def info(ctx: discord.ApplicationContext):
    """Produce information about the bot"""
    embed = GeneralEmbed.generate("Bot Information", "Information about Tarkov Tracker")
    embed.add_field(
        name="Bot Invite Link",
        value="https://discord.com/api/oauth2/authorize?client_id=864333416191229973&permissions=248896&scope=applications.commands%20bot",
        inline=False
    )
    embed.add_field(
        name="GitHub URL - Report bugs or request features here!",
        value="https://github.com/g1ver/EFT-Teamkill-Tracker/",
        inline=False
    )
    await ctx.respond(embed=embed)


@bot.slash_command(name="log")
async def log(
        ctx: discord.ApplicationContext,
        killer: Option(discord.Member, "Killer"),
        killed: Option(discord.Member, "Killed"),
        tag: Option(str, "Enter a note", required=False, default="")
):
    """Log a kill for your server."""
    kill = TarkovKill(str(uuid.uuid4()), killer, killed, ctx.guild, tag, str(datetime.utcnow()))

    db.insert(killer)
    db.insert(killed)
    db.insert(ctx.guild)
    db.insert(kill)

    embed = discord.Embed(title="Kill Logged")
    embed.add_field(name="UTC Time", value=datetime.utcnow(), inline=False)
    embed.add_field(name="Killer", value=kill.killer.mention, inline=True)
    embed.add_field(name="Killed", value=kill.killed.mention, inline=True)
    embed.add_field(name="Note", value=tag or "None", inline=False)

    await ctx.respond(embed=embed)


@bot.slash_command(name="delete")
async def delete(
        ctx: discord.ApplicationContext,
        number: int
):
    """Delete a kill on the server, view kill number with /view server."""
    await ctx.defer()
    kills = await core.kill_list_from_db(db.server_find(ctx.guild), bot)

    if kills:
        ranked_kills = menus.kills_to_deletion(kills)
        if number in ranked_kills.keys():
            kill = ranked_kills[number]
            db.delete(kill, ctx.guild)
            await ctx.respond(embed=GeneralEmbed.generate(
                "Deleted Kill",
                f"{kill.killer.mention} killed {kill.killed.mention} [{kill.tag}]")
            )
        else:
            await ctx.respond(embed=menus.GeneralEmbed.generate("Kill Deletion Failed", f"There is no kill {number}."))
    else:
        await ctx.respond(embed=menus.GeneralEmbed.generate("Kill Log", "There are no kills logged to delete."))


@bot.slash_command(name="leaderboard")
async def leaderboard(
        ctx: discord.ApplicationContext,
        option: Option(str, "Kills or deaths leaderboard", required=True, choices=["kills", "deaths"])
):
    """View the leaderboard for your server for kills or deaths."""
    await ctx.defer()
    kills = await core.kill_list_from_db(db.server_find(ctx.guild), bot)

    if kills:
        embed = menus.kills_to_leaderboards(kills, option)
    else:
        embed = menus.GeneralEmbed.generate("Kill Log", "There are no kills logged in the server.")
    await ctx.respond(embed=embed)


view = bot.create_group(
    "view", "Commands related to viewing server log."
)


@view.command(name="server")
async def view_server(ctx: discord.ApplicationContext):
    """View all kills in the server."""
    await ctx.defer()
    kills = await core.kill_list_from_db(db.server_find(ctx.guild), bot)

    if kills:
        embeds = menus.kills_to_embeds(kills, "Kill List for Server")
        paginator = pages.Paginator(pages=embeds)
        await paginator.respond(ctx.interaction)
    else:
        await ctx.respond(embed=menus.GeneralEmbed.generate("Kill Log", "There are no kills logged in the server."))


@view.command(name="kills")
async def view_kills(
        ctx: discord.ApplicationContext,
        user: discord.Member
):
    """View all kills associated with a user in the server."""
    await ctx.defer()
    kills = await core.kill_list_from_db(db.killer_find(ctx.guild, user), bot)

    if kills:
        embeds = menus.kills_to_embeds(kills, f"Kill List for @{user.display_name}")
        paginator = pages.Paginator(pages=embeds)
        await paginator.respond(ctx.interaction)
    else:
        await ctx.respond(embed=menus.GeneralEmbed.generate("Kill Log",
                                                            "There are no kills for that user logged in the server."))


@view.command(name="deaths")
async def view_deaths(
        ctx: discord.ApplicationContext,
        user: discord.Member
):
    """View all deaths associated with a user in the server."""
    await ctx.defer()
    kills = await core.kill_list_from_db(db.killed_find(ctx.guild, user), bot)

    if kills:
        embeds = menus.kills_to_embeds(kills, f"Death List for @{user.display_name}")
        paginator = pages.Paginator(pages=embeds)
        await paginator.respond(ctx.interaction)
    else:
        await ctx.respond(embed=menus.GeneralEmbed.generate("Kill Log",
                                                            "There are no deaths for that user logged in the server."))


timezone = bot.create_group(
    "timezone", "Commands related to timezone management."
)


async def tz_searcher():
    return [tz for tz in pytz.common_timezones]


@timezone.command(name="view")
async def timezone_view(ctx: discord.ApplicationContext):
    """View your server's current timezone."""
    await ctx.defer()
    tz = db.get_timezone(ctx.guild)[0]
    embed = menus.time_append(GeneralEmbed.generate("Timezone", f"{tz}"), tz)
    await ctx.respond(embed=embed)


@timezone.command(name="set")
async def timezone_set(
        ctx: discord.ApplicationContext,
        tz: Option(str, "Timezone", required=True, autocomplete=discord.utils.basic_autocomplete(tz_searcher))
):
    """Set a new timezone for your server."""
    await ctx.defer()
    if tz not in pytz.common_timezones:
        embed = GeneralEmbed.generate("Timezone Error", f"`{tz}` is not a valid timezone.")
    else:
        db.set_timezone(ctx.guild, tz)
        embed = menus.time_append(GeneralEmbed.generate("New Timezone", f"{tz}"), tz)
    await ctx.respond(embed=embed)

bot.run('')
