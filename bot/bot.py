import os
import traceback
import asyncio
import discord
import aiohttp
from datetime import datetime
import dateutil.parser
from dotenv import load_dotenv
import pytz

class BotClient(discord.Client):   
   async def connect(self, *args, **kwargs):
      self.api_session = aiohttp.ClientSession()
      await super().connect(*args, **kwargs)

   async def close(self):
      await super().close()
      await self.api_session.close()

local_tz = pytz.timezone('Europe/Paris')

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = os.getenv('API_URL')
API_TOKEN = os.getenv('API_TOKEN', '')

client = BotClient()
queue = []

class APIError(Exception):
   pass

#################### API ####################

API_HEADERS = {"Authorization": API_TOKEN, "Content-type": "application/json"}

async def get_api(url):
   async with client.api_session.get(url, headers=API_HEADERS) as resp:
      return await resp.json()

async def put_api(url, data):
   async with client.api_session.put(url, headers=API_HEADERS, json=data) as resp:
      return await resp.json()

async def post_api(url, data):
   async with client.api_session.post(url, headers=API_HEADERS, json=data) as resp:
      return await resp.json()

async def get_user_api(name):
   users = await get_api(API_URL + "/api/candidat/")
   
   for user in users:
      if user['discord_name'] == name:
         return user
   return None

async def get_recherche_api(candidat, sujet):
   if sujet is None:
      return None
   recherches = await get_api(API_URL + "/api/recherche?sujet=" + str(sujet['id']) + "&candidat=" + str(candidat['id']))
   
   if len(recherches) >= 1:
      return recherches[0]
   
   nouv = await post_api(API_URL + "/api/recherche/", {
      "candidat": candidat['url'],
      "sujet": sujet['url']
   })
   return nouv
   
async def get_suivant_api(sujet):
   if sujet is None:
      return None
   sujets = await get_api(API_URL + "/api/sujet/")
   
   for nouv in sujets:
      if nouv['parcours'] == sujet['parcours'] and nouv['ordre'] == sujet['ordre'] + 1:
         return nouv
   
   return None

async def get_code_api(code):
   sujets = await get_api(API_URL + "/api/sujet/")
   parcours = await get_api(API_URL + "/api/parcours/")
   
   p = {}
   for parcour in parcours:
      p[parcour['url']] = parcour
   
   for nouv in sujets:
      if nouv['parcours'] is None:
         raise APIError("Erreur dans la base de données : La clé 'parcours' associée au sujet d'id {} ({}) vaut None".format(nouv['id'], nouv['nom']))
      if p[nouv['parcours']]['code'] + '.' + str(nouv['ordre']) == code:
         return nouv
   
   return None

#################### DISCORD UTILS ####################

def est_invisile(user): # Non notifé par le bot
   for role in user.roles:
      if role.name == "Invisible":
         return True
   return False

def est_entraineur(user):
   for role in user.roles:
      if (role.name == "Entraîneur") or (role.name == "Bot-validateur"):
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

def get_role_members(guild, name):
   for role in guild.roles:
      if role.name == name:
         return role.members
   return []
   
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

