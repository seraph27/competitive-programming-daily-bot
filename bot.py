import os
import asyncio
import random
import discord
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from discord import app_commands
from platforms import CodeforcesClient, AtCoderClient
from utils.logger import setup_logging, get_logger
from utils.database import SettingsDatabaseManager

load_dotenv()
setup_logging()
logger = get_logger("bot")

GUILD_ID = 1376380498183589989
GUILD = discord.Object(id=GUILD_ID)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POST_HOUR = int(os.getenv("POST_HOUR", "9"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
cf_client = CodeforcesClient()
ac_client = AtCoderClient()
db_manager = SettingsDatabaseManager()

async def send_problem_embed(
    channel: discord.TextChannel,
    problem: dict,
    platform: str,
    header: str | None = None,
):
    if not problem:
        await channel.send(f"Failed to fetch {platform} problem.")
        return

    title = ""
    if platform == "codeforces":
        title = str(problem.get("id")) + ". " + str(problem.get("title"))
    else:
        title = str(problem.get("title"))

    embed = discord.Embed(
        title=title,
        url=problem.get("link"),
        color=0x9B59B6,
        description=header,
    )

    if platform == "codeforces":
        rating = problem.get("rating")
        if rating:
            embed.add_field(name="⭐ Rating", value=str(rating))
        tags = problem.get("tags")
        if tags:
            if isinstance(tags, list):
                tags_str = " ".join(f"||{t}||" for t in tags)
            else:
                tags_str = f"||{tags}||"
            embed.add_field(name="🏷️ Tags", value=tags_str, inline=False)
        embed.set_footer(text=f"From Contest #{problem.get('contestid')}")
    else:
        difficulty = problem.get("difficulty")
        embed.add_field(name="⭐ Difficulty", value=str(difficulty) if difficulty is not None else "N/A")
        embed.set_footer(text=f"From {problem.get('contest_id')}")

    await channel.send(embed=embed)

@bot.tree.command(name="random_cf", description="Get a random Codeforces problem")
@discord.app_commands.describe(min_rating="Minimum difficulty", max_rating="Maximum difficulty")
async def random_cf(interaction: discord.Interaction, min_rating: int | None = None, max_rating: int | None = None):
    await interaction.response.defer(ephemeral=False)
    problem = cf_client.get_random_problem(min_rating, max_rating)
    await send_problem_embed(interaction.channel, problem, "codeforces")
    await interaction.followup.send("Here is your Codeforces problem!", ephemeral=True)

@bot.tree.command(name="random_ac", description="Get a random AtCoder problem")
@discord.app_commands.describe(min_rating="Minimum difficulty", max_rating="Maximum difficulty")
async def random_ac(interaction: discord.Interaction, min_rating: int | None = None, max_rating: int | None = None):
    await interaction.response.defer(ephemeral=False)
    problem = ac_client.get_random_problem(min_rating, max_rating)
    if not problem:
        await interaction.followup.send("Failed to fetch problem", ephemeral=True)
        return
    await send_problem_embed(interaction.channel, problem, "atcoder")
    await interaction.followup.send("Here is your AtCoder problem!", ephemeral=True)

@bot.tree.command(name="set_channel", description="Set the channel for daily posts")
@discord.app_commands.describe(channel="Destination channel")
@commands.has_permissions(manage_guild=True)
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    success = db_manager.set_channel(interaction.guild.id, channel.id)
    if success:
        await interaction.response.send_message(
            f"Daily challenges will be posted in {channel.mention}.", ephemeral=True
        )
    else:
        await interaction.response.send_message("Failed to save channel.", ephemeral=True)


@bot.tree.command(name="daily", description="Post today's daily problems now")
async def manual_daily(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    settings = db_manager.get_server_settings(interaction.guild.id)
    target = (
        interaction.guild.get_channel(settings["channel_id"])
        if settings and interaction.guild.get_channel(settings["channel_id"])
        else interaction.channel
    )
    await send_daily_set(target)
    await interaction.followup.send(
        f"Daily problems posted in {target.mention}", ephemeral=True
    )

CATEGORIES = [
    {"name": "Easy", "cf": (800, 1200), "ac": (0, 600)},
    {"name": "Medium", "cf": (1200, 1600), "ac": (600, 1200)},
    {"name": "Hard", "cf": (1600, 2200), "ac": (1200, 1700)},
    {"name": "Expert", "cf": (2200, None), "ac": (1700, None)},
]


async def send_daily_set(channel: discord.TextChannel):
    for cat in CATEGORIES:
        platform = random.choice(["codeforces", "atcoder"])
        if platform == "codeforces":
            r = cat["cf"]
            problem = cf_client.get_random_problem(r[0], r[1])
        else:
            r = cat["ac"]
            problem = ac_client.get_random_problem(r[0], r[1])
        header = f"{cat['name']} challenge from {platform.title()}"
        await send_problem_embed(channel, problem, platform, header)


async def daily_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.utcnow()
        if now.hour == POST_HOUR and now.minute == 0:
            for guild in bot.guilds:
                settings = db_manager.get_server_settings(guild.id)
                channel = (
                    guild.get_channel(settings["channel_id"])
                    if settings and guild.get_channel(settings["channel_id"])
                    else guild.text_channels[0]
                )
                await send_daily_set(channel)
            await asyncio.sleep(60)
        await asyncio.sleep(30)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        guild_synced = await bot.tree.sync(guild=GUILD)
        logger.info(f"Synced with {len(guild_synced)} guild #{GUILD_ID}")
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
    bot.loop.create_task(daily_task())

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set")
    else:
        bot.run(DISCORD_TOKEN)
