# Code to roll fake flower packets 
import random
import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


from flask import Flask
from threading import Thread

# Flask website to ensure render is never down
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

crafter_seeds = ['Crocus', 'Succulent', 'Violent Corn', 'Bendboo', 'Cocovine', 'Dragon Pepper', 'Rainbow']
crafter_odds = [39, 25, 20, 10, 4.5, 0.5, 1]
rb_crafter_seeds = crafter_seeds[:-1]
rb_crafter_odds = [30, 25, 20, 10, 8, 7]

flower_seeds = ['Rose', 'Foxglove', 'Lilac', 'Pink Lily', 'Purple Dahlia', 'Sunflower', 'Rainbow']
flower_odds = [40, 25, 20, 10, 4.5, 0.5, 1]
rb_flower_seeds = flower_seeds[:-1]
rb_flower_odds = [30, 25, 20, 10, 8, 7]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def do_roll(seeds, odds, rb_seeds, rb_odds, rolls):
    result = random.choices(seeds, odds, k=rolls)
    result_list = {seed: 0 for seed in seeds}
    for seed in rb_seeds:
        result_list[f'Rainbow {seed}'] = 0
    for i in result:
        if i == 'Rainbow':
            roll_2 = random.choices(rb_seeds, rb_odds, k=1)[0]
            result_list[f'Rainbow {roll_2}'] += 1
        else:
            result_list[i] += 1
    return result_list

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="crafter", description="Roll a Crafter Seed Pack")
@app_commands.describe(rolls="Number of packs to roll (default 10)")
async def crafter(interaction: discord.Interaction, rolls: int = 10):
    result_list = do_roll(crafter_seeds, crafter_odds, rb_crafter_seeds, rb_crafter_odds, rolls)
    msg = "\n".join(f"{k}: {v}" for k, v in result_list.items() if v > 0)
    await interaction.response.send_message(f"**Crafter Seed Pack Roll ({rolls}):**\n{msg}")

@bot.tree.command(name="flower", description="Roll a Flower Seed Pack")
@app_commands.describe(rolls="Number of packs to roll (default 10)")
async def flower(interaction: discord.Interaction, rolls: int = 10):
    result_list = do_roll(flower_seeds, flower_odds, rb_flower_seeds, rb_flower_odds, rolls)
    msg = "\n".join(f"{k}: {v}" for k, v in result_list.items() if v > 0)
    await interaction.response.send_message(f"**Flower Seed Pack Roll ({rolls}):**\n{msg}")

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