async def get_sujet_of_msg(sujet_name, message, user):
   if user is None:
      await message.channel.send("Utilisateur non trouvé")
      return None
   if user['sujet'] is None:
      await message.channel.send("Pas de sujet en cours")
      return None

   if sujet_name == "suivant":
      sujet = await get_api(user['sujet'])
      sujet = await get_suivant_api(sujet)
      if sujet is None:
         await message.channel.send("Pas de sujet suivant dans ce parcours")
         return None
   elif sujet_name is not None:
      sujet_code = await get_code_api(sujet_name)
      if sujet_code is None:
         await message.channel.send("Sujet '{}' inconnu".format(sujet_name))
         return None
      sujet = await get_api(sujet_code['url'])
   else:
      sujet = await get_api(user['sujet'])
      if sujet is None:
         await message.channel.send("Pas de sujet en cours")
         return None
   return sujet

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
                     "time": datetime.utcnow()
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
      "```"
      "!candidat [Nom_Du_Groupe | Nom_Du_Candidat] (ex : !candidat arthur-l)\n"
      "!maj\n"
      "!dire Nom_Du_Groupe Message\n"
      "!sujet [suivant]\n"
      "!nettoie [nb_lignes]\n"
      "!valider [suivant | Id_Du_Sujet]\n"
      "!donner [suivant | Id_Du_Sujet]  (ex : !donner G.10)\n"
      "!pause [utilisateur | nom-du-groupe | ALL]  (ex : !pause GROUPE-ALGOREA-1)\n"
      "!reprendre [utilisateur | nom-du-groupe | ALL]  (ex : !reprendre ALL)\n"
      "```\n\n"
   
      "Liste des utilisateurs : \n"
      "```\n{user_list}```\n")

   user_list = ["{nick} {category}\t\t\t({time})\n".format(
         nick=get_nick(user["member"]),
         category=user["category"],
         time=utc_to_local(user["time"]).strftime("%Hh%Mm%Ss"),
      ) for user in queue]

   msg = msg.format(user_list=''.join(user_list))
   
   await get_channel(guild, 'commandes-bot').purge(limit = 20)
   await get_channel(guild, 'commandes-bot').send(msg)

async def notify_trainers(): # Won't work with mutliple servers
   await client.wait_until_ready()
   SLEEP_TIME = 30
   NOTIFY_INTERVAL = 120
   NOTIFY_DELAY = 120

   last_notification = datetime.min
   last_notif_msg = None

   while not client.is_closed():
      users_waiting = False
      if queue == []:
         last_notification = datetime.min

      # Check if some users are in the queue since 
      for users in queue:
         delta_delay = (datetime.utcnow() - users['time']).total_seconds()
         delta_interval = (datetime.utcnow() - last_notification).total_seconds()

         if delta_delay > NOTIFY_DELAY and delta_interval > NOTIFY_INTERVAL:
            last_notification = datetime.utcnow()
            users_waiting = True
            break
      if users_waiting:
         for guild in client.guilds:
            trainers = get_role_members(guild, "Entraîneur")
            available_trainers = []

            for trainer in trainers:
               # Si l'entraineur est seul dans un salon audio ET n'a pas le rôle "invisible", il sera notifé
               if trainer.voice and not est_invisile(trainer) and len(trainer.voice.channel.members) == 1:
                  available_trainers.append(trainer)

            if available_trainers:
               mentions = [user.mention for user in available_trainers]
               msg = ' '.join(mentions)
               if last_notif_msg:
                  try:
                     await last_notif_msg.delete()
                  except discord.errors.NotFound:
                     pass
               last_notif_msg = await get_channel(guild, 'commandes-bot').send(msg)

      await asyncio.sleep(SLEEP_TIME)

# ---------- Gestion des pauses


async def get_target_of(message, target):
   if target is None and message.channel.name.startswith("salon-"):
      user = await get_user_api(message.channel.name[6:])
      if user is None:
         print("WARNING : !pause concernait un utilisateur n'étant pas dans la BDD")
         return []
      return [user]
   elif target:
      chans = []
      for c in message.guild.channels:
         if target == 'ALL':
            if isinstance(c, discord.TextChannel) and c.name.startswith('salon-'):
               chans.append(c)
         elif isinstance(c, discord.TextChannel) and c.name == 'salon-' + target:
            chans.append(c)
         elif isinstance(c, discord.CategoryChannel) and c.name == target:
            for c2 in c.channels:
               if isinstance(c2, discord.TextChannel) and c2.name.startswith('salon-'):
                  chans.append(c2)
      users = []
      for c in chans:
         user = await get_user_api(c.name[6:])
         if user is None:
            print("WARNING : !pause concernait un utilisateur n'étant pas dans la BDD")
         else:
            users.append(user)
      return users
   else:
      await message.channel.send("Pour mettre un pause un ou des utilisateurs, merci de préciser la cible ('ALL', un groupe ou un utilisateur (en le mentionnant avec @...) ou de vous placer dans le salon d'un utilisateur")
   return None


