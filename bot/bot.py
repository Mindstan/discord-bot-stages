import os
import traceback
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

#################### API ####################

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

#################### DISCORD UTILS ####################

def est_entraineur(user):
   for role in user.roles:
      if role.name == "Entraîneur":
         return True
   return False

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

def get_first_user_of_category(category):
   for user in queue:
      if user["category"] == category or category == '':
         return user["member"]  
   return None

#################### CLIENT ACTIONS ####################
   
async def say_to_group(target, message, guild):
   for category in guild.categories:
      if category.name == "GROUPE-" + target:  
         for channel in category.channels:
            if channel.name.startswith("salon-"):
               await channel.send(message)
         return True

async def update_board(guild):
   members_in_queue = {str(user['member']) : user for user in queue}
   queue.clear()

   for category in guild.categories:
      if category.name.startswith("GROUPE-"):
         category_name = category.name[7:]
         couloir = get_channel(guild, 'couloir-' + category_name)

         if couloir:
            for user in couloir.members:
               old_user = members_in_queue.get(str(user), None)
               if old_user is None:
                  queue.append({
                     "member": user,
                     "category": category_name,
                     "time":datetime.utcnow()
                  })
                  
                  user_channel = get_user_channel(user)
                  if user_channel != None:
                     await user_channel.send(
                        ("{nick} a rejoint le couloir ({at_time})\n"
                        "N'oubliez pas de mettre un message dans votre salon perso disant ce que vous attendez (soumission, aide sur un sujet, etc.)").format(
                           nick=get_nick(user),
                           at_time=utc_to_local(datetime.utcnow()).strftime("%Hh%Mm%Ss")
                        ))
               else:
                  queue.append({
                     "member": user,
                     "category": category_name,
                     "time": old_user["time"]
                  })
   
   queue.sort(key=lambda user: user["time"])
   
   msg = ("Commandes : \n"
      "```!candidat [Nom_Du_Groupe | Nom_Du_Candidat] (ex : !candidat arthur-l)\n"
      "!maj\n"
      "!dire Nom_Du_Groupe Message\n"
      "!sujet [suivant]\n"
      "!sujet suivant\n"
      "!nettoie [nb_lines]\n"
      "!valider [suivant]\n"
      "!donner [suivant | Id_Du_Sujet]  (ex : !donner G.10)\n"
      "```\n\n"
   
      "Liste des utilisateurs : \n"
      "```\n{user_list}```\n")

   user_list = ["{nick} {category}\t\t\t({time})\n".format(
         nick=get_nick(user["member"]),
         category=user["category"],
         time=utc_to_local(user["time"]).strftime("%Hh%Mm%Ss"),
      ) for user in queue]

   msg = msg.format(user_list=''.join(user_list))
   
   await get_channel(guild, 'commandes-bot').purge(limit = 10)
   await get_channel(guild, 'commandes-bot').send(msg)

#################### COMMANDS ####################

async def cmd_candidat(message, username=None, *args):
   if message.author.voice == None:
      await message.channel.send("Vous n'êtes pas dans un salon audio")
      return
   
   user = None
   
   if username is None:
      user = get_first_user_of_category('')
   elif username.startswith('<@!') and message.mentions: # Mention
      user = message.mentions[0]
   elif username == username.upper(): # caps : category
      user = get_first_user_of_category(username)
   else:
      for role in message.guild.roles:
         if role.name == "u-" + username:
            user = role.members[0]
      
   if user is not None:
      user_channel = get_user_channel(user)
      if user_channel is not None:
         await user_channel.send("{user} a discuté avec {author} ({time})".format(
               user=get_nick(user),
               author=get_nick(message.author),
               time=utc_to_local(datetime.utcnow()).strftime("%Hh%Mm%Ss"),
            ))
      await user.move_to(message.author.voice.channel)
      return True
   elif username:
      await message.channel.send("Impossible de trouver l'utilisateur {}".format(username))

async def cmd_maj(message, *args):
   await update_board(message.channel.guild)
   return True

async def cmd_dire(message, group_name='', *args):
   msg_text = "{author} : {message}".format(
      author = get_nick(message.author),
      message = ' '.join(message.content.split(maxsplit=2)[2:]),
   )
   sended = await say_to_group(group_name, msg_text, message.channel.guild)
   if not sended:
      await message.channel.send("Groupe GROUPE-{} non toruvé".format(group_name))
   return sended

async def cmd_sujet(message, sujet_suivant=None, *args):
   if not message.channel.name.startswith("salon-"):
      return await message.channel.send("Cette commande ne peut pas être utilisée dans ce canal")

   user = get_user(message.channel.name[6:])
   
   if user != None and user['sujet'] != None:
      sujet = get_api(user['sujet'])
      
      if sujet_suivant == "suivant":
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
      return True
   else:
      return await message.channel.send("Utilisateur invalide")

