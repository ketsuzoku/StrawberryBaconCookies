#TODO: Add additional commands
#TODO: Add a cooldown timer for each command separately
#TODO: Enable per-channel logging
#TODO: Add code to handle alternate events
#TODO: Role Checking

import discord
import re
import aiofiles
import asyncio
import os
from discord.ext.commands import Bot

Butt = Bot(command_prefix="!")
Filter_file = "C:\\Discord Bot\\filters.txt"
Whitelist_file = "C:\\Discord Bot\\whitelists.txt"
Root_Dir = "C:\\Discord Bot\\"

# TODO: Get these dynamically?
# Links to things that are relevant to the event.
Schedlink = "https://gamesdonequick.com/schedule"
Trackerlink = "https://gamesdonequick.com/tracker/21"
# Current event.
Event = "AGDQ 2018"

# List of Badword Regex Filters, populated on startup and after the get_filters() method is called
filters = []

# List of Whitelisted URLs in Regex format, populated on startup and after the get_whitelists() method is called
whitelists = []

# URL Regex Matcher
urlregexmatch = "https?:\/\/[^\s]+\.[^\s]+|www\.[^\s]+\.[^\s]+"

#FilterURL = ""
#ChatRules = "Empty"

# Timers?
Scheduletimer = 300000
Trackertimer = 300000


# GDQ Server stuff
#mod_roles = ['Administrators','gdq-attendee-bot','gdqstaff','headmods','partners','chatmods','restreamers']
mod_roles = ['Administrator','Moderator','Lead Moderator']

# Utility commands

# Check each incoming message for urls, if a match, purge the message
# If no url, check each incoming message for badwords, if a match, purge the message, with scaling punishments based on the frequency of the infraction.
# TODO: Implement that
async def examine_message_for_badwords(message)	:
	Content = str(message.content)
	Words = Content.split(' ') # Used for URL stuff only, separates the message into a list of words using whitespace as a separator
	id = 0	
	action = 0
	
	# Check if the content matches the url regex filter
	url = re.search(urlregexmatch,Content,flags=re.I)
	
	# If yes...
	if url:
		print("Message contains a URL.")
		NewWords = []
		# Loop through the list of whitespace separated strings
		for x in Words:
			match = re.search(urlregexmatch,x,flags=re.I)
			if match:
				NewWords.append(x)
			await asyncio.sleep(0.001)
		# If each word is a match, add it to a new list of things that are URLs
		
		# Loop through the list of URLs
		for x in NewWords:
			for y in whitelists:
				match = re.search(y,x,flags=re.I)
				if match is None:
					id = -1
					action = 1
					return id,action
					print("URL does not match whitelists.")
				await asyncio.sleep(0.001)
		# Check each URL against each whitelisted link regex filter, if there is no match then the URL is bad and needs to be purged, otherwise we continue
		# This is to ensure people can't get around the link filter by including a whitelisted link with a bad one
			
	# Loop through the badword filters comparing them to the entirety of the message
	iter = 0
	for x in filters:
		match = re.search(x,Content,flags=re.I)
		if match:
			id = iter
			action = 1
			return id,action
		iter += 1
		await asyncio.sleep(0.001)
	return id,action
	# If a hit, we need to purge it.
	# ID returns the ID of the regex filter that triggered the action
	# Actions: 1 = Purge, 2 = Kick, 3 = Ban, 0 = Do Nothing
		
# Check if line starts with ! and consists of one word
async def is_command(message):
	Content = str(message.content)
	List = [Content.split(' ')]
	if message.content.startswith('!') and len(List) == 1:
		return True
	else:
		return False
		
# Check if the author of the message has one of the moderator roles
def is_mod(message):
	for role in message.author.roles:
		if role.name in mod_roles:
			return True
	return False
	
def is_permitted(message):
	if message.author.name in permitted:
		return True
	return False
		
#TODO Make filters write from URL to file later


async def get_filters(File):
	filters = []
	async with aiofiles.open(File,'r') as f:
		async for line in f:
			filters.append(line)
	return

async def get_whitelists(File):
	whitelists = []
	async with aiofiles.open(File,'r') as f:
		async for line in f:
			whitelists.append(line)
	return
	
async def add_whitelist(File,filter):
	async with aiofiles.open(File,'a') as f:
		await f.write(filter+"\n")
	await get_whitelists(File)
	return