async def set_pause_state(users_list, set_pause):
   for user in users_list:
      if user['sujet'] is not None:
         sujet_url = user['sujet']
         if isinstance(sujet_url, dict):
            sujet_url = sujet_url['url']
         recherche = await get_recherche_api(user, {
             'id': user['sujet_id'],
             'url': sujet_url,
         })
         if recherche['faux_debut'] == None:
            recherche['faux_debut'] = recherche['demarrage_officiel']
         if recherche['validation'] is not None:
            continue  # Inutile de mettre en pause un sujet fini...

         if set_pause and recherche['debut_pause'] is None:
            recherche['debut_pause'] = datetime.utcnow().isoformat()
         elif not set_pause and recherche['debut_pause'] is not None:
            deb = dateutil.parser.isoparse(recherche['faux_debut'])
            fin = dateutil.parser.isoparse(recherche['debut_pause'])
            new_false = datetime.utcnow() - (fin - deb)

            recherche['debut_pause'] = None
            recherche['faux_debut'] = new_false.isoformat()
         else:
            continue  # Rien à update pour le candidat, pas la peine de surcharger l'API

         await put_api(recherche['url'], recherche)

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
      members = get_role_members(message.guild, "u-" + username)
      if members:
         user = members[0]
      
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
   else:
      await message.channel.send("Aucun utilisateur en attente")
      return True

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
      await message.channel.send("Cette commande ne peut pas être utilisée dans ce canal")
      return None

   user = await get_user_api(message.channel.name[6:])
   sujet = await get_sujet_of_msg(sujet_suivant, message, user)
   if sujet is None:
      return None
   
   lien = sujet['lien']
   recherche = await get_recherche_api(user, sujet)
   label = '[En cours]'
   if recherche['validation'] is not None:
      label = '[Validé]'
   elif recherche['debut_pause'] is not None:
      label = '[En pause]'
   await message.channel.send("Sujet actuel : {} {}".format(sujet['nom'], label))
   await message.channel.send(str(lien))
   
   recherche = await get_recherche_api(user, sujet)
   if recherche['premiere_lecture'] == None:
      recherche['premiere_lecture'] = datetime.utcnow().isoformat()
      await put_api(recherche['url'], recherche)
   return True

async def cmd_valider(message, arg_suivant=None, *args):
   if not message.channel.name.startswith("salon-"):
      await message.channel.send("Cette commande ne peut pas être utilisée dans ce canal")
      return None
   user = await get_user_api(message.channel.name[6:])

   sujet = await get_sujet_of_msg(arg_suivant, message, user)
   if sujet is None:
      return None
      
   recherche = await get_recherche_api(user, sujet)
   if recherche['validation'] == None:
      recherche['validation'] = datetime.utcnow().isoformat()
      await put_api(recherche['url'], recherche)
   
   parcours = await get_api(sujet['parcours'])
   await message.channel.send("Sujet " + parcours['code'] + "." + str(sujet['ordre']) + ") " + sujet['nom'] + " validé par " + get_nick(message.author))
   if sujet['correction'] != None and sujet['correction'] != "":
      await message.channel.send(sujet['correction'])
   return True

async def cmd_donner(message, sujet_nom=None, *args):
   if sujet_nom is None:
      await message.channel.send("Cette commande nécessite de donner le nom du sujet")
      return None
   if not message.channel.name.startswith("salon-"):
      await message.channel.send("Cette commande ne peut être utilisée dans ce canal")
      return None

   user = await get_user_api(message.channel.name[6:])
   if user is None:
      await message.channel.send("Utilisateur non trouvé")
      return None
   
   if user['sujet']:
      await set_pause_state([user], True) # Si le sujet n'est pas validé, mise en pause
   
   if sujet_nom == "suivant":
      if user['sujet']:
         sujet = await get_api(user['sujet'])
         suiv = await get_suivant_api(sujet)
         if suiv is None:
            user['sujet'] = None
         else:
            user['sujet'] = suiv['url']
   else:
      sujet_code = await get_code_api(sujet_nom)
      if sujet_code is not None:
         user['sujet'] = sujet_code['url']
      else:
         await message.channel.send("Sujet '{}' non trouvé".format(sujet_nom))
         return False

   await put_api(user['url'], user)
   
   sujet = await get_api(user['sujet'])
   if sujet is None:
      await message.channel.send("Sujet '{}' non trouvé".format(sujet_nom))
      return None

   recherche = await get_recherche_api(user, sujet)
   user['sujet'] = sujet
   user['sujet_id'] = sujet['id']

   if recherche['demarrage_officiel'] is None:
      recherche['demarrage_officiel'] = datetime.utcnow().isoformat()
   if recherche['premiere_lecture'] is None:
      recherche['premiere_lecture'] = datetime.utcnow().isoformat()

   await put_api(recherche['url'], recherche)

   if recherche['debut_pause'] is not None:
      await set_pause_state([user], False) # Si le sujet était en cours, on reprends
   
   lien = sujet['lien']
   await message.channel.send(str(lien))
   return True

