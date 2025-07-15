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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
cf_client = CodeforcesClient()
ac_client = AtCoderClient()

async def send_daily_problem(channel: discord.TextChannel, platform: str, min_rating=None, max_rating=None):
    if platform == "codeforces":
        problem = await cf_client.get_random_problem(min_rating, max_rating)
    else:
        problem = await ac_client.get_random_problem(min_rating, max_rating)
    if not problem:
        await channel.send(f"Failed to fetch {platform} problem.")
        return
    embed = discord.Embed(title=problem['title'], url=problem['link'], color=0x9B59B6)
    if problem.get("rating"):
        embed.add_field(name="Rating", value=str(problem['rating']))
    embed.set_footer(text=f"{platform.title()} Daily Problem")
    await channel.send(embed=embed)

@bot.tree.command(name="random_cf", description="Get a random Codeforces problem")
@discord.app_commands.describe(min_rating="Minimum rating", max_rating="Maximum rating")
async def random_cf(interaction: discord.Interaction, min_rating: int | None = None, max_rating: int | None = None):
    await interaction.response.defer(ephemeral=True)
    problem = await cf_client.get_random_problem(min_rating, max_rating)
    if not problem:
        await interaction.followup.send("Failed to fetch problem", ephemeral=True)
        return
    embed = discord.Embed(title=problem['title'], url=problem['link'], color=0x9B59B6)
    if problem.get("rating"):
        embed.add_field(name="Rating", value=str(problem['rating']))
    embed.set_footer(text="Codeforces Random Problem")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="random_ac", description="Get a random AtCoder problem")
@discord.app_commands.describe(min_rating="Minimum difficulty", max_rating="Maximum difficulty")
async def random_ac(interaction: discord.Interaction, min_rating: int | None = None, max_rating: int | None = None):
    await interaction.response.defer(ephemeral=True)
    problem = await ac_client.get_random_problem(min_rating, max_rating)
    if not problem:
        await interaction.followup.send("Failed to fetch problem", ephemeral=True)
        return
    embed = discord.Embed(title=problem['title'], url=problem['link'], color=0x9B59B6)
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
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set")
    else:
        bot.run(DISCORD_TOKEN)
