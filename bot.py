#TODO: Add additional commands
#TODO: Add a cooldown timer for each command separately
#TODO: Add code to handle alternate events
#TODO: Role Checking
#TODO: Permit Command

import discord
from discord.ext.commands import Bot
import re
import aiofiles
import asyncio
import os
import sys

#Temporary
sys.path.append('C:\\Discord Bot')

from imp import reload
import config as cfg

Butt = Bot(command_prefix="!")

# These things are extremely unlikely to change while the bot is active
OAuthToken = cfg.OAuthToken
TimeOfLastToken = ""

# List of Badword Regex Filters, populated on startup and after the get_filters() method is called
filters = []
immediateban = []

# List of Whitelisted URLs in Regex format, populated on startup and after the get_whitelists() method is called
whitelists = []

# List of users permitted to post a URL.
permitted = []

enabled = False
# TODO: Store Roles Properly?
mod_roles = ['Administrator','Moderator','Lead Moderator']

# Instead of saving the variables in the code, grab them from a config file instead.
# This is a method in case we need to update the settings while the bot is active
def get_config():
	reload(cfg)
	return
	
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
	url = re.search(cfg.urlregexmatch,Content,flags=re.I)
	
	# If yes...
	if url and str(message.author) not in permitted:
		print("Message contains a URL.")
		NewWords = []
		# Loop through the list of whitespace separated strings
		for x in Words:
			match = re.search(cfg.urlregexmatch,x,flags=re.I)
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

# Check if the author of the message has one of the moderator roles
def is_mod(message):
	for role in message.author.roles:
		if role.name in mod_roles:
			return True
	return False

# TODO: Implement this properly
def is_permitted(message):
	if message.author.name in permitted:
		return True
	return False
	
# TODO: Get these from Firebase instead
async def get_filters():
	global filters
	# Get new user token, since they expire hourly.
	cfg.refresh()
	# Get Filters from DB
	filters = cfg.db.child("badwords").get(cfg.user['idToken']).val()
	# Check to remove None entries in case numbering is not maintained properly
	filters = [x for x in filters if x != None]
	return
	
async def get_banwords():
	global immediateban
	cfg.refresh()
	banlist = cfg.db.child("immediateban").get(cfg.user['idToken']).val()
	banlist = [x for x in banlist if x != None]
	immediateban = banlist
	return
	
async def get_whitelists():
	global whitelists
	cfg.refresh()	
	whitelist = cfg.db.child("whitelist").get(cfg.user['idToken']).val()
	whitelist = [x for x in whitelist if x != None]
	whitelists = whitelist
	return

async def log_message(message):
	File = cfg.Root_Dir+str(message.server)+"\\"+str(message.channel)+".log"
	async with aiofiles.open(File,'a') as f:
		await f.write("("+str(message.timestamp)+") ["+str(message.author)+"] "+str(message.content)+"\n")
	return
	
# Startup Event

async def bot_enable():
	global enabled
	await get_filters()
	await get_banwords()
	await get_whitelists()
	enabled = True
	return

@Butt.event
async def on_ready():
	print("Client logged in.")
	print("Name: "+Butt.user.name)
	print("ID: "+Butt.user.id)
	return
	
# Discord Server Events
@Butt.event
async def on_message(message):
	global filters,whitelists,immediateban
	mod = is_mod(message)
	Content = str(message.content)
	Author = str(message.author)
	Timestamp = str(message.timestamp)
	Channel = str(message.channel)
	LogChannel = discord.utils.get(Butt.get_all_channels(), name='bot-log-channel')
	await log_message(message)
	# We don't want to treat the bot messages as commands
	if (Author == Butt.user):
		return
	
	#FilteredChannels = [discord.utils.get(Butt.get_all_channels(), name='general'),discord.utils.get(Butt.get_all_channels(), name='Voicechat'),discord.utils.get(Butt.get_all_channels(), name='Chillzone')]
	if not enabled:
		if message.content.startswith("!enable") and mod:
			await bot_enable()
			await Butt.send_message(LogChannel,"!enable command triggered by "+Author+" at "+Timestamp+".")
		return
	
	if (message.channel == LogChannel):
		return
	
	# We don't want to treat the bot messages as commands
	if (Author == Butt.user):
		return
		
	# Check message for naughty things
	# TODO: Implement Scaling Punishments for repeat infractions
	
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

	# Command Block
	if message.content.startswith("!schedule"):
		await Butt.send_message(message.channel, "The "+cfg.Event+" schedule is available at "+cfg.Schedlink)
		await Butt.send_message(LogChannel,"!schedule command triggered by "+Author+" at "+Timestamp+".")
	elif message.content.startswith("!tracker"):
		await Butt.send_message(message.channel, "The "+cfg.Event+" tracker is available at "+cfg.Trackerlink)
		await Butt.send_message(LogChannel,"!tracker command triggered by "+Author+" at "+Timestamp+".")
	elif message.content.startswith("!exit") and mod:
		await Butt.send_message(message.channel, "Sadface.")
		await Butt.send_message(LogChannel,"!exit command triggered by "+Author+" at "+Timestamp+".")
		print("Exit command given by user: "+Author)
		return await Butt.close()
	elif message.content.startswith("!updatefilters") and mod:
		await get_filters()
		await get_banwords()
		await Butt.send_message(LogChannel,"!updatefilters command triggered by "+Author+" at "+Timestamp+".")
	#elif message.content.startswith("!permit") and mod:
		# TODO: Check to see if you can grab a person's name from a message without converting to string
		#if Words[1] in :
	elif message.content.startswith("!reload") and mod:
		await Butt.send_message(LogChannel,"!reload command triggered by "+Author+" at "+Timestamp+".")
		try:
			get_config()
		except:
			e = sys.exc_info()
			print("Reload failed: "+str(e))
		finally:
			print("Reload successful.")	
		
	return
	
# OAuth Token
Butt.run(OAuthToken)