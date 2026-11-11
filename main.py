import discord
from discord.ext import commands 
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename = "discord.log", encoding = "utf-8", mode = "w")
handler.setFormatter(logging.Formatter("/%(asctime)s: %(levelname)s: %(name)s: %(message)s"))
intents = discord.Intents.default()

bot = commands.Bot(command_prefix = "y@y", intents = intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready to go. Have I ever mentioned how great Matthew and Thu are")

    try:
        guild = discord.Object(id=1394189698884436011)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        print(f"oops soemthing kaboom: {e}")

schedules = {}
next_block_id = 1
user_timezones = {}

def convert_to_utc(local_datetime, user_zone):
    local_datetime = local_datetime.replace(tzinfo=user_zone)
    return local_datetime.astimezone(timezone.utc)

@bot.tree.command(name = "add_block", description = "adds block")
async def add_block(interaction: discord.Interaction, title: str, start_date: str, start_time: str, end_time: str, description: str = "", remind_min_before: int = 15, end_date: str = None, time_zone: str = None):
    global next_block_id
    current_block_id = next_block_id
    user_id = interaction.user.id
    if end_date is None:
        end_date = start_date

    if time_zone is None:
        if user_id in user_timezones:
            time_zone = user_timezones[user_id]
        else:
            await interaction.response.send_message("Please set your timezone with /timezone or specify it it the timezone parameter", ephemeral = True )
            return
    

    
    try:
        user_zone = ZoneInfo(time_zone)
    except ZoneInfoNotFoundError:
        await interaction.response.send_message("Invalid timezone. Use a name like America/Los_Angeles.", ephemeral = True)
        return
    
    try:
        start = datetime.strptime(start_date + " " + start_time, "%Y-%m-%d %H:%M")
        end = datetime.strptime(end_date + " " + end_time, "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message("Invalid format: please use YYYY-MM-DD where year must be 4 digits. Month and day can be one digit, time is in 24 hour HH:MM format", ephemeral = True )
        return

    start = convert_to_utc(start, user_zone)
    end = convert_to_utc(end, user_zone)

    if end <= start:
        await interaction.response.send_message("End time must be after start time", ephemeral = True )
        return

    if remind_min_before < 0:
        await interaction.response.send_message("Remind time can not be after the event", ephemeral = True )
        return

    if user_id not in schedules:
        schedules[user_id] = {}
    next_block_id += 1
    schedules[user_id][current_block_id] = {"title": title, "start": start, "end": end, "description": description, "remind_min_before": remind_min_before}
    user_timezones[user_id] = time_zone
    await interaction.response.send_message(f"Success! Block has been created at {start} with id {current_block_id}.", ephemeral = True )

    
        

    
GUILD_ID = discord.Object(id = 1394189698884436011)


bot.run(token, log_handler = handler, log_level = logging.DEBUG)