import discord
from datetime import datetime
from kill import TarkovKill


async def kill_list_from_db(data, bot: discord.Bot):
    kills = [TarkovKill(item[0],
                        await bot.get_or_fetch_user(item[1]),
                        await bot.get_or_fetch_user(item[2]),
                        bot.get_guild(item[3]),
                        item[4],
                        datetime.strptime(item[5], "%Y-%m-%d %H:%M:%S.%f")) for item in data]
    kills.reverse()
    return kills