async def cmd_valider(message, arg_suivant=None, *args):
   if not message.channel.name.startswith("salon-"):
      return await message.channel.send("Cette commande ne peut pas être utilisée dans ce canal")
   user = get_user(message.channel.name[6:])

   if user is None:
      return await message.channel.send("Utilisateur non trouvé")
   if user['sujet'] is None:
      return await message.channel.send("Pas de sujet en cours")
   
   sujet = get_api(user['sujet'])
   
   if arg_suivant == "suivant":
      sujet = get_suivant(sujet)
   
   print(sujet)
   
   recherche = get_recherche(user, sujet)
   if recherche['validation'] == None:
      recherche['validation'] = datetime.utcnow().isoformat()
      put_api(recherche['url'], recherche)
   
   parcours = get_api(sujet['parcours'])
   await message.channel.send("Sujet " + parcours['code'] + "." + str(sujet['ordre']) + ") " + sujet['nom'] + " validé par " + get_nick(message.author))
   if sujet['correction'] != None and sujet['correction'] != "":
      await message.channel.send(sujet['correction'])
   return True

async def cmd_donner(message, sujet_nom=None, *args):
   if sujet_nom is None:
      return await message.channel.send("Cette commande nécessite de donner le nom du sujet")
   if not message.channel.name.startswith("salon-"):
      return await message.channel.send("Cette commande ne peut être utilisée dans ce canal")

   user = get_user(message.channel.name[6:])
   if user is None:
      return await message.channel.send("Utilisateur non trouvé")
   
   if sujet_nom == "suivant":
      if user['sujet']:
         sujet = get_api(user['sujet'])
         suiv = get_suivant(sujet)
         if suiv is None:
            user['sujet'] = None
         else:
            user['sujet'] = suiv['url']
   else:
      sujet_code = get_code(sujet_nom)
      if sujet_code is not None:
         user['sujet'] = sujet_code['url']
      else:
         return await message.channel.send("Sujet '{}' non trouvé".format(sujet_nom))
   
   put_api(user['url'], user)
   
   sujet = get_api(user['sujet'])
   if sujet is None:
      return await message.channel.send("Sujet '{}' non trouvé".format(sujet_nom))

   recherche = get_recherche(user, sujet)
   
   if recherche['demarrage_officiel'] == None:
      recherche['demarrage_officiel'] = datetime.utcnow().isoformat()
   if recherche['premiere_lecture'] == None:
      recherche['premiere_lecture'] = datetime.utcnow().isoformat()
   
   put_api(recherche['url'], recherche) 
   
   lien = sujet['lien']
   await message.channel.send(str(lien))
   return True

async def cmd_nettoie(message, n=10, *args):
   try:
      n = int(n)
   except ValueError:
      n = 10
   await message.channel.purge(limit = n+1) # +1 for the command

COMMANDS = { # (cmd_function, trainer_role_required)
   'candidat' : (cmd_candidat, True),
   'maj' : (cmd_maj, False),
   'dire' : (cmd_dire, True),
   'sujet' : (cmd_sujet, False),
   'valider' : (cmd_valider, True),
   'donner' : (cmd_donner, True),
   'nettoie' : (cmd_nettoie, True),
}

#################### CLIENT & EVENTS ####################

@client.event
async def on_ready():
   print('%s has connected to Discord!' % client.user)
   for guild in client.guilds:
      await update_board(guild)

@client.event
async def on_message(message):
   if message.author == client.user or not message.content.startswith('!'):
      return
      
   words = message.content.split()
   command = words[0][1:] # Without '!'

   if command in COMMANDS:
      fct, require_trainer = COMMANDS[command]
      if require_trainer and not est_entraineur(message.author):
         await message.channel.send('Vous n\'êtes pas entraîneur, vous ne pouvez pas utiliser cette commande')
      else:
         try:
            if await fct(message, *words[1:]) is True:
               try:
                  await message.delete()
               except discord.errors.NotFound:
                  pass # Message already deleted
         except:
            tb = traceback.format_exc()
            print(tb)
            await message.channel.send('Une erreur est survenue : \n' + tb)
   else:
      await message.channel.send('La commande {} n\'existe pas'.format(command))

@client.event
async def on_voice_state_update(member, before, after):
   if before.channel != None and before.channel.name.startswith("couloir"):
      await update_board(member.guild)
   elif after.channel != None and after.channel.name.startswith("couloir"):
      await update_board(member.guild)
   
client.run(TOKEN)