async def add_filter(File,filter):
	async with aiofiles.open(File,'a') as f:
		await f.write('filter')
	await get_filters(File)
	return

async def log_message(message):
	File = Root_Dir+str(message.server)+"\\"+str(message.channel)+".log"
	async with aiofiles.open(File,'a') as f:
		await f.write("("+str(message.timestamp)+") ["+str(message.author)+"] "+str(message.content)+"\n")
	return
	
# Startup Event

@Butt.event
async def on_ready():
	print("Client logged in.")
	print("Name: "+Butt.user.name)
	print("ID: "+Butt.user.id)
	await get_filters(Filter_file)
	await get_whitelists(Whitelist_file)
	return

# Discord Server Events
@Butt.event
async def on_message(message):
	#Convert some objects to string so we can examine them later
	Content = str(message.content)
	Author = str(message.author)
	Timestamp = str(message.timestamp)
	Channel = str(message.channel)
	
	# Clean this up later for multi-server shit
	LogChannel = discord.utils.get(Butt.get_all_channels(), name='bot-log-channel')
	#FilteredChannels = [discord.utils.get(Butt.get_all_channels(), name='general'),discord.utils.get(Butt.get_all_channels(), name='Voicechat'),discord.utils.get(Butt.get_all_channels(), name='Chillzone')]
	
	#log_message(message)
	# We don't want to report on messages in the log channel; infinite loops are bad
	if (message.channel == LogChannel):
		return
	
	# Terminal Logging
	print(Channel + ": "+Content+"\" by user "+Author+" at "+Timestamp)
	
	# We don't want to treat the bot messages as commands
	if (Author == Butt.user):
		return
		

	print("Server: "+str(message.server))
	print("Channel: "+str(message.channel))
	print("Log file: "+Root_Dir+str(message.server)+"\\"+str(message.channel)+".log")
	await log_message(message)
	
	# Check message for naughty things
	mod = is_mod(message)
	if not mod:
		Badwordcheck = await examine_message_for_badwords(message)
		if Badwordcheck[0] != 0:
			await Butt.delete_message(message)
			if Badwordcheck[1] == 1:
				Badwordcheck[1] = 'Purge'
			elif Badwordcheck[1] == 2:
				Badwordcheck[1] = 'Kick'
				await kick_user(message)
			elif Badwordcheck[1] == 3:
				Badwordcheck[1] = 'Ban'
				await ban_user(message)
			else:
				Badwordcheck[1] = 'No action taken'
			if Badwordcheck[0] == -1:
				await Butt.send_message(LogChannel,"User "+Author+" triggered URL filter. Message: \""+Content+"\". Action taken: "+Badwordcheck[1]+".")
				return

			await Butt.send_message(LogChannel,"User "+Author+" triggered badwords filter \#" + Badwordcheck + ". Message: \""+Content+"\". Action taken: "+Badwordcheck[1]+".")
			return
	

	#Probably separate handling for commands to non-commands?
	command = await is_command(message)
	if command:
		if message.content.startswith("!schedule"):
			await Butt.send_message(message.channel, "The "+Event+" schedule is available at "+Schedlink)
			await Butt.send_message(LogChannel,"!schedule command triggered by "+Author+" at "+Timestamp+" .")
		elif message.content.startswith("!tracker"):
			await Butt.send_message(message.channel, "The "+Event+" tracker is available at "+Trackerlink)
			await Butt.send_message(LogChannel,"!tracker command triggered by "+Author+" at "+Timestamp+" .")
		elif message.content.startswith("!exit") and mod:
			await Butt.send_message(message.channel, "Sadface.")
			await Butt.send_message(LogChannel,"!exit command triggered by "+Author+" at "+Timestamp+" .")
			print("Exit command given by user: "+Author)
			return await Butt.close()
		elif message.content.startswith("!updatefilters") and mod:
			await get_filters(Filter_file)
			await Butt.send_message(LogChannel,"!updatefilters command triggered by "+Author+" at "+Timestamp+" .")
		
	return
	
# OAuth Token, PROTECT
Butt.run("MzM5ODEwNzA0MTE2Njc4NjU3.DFpY6A.8iEFTjwR3-skcaRXvbqB7Z-nIeU")