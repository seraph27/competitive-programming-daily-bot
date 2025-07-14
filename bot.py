import os
import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv

from platforms import CodeforcesClient, AtCoderClient
from utils.logger import setup_logging, get_logger

load_dotenv()
setup_logging()
logger = get_logger("bot")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POST_HOUR = int(os.getenv("POST_HOUR", "9"))

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
cf_client = CodeforcesClient()
ac_client = AtCoderClient()

async def send_daily_problem(channel: discord.TextChannel, platform: str):
    if platform == "codeforces":
        problem = await cf_client.get_random_problem()
    else:
        problem = await ac_client.get_random_problem()
    if not problem:
        await channel.send(f"Failed to fetch {platform} problem.")
        return
    embed = discord.Embed(title=problem['title'], url=problem['link'], color=0x00AAFF)
    if problem.get("rating"):
        embed.add_field(name="Rating", value=str(problem['rating']))
    embed.set_footer(text=f"{platform.title()} Daily Problem")
    await channel.send(embed=embed)

@bot.tree.command(name="daily_cf", description="Get a random Codeforces problem")
async def daily_cf(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    problem = await cf_client.get_random_problem()
    if not problem:
        await interaction.followup.send("Failed to fetch problem", ephemeral=True)
        return
    embed = discord.Embed(title=problem['title'], url=problem['link'], color=0x00AAFF)
    if problem.get("rating"):
        embed.add_field(name="Rating", value=str(problem['rating']))
    embed.set_footer(text="Codeforces Random Problem")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="daily_ac", description="Get a random AtCoder problem")
async def daily_ac(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    problem = await ac_client.get_random_problem()
    if not problem:
        await interaction.followup.send("Failed to fetch problem", ephemeral=True)
        return
    embed = discord.Embed(title=problem['title'], url=problem['link'], color=0x00AAFF)
    embed.set_footer(text="AtCoder Random Problem")
    await interaction.followup.send(embed=embed, ephemeral=True)

async def daily_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.utcnow()
        if now.hour == POST_HOUR and now.minute == 0:
            for guild in bot.guilds:
                channel = guild.text_channels[0]
                await send_daily_problem(channel, "codeforces")
                await send_daily_problem(channel, "atcoder")
            await asyncio.sleep(60)
        await asyncio.sleep(30)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    try:
        await bot.tree.sync()
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
    bot.loop.create_task(daily_task())

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set")
    else:
        bot.run(DISCORD_TOKEN)
