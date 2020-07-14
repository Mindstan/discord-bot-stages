import os
import asyncio
import discord
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

def get_object(user):
   global queue
   for member in queue:
      if str(member["member"]) == str(user):
         return member

def get_channel(guild, name):
   for channel in guild.channels:
      if str(channel) == name:
         return channel
   return None

def get_nick(member):
   if member.nick == None:
      return str(member)
   return member.nick
   
def get_user_channel(member):
   for role in member.roles:
      if role.name.startswith('u-'):
         return get_channel(member.guild, 'salon-' + role.name[2:])
   return None

async def update_board(guild):
   global queue
   
   nqueue = []
   for category in ["IOI", "EJOI"]:
      for user in get_channel(guild, 'couloir-' + category).members:
         obj = get_object(user)
         if obj == None:
            nqueue.append({"member":user, "category":category, "time": datetime.now(), "motive":""})
            
            user_channel = get_user_channel(user)
            if user_channel != None:
               #await user_channel.send(get_nick(user) + " a rejoint le couloir (" + datetime.now().strftime("%Hh%Mm%Ss") + ")\n N'oublie pas de dire pourquoi tu as besoin d'un entraîneur avec !motive !")
               await user_channel.send(get_nick(user) + " a rejoint le couloir (" + datetime.now().strftime("%Hh%Mm%Ss") + ")\n N'oubliez pas de mettre un message dans votre salon perso disant ce que vous attendez (soumission, aide sur un sujet, etc.)")
         else:
            nqueue.append({"member":user, "category":category, "time": obj["time"], "motive":obj["motive"]})
   
   queue = sorted(nqueue, key=lambda user: user["time"])
   
   msg = "Commandes : \n"
   msg += "```!next\n!next IOI\n!next EJOI\n!upd```\n"
   
   msg += "Liste des utilisateurs : \n```\n"
   for user in queue:
      msg += get_nick(user["member"]) + " " + user["category"] + "\t\t\t(" + user["time"].strftime("%Hh%Mm%Ss") + ") \t -> " + user["motive"] + "\n"
   msg += "```\n"
   
   await get_channel(guild, 'commandes-bot').purge(limit = 10)
   await get_channel(guild, 'commandes-bot').send(msg)

async def say(typ, message, guild):
   for category in guild.categories:
      estValide = False
      if category.name.startswith("CANDIDATS-"):
         if typ == "":
            estValide = True
         elif category.name == "CANDIDATS-" + typ:
            estValide = True
      
      if estValide:
         for channel in category.channels:
            await channel.send(message)

@client.event
async def on_ready():
   print('%s has connected to Discord!' % client.user)

queue = []

def get_category(category):
   for user in queue:
      if user["category"] == category or category == '':
         return user["member"]  
   return None

async def move_to(user, channel):
   if user != None:
      await user.move_to(channel)

def est_entraineur(user):
   for role in user.roles:
      if role.name == "Entraîneur":
         return True
   return False

@client.event
async def on_message(message):
   if message.author == client.user:
      return
      
   words = message.content.split()
   if len(words) != 0 and words[0] == '!next':
      if message.author.voice == None:
         await message.channel.send("Vous n'êtes pas dans un salon audio")
         return
      if not est_entraineur(message.author):
         return
      
      await message.channel.purge(limit = 1)
      
      user = None
      if len(words) == 1:
         user = get_category('')
         await move_to(get_category(''), message.author.voice.channel)
      else:
         user = get_category(words[1])
         
      if user != None:
         user_channel = get_user_channel(user)
         if user_channel != None:
            await user_channel.send(get_nick(user) + " a discuté avec " + get_nick(message.author) + " (" + datetime.now().strftime("%Hh%Mm%Ss") + ")")
         await move_to(user, message.author.voice.channel)
   
   elif len(words) != 0 and words[0] == '!upd':
      await message.channel.purge(limit = 1)
      await update_board(message.channel.guild)
   
   elif len(words) != 0 and words[0] == "!motive":
      for iUser in range(len(queue)):
         if str(queue[iUser]["member"]) == str(message.author):
            queue[iUser]["motive"] = message.content[8:]
            await update_board(message.channel.guild)
   
   elif len(words) != 0 and words[0] == "!say":
      if not est_entraineur(message.author):
         return
      await message.channel.purge(limit = 1)
      
      if len(words) != 1 and words[1] == "IOI":
         await say("IOI", message.content[8:], message.channel.guild)
      elif len(words) != 1 and words[1] == "EJOI":
         await say("EJOI", message.content[9:], message.channel.guild)
      else:
         await say("", message.content[5:], message.channel.guild)

@client.event
async def on_voice_state_update(member, before, after):
   if before.channel != None and before.channel.name.startswith("couloir"):
      await update_board(member.guild)
   elif after.channel != None and after.channel.name.startswith("couloir"):
      await update_board(member.guild)
   
client.run(TOKEN)