async def cmd_nettoie(message, n=10, *args):
   try:
      n = int(n)
   except ValueError:
      n = 10
   await message.channel.purge(limit=n + 1)  # +1 for the command

def get_chans_of_users(users, guild):
   users = set([u['discord_name'] for u in users])
   user_chans = []
   for chan in guild.channels:
      if chan.name.startswith('salon-') and chan.name[6:] in users:
         user_chans.append(chan)
   return user_chans
   
async def cmd_pause(message, target=None, *args):
   users = await get_target_of(message, target)
   if users is None:
      return False
   users_names = ["{} {}".format(u['prenom'], u['nom']) for u in users]
   await set_pause_state(users, True)

   for chan in get_chans_of_users(users, message.guild):
      await chan.send("**Début de la pause**")

   await message.channel.send("Mise en pause de : {}".format(', '.join(users_names)))
   return True

async def cmd_reprendre(message, target=None, *args):
   users = await get_target_of(message, target)
   if users is None:
      return False
   users_names = ["{} {}".format(u['prenom'], u['nom']) for u in users]
   await set_pause_state(users, False)

   for chan in get_chans_of_users(users, message.guild):
      await chan.send("**Reprise du stage**")

   await message.channel.send("Reprise pour : {}".format(', '.join(users_names)))
   return True

COMMANDS = { # (cmd_function, trainer_role_required)
   'candidat' : (cmd_candidat, True),
   'maj' : (cmd_maj, False),
   'dire' : (cmd_dire, True),
   'sujet' : (cmd_sujet, False),
   'valider' : (cmd_valider, True),
   'donner' : (cmd_donner, True),
   'nettoie' : (cmd_nettoie, True),
   'pause' : (cmd_pause, True),
   'reprendre' : (cmd_reprendre, True),
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

   if command not in COMMANDS:
      await message.channel.send('La commande {} n\'existe pas'.format(command))
      return

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
      except aiohttp.client_exceptions.ClientConnectorError as e:
         host = '{} {}'.format(e.host, e.port)
         print("[ERROR]", e)
         await message.channel.send("Impossible de se connecter à l'API ({})".format(host))
      except aiohttp.client_exceptions.ContentTypeError as e:
         print('[ERROR]', e, e.args)
         reqInfos = e.args[0]
         await message.channel.send("Erreur de la part de l'API ({} {}) : {}".format(reqInfos.method, reqInfos.url, e.message))
      except aiohttp.client_exceptions.ClientError as e:
         await message.channel.send("Erreur avec l'API : {}\n\n{}".format(e, e.args))
         print("[API ERROR]", e)
         print(traceback.format_exc())
      except APIError as e:
         print("[ERREUR DE L'API]", e)
         await message.channel.send("[ERREUR DE L'API] {}".format(e))
      except:
         tb = traceback.format_exc()
         print(tb)
         if len(tb) > 1900:
            tb = tb[:1900] + "[...] (traceback too long to be displayed)"
         await message.channel.send('Une erreur est survenue : \n' + tb)

@client.event
async def on_voice_state_update(member, before, after):
   if before.channel != None and before.channel.name.startswith("couloir"):
      await update_board(member.guild)
   elif after.channel != None and after.channel.name.startswith("couloir"):
      await update_board(member.guild)

client.loop.create_task(notify_trainers())
client.run(TOKEN)
