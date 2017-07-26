import discord
from discord.ext.commands import Bot

my_bot = Bot(command_prefix="!")

@my_bot.event
async def on_read():
    print("Client logged in")

@my_bot.command()
async def hello(*args):
    return await my_bot.say("Hello, world!")

my_bot.run("MzM5ODEwNzA0MTE2Njc4NjU3.DFpY6A.8iEFTjwR3-skcaRXvbqB7Z-nIeU")