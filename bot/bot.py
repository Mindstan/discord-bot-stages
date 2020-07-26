import os
import asyncio
import discord
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import pytz

local_tz = pytz.timezone('Europe/Paris')

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = os.getenv('API_URL')
API_TOKEN = os.getenv('API_TOKEN', '')

client = discord.Client()

queue = []

#API UTILS
def get_api(url):
   xhr = requests.get(url, headers={"Authorization": API_TOKEN,"Content-type": "application/json"})
   return json.loads(xhr.content.decode('utf-8'))

def put_api(url, data):
   xhr = requests.put(url, headers={"Authorization": API_TOKEN,"Content-type": "application/json"}, data=json.dumps(data))
   return json.loads(xhr.content.decode('utf-8'))

def post_api(url, data):
   xhr = requests.post(url, headers={"Authorization": API_TOKEN,"Content-type": "application/json"}, data=json.dumps(data))
   return json.loads(xhr.content.decode('utf-8'))

def get_user(name):
   users = get_api(API_URL + "/api/candidat/")
   
   for user in users:
      if user['discord_name'] == name:
         return user
   return None

def get_recherche(candidat, sujet):
   recherches = get_api(API_URL + "/api/recherche?sujet=" + str(sujet['id']) + "&candidat=" + str(candidat['id']))
   
   if len(recherches) >= 1:
      return recherches[0]
   
   nouv = post_api(API_URL + "/api/recherche/", {
      "candidat": candidat['url'],
      "sujet": sujet['url']
   })
   return nouv
   
def get_suivant(sujet):
   sujets = get_api(API_URL + "/api/sujet/")
   
   for nouv in sujets:
      if nouv['parcours'] == sujet['parcours'] and nouv['ordre'] == sujet['ordre'] + 1:
         return nouv
   
   return None

def get_code(code):
   sujets = get_api(API_URL + "/api/sujet/")
   parcours = get_api(API_URL + "/api/parcours/")
   
   p = {}
   for parcour in parcours:
      p[parcour['url']] = parcour
   
   for nouv in sujets:
      if p[nouv['parcours']]['code'] + '.' + str(nouv['ordre']) == code:
         return nouv
   
   return None

#DISCORD UTILS
def est_entraineur(user):
   for role in user.roles:
      if role.name == "Entraîneur":
         return True
   return False

async def move_to(user, channel):
   if user != None:
      await user.move_to(channel)

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

def get_category(category):
   for user in queue:
      if user["category"] == category or category == '':
         return user["member"]  
   return None





@client.event
async def on_ready():
   print('%s has connected to Discord!' % client.user)
   
async def say(typ, message, guild):
   for category in guild.categories:
      if category.name.startswith("GROUPE-") and category.name == "GROUPE-" + typ:  
         for channel in category.channels:
            if channel.name.startswith("salon-"):
               await channel.send(message)

async def update_board(guild):
   global queue
   
   nqueue = []
   for category in guild.categories:
      if category.name.startswith("GROUPE-"):
         category_name = category.name[7:]  

         for user in get_channel(guild, 'couloir-' + category_name).members:
            obj = get_object(user)
            if obj == None:
               nqueue.append({"member":user, "category":category_name, "time":datetime.utcnow()})
               
               user_channel = get_user_channel(user)
               if user_channel != None:
                  await user_channel.send(get_nick(user) + " a rejoint le couloir (" + utc_to_local(datetime.utcnow()).strftime("%Hh%Mm%Ss") + ")\n N'oubliez pas de mettre un message dans votre salon perso disant ce que vous attendez (soumission, aide sur un sujet, etc.)")
            else:
               nqueue.append({"member":user, "category":category_name, "time": obj["time"]})
   
   queue = sorted(nqueue, key=lambda user: user["time"])
   
   msg = "Commandes : \n"
   msg += "```!candidat\n!candidat Nom_Du_Groupe\n!candidat Nom_Du_Candidat (ex: arthur-l)\n!maj\n!dire Nom_Du_Groupe Message\n!sujet\n!sujet suivant\n!nettoie\n!valider\n!valider suivant\n!donner suivant\n!donner Id_Du_Sujet (ex: G.10)```\n"
   
   msg += "Liste des utilisateurs : \n```\n"
   for user in queue:
      msg += get_nick(user["member"]) + " " + user["category"] + "\t\t\t(" + utc_to_local(user["time"]).strftime("%Hh%Mm%Ss") + ") \n"
   msg += "```\n"
   
   await get_channel(guild, 'commandes-bot').purge(limit = 10)
   await get_channel(guild, 'commandes-bot').send(msg)

