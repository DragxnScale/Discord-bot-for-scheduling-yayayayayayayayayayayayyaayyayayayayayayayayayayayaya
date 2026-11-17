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
            await interaction.response.send_message("Please set your timezone with /time_zone or specify it it the timezone parameter", ephemeral = True )
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

@bot.tree.command(name = "timezone", description = "changes timezone")
async def time_zone(interaction: discord.Interaction, time_zone: str):
    user_id = interaction.user.id
    try:
        ZoneInfo(time_zone)
    except ZoneInfoNotFoundError:
        await interaction.response.send_message("Invalid timezone. Use a name like America/Los_Angeles.", ephemeral = True)
        return
    user_timezones[user_id] = time_zone
    await interaction.response.send_message(f"Your timezone has been set to {time_zone}", ephemeral = True)
     
GUILD_ID = discord.Object(id = 1394189698884436011)


@bot.tree.command(name="remove_block", description="Removes a scheduled block")
async def remove_block(interaction: discord.Interaction, block_id: int):
    user_id = interaction.user.id

    if user_id in schedules and block_id in schedules[user_id]: 
        schedules[user_id].pop(block_id)
        await interaction.response.send_message(f"Block {block_id} has been removed successfully", ephemeral = True)
    elif user_id not in schedules:
        await interaction.response.send_message(f"No current blocks", ephemeral = True )
    elif block_id not in schedules[user_id]:
        await interaction.response.send_message(f'Block "{block_id}" not in your schedule', ephemeral = True )
    else:
        print("wtf happend")


@bot.tree.command(name="upcoming", description="shows next block")
async def upcoming(interaction: discord.Interaction):
    user_id = interaction.user.id
    current_time = datetime.now(timezone.utc)
    next_block = None
    next_block_id = None
    if user_id in schedules and schedules[user_id]:
        for block_id, block in schedules[user_id].items():
            if block["start"] > current_time and (next_block is None or block["start"] < next_block["start"]):
                next_block = block
                next_block_id = block_id
        
        if next_block == None:
            await interaction.response.send_message("All blocks have passed", ephemeral = True )

        else:
            time_diff = next_block["start"] - current_time
            await interaction.response.send_message(f"Block #{next_block_id}: {next_block["title"]} is in {time_diff.total_seconds()/60} minutes", ephemeral = True )

    else:
        await interaction.response.send_message("No upcoming blocks", ephemeral = True )




bot.run(token, log_handler = handler, log_level = logging.DEBUG)