import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

url = "https://vulcanvalues.com/grow-a-garden/stock"
headers = {"User-Agent": "Mozilla/5.0"}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

USER_ID = 425747134646583297
CHANNEL_ID = 1381739845273255976

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    bot.loop.create_task(stock_loop())

last_output = None

def scrape_stock():
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    current_output = []
    for header in soup.find_all("h2", class_="text-xl font-bold mb-2 text-center"):
        section_name = header.text.strip()
        section_lines = [f"\n== {section_name} =="]
        container = header.find_parent("div")
        if container:
            items = container.find_all("li")
            for item in items:
                spans = item.find_all("span")
                if spans:
                    text = ' '.join([s.get_text(strip=True) for s in spans])
                    text = re.sub(r'(x\d+)', r' \1', text)
                    text = re.sub(r'(x\d+)(?:.*\1)+', r'\1', text)
                    section_lines.append(text)
        current_output.extend(section_lines)
    return current_output

def parse_stock_output(stock_lines):
    """
    Converts stock output lines into a dict: {item: count}
    """
    stock_dict = {}
    for line in stock_lines:
        if line.startswith("==") or not line.strip():
            continue
        parts = line.rsplit(" x", 1)
        if len(parts) == 2:
            item, count = parts
            stock_dict[item.strip()] = int(count.strip())
    return stock_dict

def filter_stock(current_output):
        skip_headers = ['== HONEY STOCK ==', '== EGG STOCK ==']

        included_stock = []
        filtered_stock = []

        current_list = None

        for item in current_output:
            item = item.strip()
            if item.startswith("=="):
                if item in skip_headers:
                    current_list = filtered_stock
                else:
                    current_list = included_stock
                current_list.append(item)
            else:
                if current_list is not None:
                    current_list.append(item)
        return included_stock, filtered_stock


async def run_stock_tasks(channel):
    while not bot.is_closed():
        keywords = load_keywords()
        now = datetime.now()
        # Calculate seconds until next 5:05 mark
        next_5min = (now.minute // 5 + 1) * 5
        next_5min_dt = now.replace(minute=next_5min % 60, second=5, microsecond=0)
        if next_5min >= 60:
            next_5min_dt = next_5min_dt.replace(hour=(now.hour + 1) % 24)
        wait_seconds = (next_5min_dt - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        current_output = scrape_stock()
        included_stock, filtered_stock = filter_stock(current_output)

        # Send included_stock every 5 minutes and 5 seconds
        message = "\n".join(included_stock)
        await channel.send(f"**Included Stock:**\n```{message}```")

        # Ping user if keyword found in included_stock
        found_keywords = [word for word in keywords if any(word in line for line in included_stock)]
        if found_keywords:
            user = await bot.fetch_user(USER_ID)
            keyword_list = ', '.join(found_keywords)
            await channel.send(f"{user.mention} Keyword(s) found in Included Stock: {keyword_list}")

        # If it's a 30-minute mark, also send filtered_stock
        now = datetime.now()
        if now.minute % 30 == 0 and now.second == 5:
            message = "\n".join(filtered_stock)
            await channel.send(f"**Filtered Stock:**\n```{message}```")

            # Ping user if keyword found in filtered_stock
            found_keywords = [word for word in keywords if any(word in line for line in filtered_stock)]
            if found_keywords:
                user = await bot.fetch_user(USER_ID)
                keyword_list = ', '.join(found_keywords)
                await channel.send(f"{user.mention} Keyword(s) found in Filtered Stock: {keyword_list}")

async def stock_loop():
    global last_output
    await bot.wait_until_ready()
    channel_id = CHANNEL_ID  # Replace with your channel ID
    channel = bot.get_channel(channel_id)
    if not channel:
        print("Channel not found!")
        return
    await run_stock_tasks(channel)

@bot.command()
async def scrape(ctx):
    current_output = scrape_stock()
    message = "\n".join(current_output)
    await ctx.send(f"```{message}```")

@bot.command(name="clear")
@commands.has_permissions(administrator=True)
async def clearall(ctx):
    """Delete all messages in the current channel (admin only)."""
    await ctx.send("Deleting all messages...", delete_after=2)
    def not_pinned(msg):
        return not msg.pinned
    deleted = 0
    while True:
        msgs = await ctx.channel.purge(limit=100, check=not_pinned)
        if not msgs:
            break
        deleted += len(msgs)
    await ctx.send(f"Deleted {deleted} messages.", delete_after=5)

@bot.command()
async def addkeyword(ctx, *, word):
    keywords = load_keywords()
    if word in keywords:
        await ctx.send(f"`{word}` is already in the keyword list.")
    else:
        keywords.append(word)
        save_keywords(keywords)
        await ctx.send(f"Added `{word}` to the keyword list.")

@bot.command()
async def removekeyword(ctx, *, word):
    keywords = load_keywords()
    if word not in keywords:
        await ctx.send(f"`{word}` is not in the keyword list.")
    else:
        keywords.remove(word)
        save_keywords(keywords)
        await ctx.send(f"Removed `{word}` from the keyword list.")

@bot.command()
async def listkeywords(ctx):
    keywords = load_keywords()
    if not keywords:
        await ctx.send("No keywords set.")
    else:
        await ctx.send("Current keywords:\n" + "\n".join(f"- {k}" for k in keywords))

def load_keywords():
    try:
        with open("keywords.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_keywords(keywords):
    with open("keywords.txt", "w", encoding="utf-8") as f:
        for word in keywords:
            f.write(f"{word}\n")

bot.run(TOKEN)