@client.event
async def on_message(message):
   if message.author == client.user:
      return
      
   words = message.content.split()
   if len(words) != 0 and words[0] == '!candidat':
      if not est_entraineur(message.author):
         return
      if message.author.voice == None:
         await message.channel.send("Vous n'êtes pas dans un salon audio")
         return
      
      await message.channel.purge(limit = 1)
      
      user = None
      if len(words) == 1:
         user = get_category('')
         await move_to(get_category(''), message.author.voice.channel)
      elif words[1] == words[1].upper():
         user = get_category(words[1])
      else:
         for role in message.guild.roles:
            if role.name == "u-" + words[1]:
               user = role.members[0]
         
      if user != None:
         user_channel = get_user_channel(user)
         if user_channel != None:
            await user_channel.send(get_nick(user) + " a discuté avec " + get_nick(message.author) + " (" + utc_to_local(datetime.utcnow()).strftime("%Hh%Mm%Ss") + ")")
         await move_to(user, message.author.voice.channel)
   
   elif len(words) != 0 and words[0] == '!maj':
      await message.channel.purge(limit = 1)
      await update_board(message.channel.guild)
   
   elif len(words) >= 2 and words[0] == "!dire":
      if not est_entraineur(message.author):
         return
      await message.channel.purge(limit = 1)
      await say(words[1], get_nick(message.author) + " : " + message.content[(7 + len(words[1])):], message.channel.guild)
   
   elif len(words) >= 1 and words[0] == "!sujet":
      if message.channel.name.startswith("salon-"):
         await message.channel.purge(limit = 1)
         
         user = get_user(message.channel.name[6:])
         
         if user != None and user['sujet'] != None:
            sujet = get_api(user['sujet'])
            
            if len(words) >= 2 and words[1] == "suivant":
               sujet = get_suivant(sujet)
               
               if sujet == None:
                   await message.channel.send("Pas de sujet suivant dans ce parcours")
                   return
            
            lien = sujet['lien']
            await message.channel.send(str(lien))
            
            recherche = get_recherche(user, sujet)
            if recherche['premiere_lecture'] == None:
               recherche['premiere_lecture'] = datetime.utcnow().isoformat()
               put_api(recherche['url'], recherche)
   
   elif len(words) >= 1 and words[0] == "!valider":
      if not est_entraineur(message.author):
         return
      
      if message.channel.name.startswith("salon-"):
         await message.channel.purge(limit = 1)
         user = get_user(message.channel.name[6:])
         
         if user != None and user['sujet'] != None:
            sujet = get_api(user['sujet'])
            
            if len(words) >= 2 and words[1] == "suivant":
               sujet = get_suivant(sujet)
            
            print(sujet)
            
            recherche = get_recherche(user, sujet)
            if recherche['validation'] == None:
               recherche['validation'] = datetime.utcnow().isoformat()
               put_api(recherche['url'], recherche)
            
            await message.channel.send("Sujet validé !")
   
   elif len(words) >= 2 and words[0] == "!donner":
      if not est_entraineur(message.author):
         return
      
      if message.channel.name.startswith("salon-"):
         await message.channel.purge(limit = 1)
         user = get_user(message.channel.name[6:])
         
         
            
         if words[1] == "suivant":
            if user and user['sujet']:
               sujet = get_api(user['sujet'])
               suiv = get_suivant(sujet)
               if suiv == None:
                  user['sujet'] = None
               else:
                  user['sujet'] = suiv['url']
         else:
            user['sujet'] = get_code(words[1])['url']
         
         put_api(user['url'], user)
         
         sujet = get_api(user['sujet'])
         recherche = get_recherche(user, sujet)
         
         if recherche['demarrage_officiel'] == None:
            recherche['demarrage_officiel'] = datetime.utcnow().isoformat()
         if recherche['premiere_lecture'] == None:
            recherche['premiere_lecture'] = datetime.utcnow().isoformat()
         
         put_api(recherche['url'], recherche) 
         
         lien = sujet['lien']
         await message.channel.send(str(lien))
      
   elif len(words) >= 1 and words[0] == "!nettoie":
      if not est_entraineur(message.author):
         return
      await message.channel.purge(limit = 10)

@client.event
async def on_voice_state_update(member, before, after):
   if before.channel != None and before.channel.name.startswith("couloir"):
      await update_board(member.guild)
   elif after.channel != None and after.channel.name.startswith("couloir"):
      await update_board(member.guild)
   
client.run(TOKEN)
