# Written 11 - 29 -2021
# Author: Morgana Iacocca - morgana.iacocca@gmail.com
# Purpose: To do everything I need to run Demigods

import os 
import random
import math
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
serversDict = {}

# ctx.author.mention
# ctx.guild for server name
# ctx.author.send(message) for DMs

class PbtAGame:
   def __init__(self, dms, players, pcs, npcs, basicMoves, spindle, playbooks):
      self.dms = dms                # str[]  - discord tags of DMs
      self.players = players        # {str: PbtACharacter}   - discord tags of player map to character object
      self.pcs = pcs                # {str: PbtACharacter}   - character nickname maps to character object
      self.npcs = npcs              # {str: PbtACharacter}   - character nickname maps to character object
      self.basicMoves = basicMoves  # {str: PbtAMove}        - move name maps to move object
      self.spindle = spindle        # str
      self.playbooks = playbooks    # {str: PbtAPlaybook}    - playbook name maps to playbook object
      
   # Assumes all information is valid
   def makeMove(self, characterName, movename, type, bonus, replacement):
      actor = 0
      move = 0
      mod = 0
      modified = False
      if(characterName in self.pcs):
         actor = self.pcs[characterName]
      elif(characterName in self.npcs):
         actor = self.npcs[characterName]
      else:
         return "Character could not be found."
         
      if(movename in actor.moves):
         move = actor.moves[movename]
      elif(movename in self.basicMoves):
         move = self.basicMoves[movename]
      else:
         return "Move could not be found, or is unavailable."
      
      if (replacement == "none"):
         if (move.modifier in actor.stats):
            mod = actor.stats[move.modifier]
         elif(move.modifier == "Harm"):
            mod = actor.harm
         else:
            mod = 0
      else:
         modified = True
         if(replacement in actor.stats):
            mod = actor.stats[replacement]
         elif(replacement == "Harm"):
            mod = actor.harm
         elif(replacement.isnumeric()):
            mod = int(replacement)
         else:
            mod = 0        
      
      response = "**Name**: " + move.name +"\n=============================\n"
      response = response + "**Description:**\n\t" +  move.description
      
      if(move.count > 0):
         response = response + "\n=============================\n"
         response = response + "**Roll**: " + str(move.count)+"d"+str(move.sides) + " + "
         if(modified):
            response = response + replacement
         else:
            response = response + move.modifier
         response = response + " + Bonus\n**Dice:** "
         roll = ()
         if(type == "Favor"):
            roll = rollDice(move.count+1, move.sides, "h", move.count)
         elif(type == "Disfavor"):
            roll = rollDice(move.count+1, move.sides, "l", move.count)
         else:
            roll = rollDice(move.count, move.sides, "n", move.count)
         temp = ""
         for dieResult in roll[0]:
            temp = temp + str(dieResult) + ", "
         response = response + temp[0:len(temp)-2] + "\n"
         response = response + "**Result:** "
         diceSum = sum(roll[1]) + bonus + mod
         for dieResult in roll[1]: 
            response = response + str(dieResult) + " + "
         response = response + str(mod) + " + " + str(bonus) + " = " + str(diceSum) + "\n**Outcome:**\n\t"
         if(diceSum <= 6):
            if("6- " in move.outcomes):
               response = response + move.outcomes["6- "] + "\n"
            response = response + "\t Herald makes a Hard Move\n"
         elif(diceSum <= 9):
            if("7-9" in move.outcomes):
               response = response + move.outcomes["7-9"] + "\n"
            else:
               response = response + "No outcome\n"
         elif(diceSum <= 13):
            if("10+" in move.outcomes):
               response = response + move.outcomes["10+"] + "\n"
            else:
               response = response + "No outcome\n"
         else:
            if(move.name in actor.godlikes):
               if("13+" in move.outcomes):
                  response = response + move.outcomes["13+"] + "\n"
               else:
                  response = response + "No outcome\n"
            else:
               if("10+" in move.outcomes):
                  response = response + move.outcomes["10+"] + "\n"
               else:
                  response = response + "No outcome\n"
      if(len(move.choices) > 0):
         response = response + "=============================\n"
         response = response + "**Choices**:"
         for choice in move.choices:
            response = response + "\n--------------------\n"
            response = response + "*" + choice + "*"
            for choic in move.choices[choice]:
               response = response + "\n\t - " + choic
      return response               
      

class PbtAPlaybook:
   def __init__(self, name, description, ascendanceMove, deathMove, baseStats, items, moves, tangles, advancements, furtherAdvancements, gainThread):
      self.name = name
      self.description = description
      self.ascendanceMove = ascendanceMove
      self.deathMove = deathMove
      self.baseStats = baseStats
      self.items = items
      self.moves = moves
      self.tangles = tangles
      self.advancements = advancements
      self.furtherAdvancements = furtherAdvancements
      self.gainThread = gainThread

class PbtACharacter:
   def __init__(self, fname, players, name, pronouns, parent, pantheon, art, armor, harm, attack, thread, playbook, stats, godlikes, items, moves, conditions, tangleTable, tangles, backstory, description):
      self.fname = fname               # str
      self.players = players           # str[]
      self.name = name                 # str
      self.pronouns = pronouns         # str
      self.parent = parent             # str
      self.pantheon = pantheon         # str
      self.art = art                   # str
      self.armor = armor               # int
      self.harm = harm                 # int
      self.attack = attack             # int
      self.thread = thread             # int
      self.playbook = playbook         # str
      self.stats = stats               # {str: int}
      self.godlikes = godlikes         # str[]
      self.items = items               # {str: str}
      self.moves = moves               # {str: PbtAMove}
      self.conditions = conditions     # str[]
      self.tangleTable = tangleTable   # {str: int}
      self.tangles = tangles           # str[]
      self.backstory = backstory       # {str: str}
      self.description = description   # {str: str}
      
   def getInfo(self, infoName):
      response = []
      if(infoName == "Players"):
         response = [self.fname + "'s players are: " + " ".join(self.players[::2])]
      elif(infoName == "Name"):
         response = [self.fname + "'s full name is " + self.name]
      elif(infoName == "Pronouns"):
         response = [self.fname + "'s pronouns are " + self.pronouns]
      elif(infoName == "Parent"):
         response = [self.fname + "'s divine parent is " + self.parent]
      elif(infoName == "Pantheon"):
         response = [self.fname + " descends from the " +self.pantheon + " pantheon"]
      elif(infoName == "Art"):
         response = [self.art]
      elif(infoName == "Armor"):
         response = [self.fname + " has " + str(self.armor) + " Armor"]
      elif(infoName == "Harm"):
         response = [self.fname + " has " + str(self.harm) + " Harm"]
      elif(infoName == "Attack"):
         response = [self.fname + " has " + str(self.attack) + " Attack"]
      elif(infoName == "Threads"):
         response = [self.fname + " has " + str(self.thread) + " Threads"]
      elif(infoName == "Playbook"):
         response = [self.fname + " uses the " + self.playbook + " playbook"]
      elif(infoName == "Stats"):
         message = self.fname + "'s Stats are:"
         for stat in self.stats:
            message = message + "\n\t" + stat + ": " + str(self.stats[stat])
         response = [message]
      elif(infoName == "Godlikes"):
         response = [self.fname + " is Godlike in the following moves:\n\t" + "\n\t".join(self.godlikes)]
      elif(infoName == "Items"):
         message = self.fname + " has the following items/gifts: "
         for item in self.items:
            message = message + "\n\t**" + item + "**: " + self.items[item]
         response = [message]
      elif(infoName == "Moves"):
         response.append(self.fname + " has the following moves:")
         for move in self.moves:
            response.append(self.moves[move].toString())    
      elif(infoName == "Conditions"):
         response = [self.fname + " has the following conditions:\n\t" + "\n\t".join(self.conditions)] 
      elif(infoName == "Tangles"):
         response = self.tangles
      elif(infoName == "Backstory"):
         response.append(self.fname + " has the following backstory:\n")
         for backstorypiece in self.backstory:
            response.append("**"+backstorypiece+"**: "+self.backstory[backstorypiece])
      elif(infoName == "Description"):
         response.append(self.fname + " has the following description:\n")
         for descpiece in self.description:
            response.append("**"+descpiece+"**: "+self.description[descpiece])
      else:
         response = ["Information could not be found"]
      return response      
   
   def updateSheet(self):
      file = open(self.fname + ".txt", "w")
      playerline = ""
      for player in self.players:
         playerline = playerline + player + " "
      file.write(playerline.strip()+"\n")
      file.write(self.name + "\n")
      file.write(self.pronouns + "\n")
      file.write(self.parent + "\n")
      file.write(self.pantheon + "\n")
      file.write(self.art + "\n")
      file.write(str(self.armor) + "\n")
      file.write(str(self.harm) + "\n")
      file.write(str(self.attack) + "\n")
      file.write(str(self.thread) + "\n")
      file.write(self.playbook + "\n")
      for stat in self.stats:
         file.write(stat + " " + str(self.stats[stat]) + "\n")
      file.write("Godlikes\n")
      for godlike in self.godlikes:
         file.write(godlike+"\n")
      file.write("Items\n")
      for item in self.items:
         file.write(item + " Description: " + self.items[item] + "\n")
      file.write("Moves\n")
      for move in self.moves:
         mov = self.moves[move]
         file.write(mov.name + "\n" + mov.description + "\n")
         file.write("Roll " + str(mov.count) + " " + str(mov.sides) + " " + mov.modifier + "\n")
         for outcome in mov.outcomes:
            file.write(outcome + " " + mov.outcomes[outcome] + "\n")
         file.write("EndOutcomes\nChoices")
         for choice in mov.choices:
            file.write(" " + choice)
         file.write("\n")
         for choic in mov.choices:
            file.write(choic + "\n")
            for choi in mov.choices[choic]:
               file.write(choi + "\n")
         file.write("EndMove\n")
      file.write("Conditions\n")
      for condition in self.conditions:
         file.write(condition + "\n")
      file.write("TangleTable\n")
      for person in self.tangleTable:
         file.write(person + " " + str(self.tangleTable[person]) + "\n")
      file.write("Tangles\n")
      for tangle in self.tangles:
         file.write(tangle + "\n")
      file.write("Backstory\n")
      for backpiece in self.backstory:
         file.write(backpiece + " BeginText " + self.backstory[backpiece] + "\n") 
      file.write("Description\n")
      for descpiece in self.description:
         file.write(descpiece + " BeginText " + self.description[descpiece] + "\n")
      file.write("E0F")  
      file.close()

class PbtAMove:
   def __init__(self, name, description, count, sides, modifier, outcomes, choices):
      self.name = name                # str 
      self.description = description  # str 
      self.count = count              # int
      self.sides = sides              # int
      self.modifier = modifier        # str
      self.outcomes = outcomes        # {str: str}
      self.choices = choices          # {str: str[]}
   
   def toString(self):
      message = "**Move Name:** "+self.name+"\n**Description:** " + self.description
      if(self.count > 0):
         message = message + "\nRoll " + str(self.count) + "d" + str(self.sides) + " + " + self.modifier
      if(len(self.outcomes) > 0):
         for outcome in self.outcomes:
            prereq = "%3s" % outcome
            message = message + "\n\t" + prereq + ": " + self.outcomes[outcome]
      if(len(self.choices) > 0):
         message = message + "\n**Choices:**"
         for cho in self.choices:
            message = message + "\n" + cho
            for choi in self.choices[cho]:
               message = message + "\n\t - " + choi
      return message      

def readUntil(lines, breaker):
   response = [] 
   index = 0
   for i in range(0, len(lines)):
      if(lines[i] == breaker):
         break
      else:
         response.append(lines[i])
         index += 1
   return (index, response)

# dms, players, pcs, npcs, basicMoves, spindle, playbooks
def loadGame(fname):
   file = open(fname+".txt")
   lines = file.read().splitlines()
   file.close()
   response = readUntil(lines, "Players")
   lines = lines[response[0]:]
   dms = []
   for line in response[1][1:]:
      linelist = line.split()
      dms.append(linelist[0])
      dms.append(linelist[1])
   response = readUntil(lines, "NPC Files")
   lines = lines[response[0]:]
   players = {}
   pcs = {}
   for line in response[1][1:]:
      linelist = line.split()
      players[linelist[0]] = linelist[2]
      players[linelist[1]] = linelist[2]
      pcs[linelist[2]] = loadCharacter(linelist[2])
   response = readUntil(lines, "Spindle")
   lines = lines[response[0]:]
   npcs = {}
   for line in response[1][1:]:
      npcs[line] = loadCharacter(line)
   response = readUntil(lines, "Playbooks")
   lines = lines[response[0]:]
   spindle = response[1][1]
   response = readUntil(lines, "Basic Moves")
   lines = lines[response[0]:]
   playbooks = {}
   for line in response[1][1:]:
      playbooks[line] = "REPLACE ME"
   response = readUntil(lines, "E0F")
   basicMoves = loadBasicMoves(response[1][1])
   return PbtAGame(dms, players, pcs, npcs, basicMoves, spindle, playbooks)
    
# fname, players, name, pronouns, parent, pantheon, art, armor, harm, attack, thread, playbook, 
# stats, items, moves, conditions, tangles, backstory, description    
def loadCharacter(fname):
   file = open(fname+".txt")
   lines = file.read().splitlines()
   file.close()
   players = lines[0].split()
   name = lines[1]
   pronouns = lines[2]
   parent = lines[3]
   pantheon = lines[4]
   art = lines[5]
   armor = int(lines[6])
   harm = int(lines[7])
   attack = int(lines[8])
   thread = int(lines[9])
   playbook = lines[10]
   lines = lines[11:]
   response = readUntil(lines, "Godlikes")
   lines = lines[response[0]:]
   stats = {}
   for stat in response[1]:
      line = stat.split()
      stats[line[0]] = int(line[1])
   response = readUntil(lines, "Items")
   lines = lines[response[0]:]
   godlikes = []
   for line in response[1][1:]:
      godlikes.append(line)
   response = readUntil(lines, "Moves")
   lines = lines[response[0]:]
   items = loadItems(response[1][1:])
   response = readUntil(lines, "Conditions")
   lines = lines[response[0]:]
   moves = loadMoves(response[1][1:])
   response = readUntil(lines, "TangleTable")
   lines = lines[response[0]:]
   conditions = response[1][1:]
   response = readUntil(lines, "Tangles")
   lines = lines[response[0]:]
   tangleTable = {}
   for person in response[1][1:]:
      line = person.split()
      tangleTable[line[0]] = int(line[1])   
   response = readUntil(lines, "Backstory")
   lines = lines[response[0]:]
   tangles = response[1][1:]
   response = readUntil(lines, "Description")
   lines = lines[response[0]:]
   backstory = {}
   for line in response[1][1:]:
      linelist = line.split()
      response = readUntil(linelist, "BeginText")
      backstory[" ".join(response[1])] = " ".join(linelist[response[0]+1:])
   response = readUntil(lines, "E0F")
   lines = lines[response[0]:]
   description = {}
   for line in response[1][1:]:
      linelist = line.split()
      response = readUntil(linelist, "BeginText")
      description[" ".join(response[1])] = " ".join(linelist[response[0]+1:])
   return PbtACharacter(fname, players, name, pronouns, parent, pantheon, art, armor, harm, attack, thread, playbook, stats, godlikes, items, moves, conditions, tangleTable, tangles, backstory, description)

def loadItems(list):
   items = {}
   for line in list:
      linelist = line.split()
      response = readUntil(linelist, "Description:")
      desc = " ".join(linelist[response[0]+1:])
      name = correctMyString(" ".join(response[1]))
      items[name] = desc
   return items
  
def loadBasicMoves(fname):
   file = open(fname+ ".txt")
   lines = file.read().splitlines()
   file.close()
   return loadMoves(lines)   
   
def loadMoves(list):
   moves = {}
   while(len(list) > 1):
      response = readUntil(list, "EndMove")
      list = list[response[0]+1:]
      move = loadMove(response[1])
      moves[move.name] = move
   return moves   

# name, description, count, sides, modifier, outcomes, choices
def loadMove(list):
   name = correctMyString(list[0])
   desc = list[1]
   roll = list[2].split()
   count = int(roll[1])
   sides = int(roll[2])
   modifier = roll[3]
   list = list[3:]
   response = readUntil(list, "EndOutcomes")
   outcomes = {}
   for line in response[1]:
      outcomes[line[:3]] = line[4:]
   list = list[response[0]+1:]
   choiceNamesList = list[0].split()
   list = list[1:]
   choicesNames = []
   choices = {}
   for i in range(2, len(choiceNamesList)+1):
      if(i < len(choiceNamesList)):
         response = readUntil(list, choiceNamesList[i])
      else:
         response = readUntil(list, "EndMove")
      list = list[response[0]:]
      choices[choiceNamesList[i-1]] = response[1][1:]
   return PbtAMove(name, desc, count, sides, modifier, outcomes, choices)     
   
def correctMyString(myString):
   line = myString.split()
   response = []
   for word in line:
      response.append(word.capitalize())
   return " ".join(response)

def rollDice(count, sides, type, taken):
   rolls = []
   takenrolls = []
   for i in range(0, count):
      roll = random.randint(1, sides)
      rolls.append(roll)
      takenrolls.append(roll)
   takenrolls.sort()
   if(type == "h"):
      lowind = len(takenrolls) - taken
      takenrolls = takenrolls[lowind:]
      return (rolls, takenrolls)
   elif(type == "l"):
      takenrolls = takenrolls[:taken]
      return (rolls, takenrolls)
   else:
      return (rolls, takenrolls)
   

def addServerData(guildname, fname):
   game = loadGame(fname)
   serversDict[guildname] = game

bot = commands.Bot(command_prefix='~')

@bot.event
async def on_ready():
   await bot.change_presence(status=discord.Status.online, activity=discord.Game("Use ~help for commands"))

@bot.command(name='loadGame', help="Format: ~loadGame [Filename]; Loads and stores game")
async def loadPbtAGame(ctx, *args):
   if(len(args) < 1):
      await ctx.send("Please specify name of the file containing the game")
   elif(len(args) > 1):
      await ctx.send("Too many parameters given. Filename is a single word")
   else:
      addServerData(ctx.guild, args[0])
      await ctx.send("Game has been loaded!")

@bot.command(name='harm', help="Format: ~harm [Character (str)] [Amount (optional)]")
async def harmPbtAChar(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) != 2):
         await ctx.send("The expected number of arguments is 2. Please use the format: ~harm [Character (str)] [Amount (optional)]")
      else:
         if(args[1].isnumeric):
            harmed = int(args[1])
            charName = args[0]
            if((charName not in game.pcs) and (charName not in game.npcs)):
               await ctx.send("Player could not be found, please try again")
               return
            
            actor = 0
            if(charName in game.pcs):
               actor = game.pcs[charName]
            else:
               actor = game.npcs[charName]  
            
            if((ctx.author.mention not in game.dms) and (ctx.author.mention not in actor.players)):
               await ctx.send("You do not have control of this character.")
            else:
               actor.harm += harmed
               actor.updateSheet()
               await ctx.send("Character has been successfully harmed, and is current at " + str(actor.harm) + " Harm.")
               
         else:
            await ctx.send("Please use a number to indicate the amount to be healed")

@bot.command(name='heal', help="Format: ~heal [Character (str)] [Amount (optional)]")
async def healPbtAChar(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) != 2):
         await ctx.send("The expected number of arguments is 2. Please use the format: ~heal [Character (str)] [Amount (optional)]")
      else:
         if(args[1].isnumeric):
            healed = int(args[1])
            charName = args[0]
            if((charName not in game.pcs) and (charName not in game.npcs)):
               await ctx.send("Player could not be found, please try again")
               return
            
            actor = 0
            if(charName in game.pcs):
               actor = game.pcs[charName]
            else:
               actor = game.npcs[charName]  
            
            if((ctx.author.mention not in game.dms) and (ctx.author.mention not in actor.players)):
               await ctx.send("You do not have control of this character.")
            else:
               actor.harm -= healed
               if(actor.harm < 0):
                  actor.harm = 0
               actor.updateSheet()
               await ctx.send("Character has been successfully healed and is current at " + actor.harm + " Harm.")
               
         else:
            await ctx.send("Please use a number to indicate the amount to be healed")

@bot.command(name='gainThread', help="Format: ~gainThread [Character (str)] [Amount (optional)]")
async def gainPbtAThread(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) != 2):
         await ctx.send("The expected number of arguments is 2. Please use the format: ~gainThread [Character (str)] [Amount (optional)]")
      else:
         if(args[1].isnumeric):
            gained = int(args[1])
            charName = correctMyString(args[0])
            if((charName not in game.pcs) and (charName not in game.npcs)):
               await ctx.send("Player could not be found, please try again")
               return
            
            actor = 0
            if(charName in game.pcs):
               actor = game.pcs[charName]
            else:
               if(ctx.author.mention not in game.dms):
                  await ctx.send("You cannot give NPCs threads")
                  return
               else:
                  actor = game.npcs[charName]  
            
            if((ctx.author.mention not in game.dms) and (ctx.author.mention not in actor.players)):
               await ctx.send("You do not have control of this character.")
            else:
               actor.thread += gained
               actor.updateSheet()
               await ctx.send("Threads have been successfully added")
               
         else:
            await ctx.send("Please use a number to indicate the number of threads gained")

@bot.command(name='spendThread', help="Format: ~spendThread [Character (str)] [Amount (optional)]")
async def spendPbtAThread(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) < 2):
         await ctx.send("You may spend 1 thread to:\n\t- Reduce 2 Harm. This can combine with your Epic Armor and Shield\n\t- Add a significant detail to the scene\n\t- Give yourself Fate's Favor on a roll you just made\n\nOr you may spend 5 threads to take an advance")
      elif(len(args) > 2):
         await ctx.send("The maximum number of arguments is 2. Please use the format: ~spendThread [Character (str)] [Amount (optional)]")
      else:
         if(args[1].isnumeric):
            spent = int(args[1])
            charName = args[0]
            if((charName not in game.pcs) and (charName not in game.npcs)):
               await ctx.send("Player could not be found, please try again")
               return
            
            actor = 0
            if(charName in game.pcs):
               actor = game.pcs[charName]
            else:
               if(ctx.author.mention not in game.dms):
                  await ctx.send("You cannot spend NPC threads")
                  return
               else:
                  actor = game.npcs[charName]  
            
            if((ctx.author.mention not in game.dms) and (ctx.author.mention not in actor.players)):
               await ctx.send("You do not have control of this character.")
            else:
               if(actor.thread >= spent):
                  actor.thread -= spent
                  actor.updateSheet()
                  await ctx.send("Threads have been successfully spent")
               else:
                  await ctx.send("You do not have enough threads!")
               
         else:
            await ctx.send("Please use a number to indicate the number of threads spent")

@bot.command(name='exchangeHarm', help="Format: ~exchangeHarm [player character name (str)] [character 2 name (str)] [protect or crush (optional)] [protect or crush (optional)]")
async def PbtAExchangeHarm(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) < 2):
         await ctx.send("The minimum number of arguments is 2. Please use the format ~exchangeHarm [player character name (str)] [character 2 name (str)] [protect or crush (optional)] [protect or crush (optional)]")
      elif(len(args) > 4):
         await ctx.send("The maximum number of arguments is 4. Please use the format ~exchangeHarm [player character name (str)] [character 2 name (str)] [protect or crush (optional)] [protect or crush (optional)]")
      else:
         char1Name = correctMyString(str(args[0]))
         char2Name = correctMyString(str(args[1]))
         Protect = 0
         Crush = 0
         for myArg in args[2:]:
            if(correctMyString(myArg) == "Crush"):
               Crush = 1
            if(correctMyString(myArg) == "Protect"):
               Protect = 1
               
         if((char1Name not in game.pcs) and (char1Name not in game.npcs)):
            await ctx.send("Player could not be found, please try again")
            return
         
         if((char2Name not in game.pcs) and (char2Name not in game.npcs)):
            await ctx.send("Player could not be found, please try again")
            return 
         
         playerActor = 0
         if(char1Name in game.pcs):
            playerActor = game.pcs[char1Name]
         else:
            if(ctx.author.mention not in game.dms):
               await ctx.send("The first character must be a player character.")
               return
            else:
               playerActor = game.npcs[char1Name]
         
         otherActor = 0
         if(char2Name in game.pcs):
            otherActor = game.pcs[char2Name]
         else:
            otherActor = game.npcs[char2Name]
         
         if((ctx.author.mention not in game.dms) and (ctx.author.mention not in playerActor.players)):
            await ctx.send("You do not have control of this character")
            return
            
         outgoingHarm = playerActor.attack + Crush - otherActor.armor
         incomingHarm = otherActor.attack - Protect - playerActor.armor
         
         playerActor.harm += incomingHarm
         otherActor.harm += outgoingHarm
         
         playerActor.updateSheet()
         otherActor.updateSheet()
         
         await ctx.send(playerActor.fname + " has dealt " + str(outgoingHarm) + " to " + otherActor.fname)
         await ctx.send(otherActor.fname + " has dealt " + str(incomingHarm) + " to " + playerActor.fname)
         
            
@bot.command(name='get', help="Format: ~get [character name (str)] [Piece of information (str)]")
async def getPbtACharInfo(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) != 2):
         await ctx.send("The expected number of arguments is 2. Please use the format ~get [character name (str)] [Piece of information (str)]")
      else:
         charName = correctMyString(str(args[0]))
         infoPiece = correctMyString(str(args[1]))
         infoPieceList = ["Players", "Name", "Pronouns", "Parent", "Pantheon", "Art", "Armor", "Harm", "Attack", "Threads", "Playbook", "Stats", "Godlikes", "Items", "Moves", "Conditions", "Tangles", "Backstory", "Description"]   
         
         if((charName not in game.pcs) and (charName not in game.npcs)):
            await ctx.send("Player could not be found, please try again")
            return
            
         actor = 0
         if(charName in game.pcs):
            actor = game.pcs[charName]
         else:
            actor = game.npcs[charName]
         
         if(infoPiece not in infoPieceList):
            await ctx.send("Unknown piece of information. The information available is: \n\t" + "\n\t".join(infoPieceList))
            return
         
         response = actor.getInfo(infoPiece)
         if(charName in game.pcs):
             if((infoPiece == "Backstory") or (infoPiece == "Tangles")):
               if(ctx.author.mention in actor.players):
                  for part in response:
                     await ctx.author.send(part)
               elif(ctx.author.mention in game.dms):
                  for part in response:
                     await ctx.author.send(part)
               else:
                  await ctx.author.send("You don't have permission to view this information")
             else:
               for part in response:
                  await ctx.send(part)
         else:
            if((infoPiece == "Pronouns") or (infoPiece == "Art") or (infoPiece == "Description") or (infoPiece == "Name")):
               for part in response:
                  await ctx.send(part)
            else:
               if(ctx.author.mention in game.dms):
                  for part in response:
                     await ctx.author.send(part)
               else:
                  await ctx.send("You do not have permission to view this information")
         

@bot.command(name='makeMove', help="Format: ~makeMove [character name (str)] [\" Move Name\" (str) IN QUOTES] [type: favor, disfavor, normal (str)] [bonus (int)] [replacement (str) or (int)]")
async def makePbtAMove(ctx, *args):
   contextServerName = ctx.guild
   if contextServerName not in serversDict:
      await ctx.send("Game could not be found. Please use ~loadGame first.")
   else:
      game = serversDict[contextServerName]
      if(len(args) < 4):
         await ctx.send("The minimum number of arguments is 4. Please use the format: ~makeMove [character name (str)] [\" Move Name\" (str) IN QUOTES] [type: favor, disfavor, normal (str)] [bonus (int)] [replacement (str) or (int)]")
      elif(len(args) > 5):
         await ctx.send("The maximum number of arguments is 5. Please use the format: ~makeMove [character name (str)] [\" Move Name\" (str) IN QUOTES] [type: favor, disfavor, normal (str)] [bonus (int)] [replacement (str) or (int)]")
      else:
         charName = correctMyString(str(args[0]))
         moveName = correctMyString(str(args[1]))
         tempType = correctMyString(str(args[2]))
         bonus = int(args[3])
         replacement = "none"
         if(len(args) == 5):
            if(args[4].isnumeric()):
               replacement = args[4]
            else:
               replacement = correctMyString(str(args[4]))
         
         if((charName not in game.pcs) and (charName not in game.npcs)):
            await ctx.send("Player could not be found, please try again")
            return
         actor = 0
         if(charName in game.pcs):
            actor = game.pcs[charName]
         else:
            actor = game.npcs[charName]
         
         if((moveName not in game.basicMoves) and (moveName not in actor.moves)):
            await ctx.send("Move could not be found, please try again")
            return
            
         type = 0
         if(tempType in ["Favor", "F", "Advantage", "A"]):
            type = "Favor"
         elif(tempType in ["Disfavor", "D", "Disadvantage"]):
            type = "Disfavor"
         else:
            type = "Normal"
         
         response = game.makeMove(charName, moveName, type, bonus, replacement)
         
         if(ctx.author.mention in actor.players):
            await ctx.send(response)
         elif(ctx.author.mention in game.dms):
            await ctx.send(response)
         else:
            await ctx.send("You do not have access to this character.")
         
   
@bot.command(name='simpleRoll', help="Rolls N Dice with side count M.")
async def simpleRoll(ctx, *args):
   if(len(args) != 3):
      response = "The proper format is -roll N d M, for N dice with side count M"
   else:  
      n = (int)((args[0]).strip())
      m = (int)((args[2]).strip())
      rolls = []
      sum = 0
      response = ""
      for i in range(0, n):
         x = random.randint(1, m)
         sum = sum + x
         rolls.append(x)
      rolls.sort()
      for j in range(0, n):
         response = response + "  " + str(rolls[j])
      response = response + "\nSum = " + str(sum)
   await ctx.send(response)
   
@bot.command(name='roll', help="Any combination of NdMH/LO + P")
async def AdvancedRoll(ctx, *args):
   input = "".join(args)
   input = input.strip()

@bot.command(name='test', help="test, pls dont abuse uwu")
async def test(ctx, *args):
   game = serversDict[ctx.guild]
   print(ctx.author.mention)
   #compare = ["<@140223051240439809>"]
   response = ctx.author.mention
   print(ctx.author.mention in game.players)
   await ctx.send("Hai cutie, " + ctx.author.mention)
   message_channel = bot.get_channel("506949534237327363")
   print(f"Got channel {message_channel}")
   print(message.channel.name)
   await message_channel.send("Your message")
      
@tasks.loop(hours=24)
async def test2():
   message_channel = bot.get_channel(750712940235063330)
   #print(f"Got channel {message_channel}")
   x=datetime.today()
   day = int(x.strftime("%d"))
   month = int(x.strftime("%m"))
   if(len(Birthdays[month-1][day-1]) > 0):
      response = "Happppppy Birthdayyyyyyyyyyyyyyyy "
      for name in Birthdays[month-1][day-1]:
         response += name + " "
      response += "!!!!!!!"
      await message_channel.send(response)
    
@test2.before_loop
async def before():
   await bot.wait_until_ready()
   #print("Finished waiting")

Birthdays = [[[] for c in range(31)] for r in range(12)]

@bot.command(name='addMyBirthday', help="Format: ~addMyBirthday MM DD, where MM is month and DD is day")
async def addMyBirthday(ctx, *args):
   if(len(args) != 2):
      response = "The proper format is ~addMyBirthday MM DD, and thus needs 2 parameters"
   else:
      month = int(args[0])
      day = int(args[1])
      if((month < 1) or (month > 12) or (day < 1) or (day > 31)):
         response = "The inputted day is invalid"
      elif(ctx.author.mention in Birthdays[month-1][day-1]):
         response = "I already have that one marked!"
      else:
         Birthdays[month-1][day-1].append(ctx.author.mention)
         response = "Added! Thanks, " + ctx.author.mention
      updateBirthdays()
      await ctx.send(response)
      
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"] 

@bot.command(name='getBirthdays', help="Format: ~getBirthdays")
async def getBirthdays(ctx, *args):
   response = ""
   for month in range(0, len(Birthdays)):
      printMe = False
      tempResponse = "\n------------------------------------\n**" + months[month] + "**\n"
      for day in range(0, len(Birthdays[month])):
         if(len(Birthdays[month][day]) > 0):
            printMe = True
            for name in Birthdays[month][day]:
               tempResponse += "\t" + str(day+1) + " - " + name + "\n"
      if(printMe):
         response += tempResponse # + "------------------------------------\n"
   await ctx.send(response)
      
def loadBirthdays():
   file = open("Birthdays.txt")
   lines = file.read().splitlines()
   file.close()
   for temp in lines:
      line = temp.split()
      Birthdays[int(line[1])-1][int(line[2])-1].append(line[0])


def updateBirthdays():
   file = open("Birthdays.txt", "w")
   for month in range(0, len(Birthdays)):
      for day in range(0, len(Birthdays[month])):
         for name in Birthdays[month][day]:
            line = name + " " + str(month+1) + "  " + str(day+1) + "\n"
            file.write(line)
   file.close()
    

def getRandItems(itemList, count):
   items = []
   for i in range(0, count):
      index = random.randint(0, len(itemList)-1)
      items.append(itemList[index])
   return items

randomizerDict = {}

def unpackList(filename):
   file = open(filename+".txt", "r")
   temp = file.read().split("\n")
   file.close()
   return temp

def updateList(filename):
   file = open(filename+".txt", "w")
   file.write(correctMyString(randomizerDict[filename][0]))
   for it in randomizerDict[filename][1:]:
      line = "\n" + correctMyString(it)
      file.write(line)
   file.close()

def loadRandomizers():   
   randomizerDict["nouns"] = unpackList("nouns")
   randomizerDict["adjectives"] = unpackList("adjectives")
   randomizerDict["items"] = unpackList("items")
   randomizerDict["monsters"] = unpackList("monsters")
   randomizerDict["trinkets"] = unpackList("trinkets")
   randomizerDict["classes"] = unpackList("classes")
   randomizerDict["spells"] = unpackList("spells")
   randomizerDict["spellGoals"] = unpackList("spellGoals")
   randomizerDict["npcnames"] = unpackList("npcnames")
   randomizerDict["npcpronouns"] = unpackList("npcpronouns")
   randomizerDict["races"] = unpackList("races")
   randomizerDict["personalities"] = unpackList("personalities")
   randomizerDict["backgrounds"] = unpackList("backgrounds")
   randomizerDict["goals"] = unpackList("goals")
   randomizerDict["rumorSubjects"] = unpackList("rumorSubjects")
   randomizerDict["rumorActions"] = unpackList("rumorActions")
   randomizerDict["complications"] = unpackList("complications")
   randomizerDict["alph"] = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
   randomizerDict["cons"] = ["b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "z"]
   randomizerDict["vow"] = ["a", "e", "i", "o", "u", "y"]

@bot.command(name='addNouns', help="Format: ~addNouns <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addNouns(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addNouns <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["nouns"]):
            repeat = True
         else:
            randomizerDict["nouns"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("nouns")
      await ctx.send(response)
      
@bot.command(name='addAdjectives', help="Format: ~addAdjectives <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addAdjectives(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addAdjectives <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["adjectives"]):
            repeat = True
         else:
            randomizerDict["adjectives"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("adjectives")
      await ctx.send(response)      

@bot.command(name='addMonsters', help="Format: ~addMonsters <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addMonsters(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addMonsters <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["monsters"]):
            repeat = True
         else:
            randomizerDict["monsters"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("monsters")
      await ctx.send(response)
      
@bot.command(name='addItems', help="Format: ~addItems <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addItems(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addItems <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["trinkets"]):
            repeat = True
         else:
            randomizerDict["items"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("items")
      await ctx.send(response)

@bot.command(name='addTrinkets', help="Format: ~addTrinkets <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addTrinkets(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addTrinkets <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["trinkets"]):
            repeat = True
         else:
            randomizerDict["trinkets"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("trinkets")
      await ctx.send(response)
      
@bot.command(name='addSpellGoal', help="Format: ~addSpellGoal <Description>, where Description is a string representation of a general/vague concept of what a spell accomplishes")
async def addSpellGoal(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addSpellGoal <Description>, where Description is a string representation of a general/vague concept of what a spell accomplishes"
   else:
      randomizerDict["spellGoals"].append(" ".join(args))
      response = "Added! Thanks, " + ctx.author.mention
      updateList("spellGoals")
      await ctx.send(response)
      
@bot.command(name='addPronouns', help="Format: ~addPronouns <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addPronouns(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addPronouns <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["npcpronouns"]):
            repeat = True
         else:
            randomizerDict["npcpronouns"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("npcpronouns")
      await ctx.send(response)

@bot.command(name='addRaces', help="Format: ~addRaces <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addRaces(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addRaces <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["races"]):
            repeat = True
         else:
            randomizerDict["races"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("races")
      await ctx.send(response)

@bot.command(name='addPersonalities', help="Format: ~addPersonalities <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addPersonalities(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addPersonalities <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["personalities"]):
            repeat = True
         else:
            randomizerDict["personalities"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("personalities")
      await ctx.send(response)

@bot.command(name='addBackgrounds', help="Format: ~addBackgrounds <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addBackgrounds(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addBackgrounds <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["backgrounds"]):
            repeat = True
         else:
            randomizerDict["backgrounds"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("backgrounds")
      await ctx.send(response)

@bot.command(name='addGoal', help="Format: ~addGoal <Description>, where Description is a string representation of a general/vague concept of what a person wants or is working towards")
async def addGoal(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addGoal <Description>, where Description is a string representation of a general/vague concept of what a person wants or is working towards"
   else:
      randomizerDict["goals"].append(" ".join(args))
      response = "Added! Thanks, " + ctx.author.mention
      updateList("goals")
      await ctx.send(response)
            
@bot.command(name='addRumorSubjects', help="Format: ~addRumorSubjects <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" ")
async def addRumorSubjects(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addRumorSubjects <Thing1> <Thing2> ... <ThingN>, where ThingN is a ONE WORD string representation of the name of the nth thing being added. Any input requiring more than one word must be wrapped in quotes such as \"The Thing\" "
   else:
      repeat = False
      for arg in args:
         if(correctMyString(arg) in randomizerDict["rumorSubjects"]):
            repeat = True
         else:
            randomizerDict["rumorSubjects"].append(correctMyString(arg))
      if(repeat):
         response = "One or more items were already on the list. Everything else has been added, thanks! " + ctx.author.mention
      else:      
         response = "Added! Thanks, " + ctx.author.mention
      updateList("rumorSubjects")
      await ctx.send(response)

@bot.command(name='addRumorDescription', help="Format: ~addRumorDescription <Description>, where Description is a string representation of a general/vague concept of what a person/organization did/is doing but does NOT name that person/organization")
async def addRumorDescription(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addRumorDescription <Description>, where Description is a string representation of a general/vague concept of what a person/organization did/is doing but does NOT name that person/organization"
   else:
      randomizerDict["rumorActions"].append(" ".join(args))
      response = "Added! Thanks, " + ctx.author.mention
      updateList("rumorActions")
      await ctx.send(response)

@bot.command(name='addComplication', help="Format: ~addComplication <Description>, where Description is a string representation of a general/vague concept of  why something is difficult / needs to be overcome")
async def addComplication(ctx, *args):
   if(len(args) == 0):
      response = "The proper format is ~addComplication <Description>, where Description is a string representation of a general/vague concept of why something is difficult / needs to be overcome"
   else:
      randomizerDict["complications"].append(" ".join(args))
      response = "Added! Thanks, " + ctx.author.mention
      updateList("complications")
      await ctx.send(response)

@bot.command(name='getMonster', help="Format: ~getMonster M N A, where M is number of random monsters sampled, and N is number of random nouns sampled, and A is the number of adjectives sampled. The default values are 1 monster, 1 noun, 1 adjective")
async def getMonster(ctx, *args):
   if(len(args) > 3):
      response = "The proper format is ~getMonster M N A, where M is number of random monsters sampled, and N is number of random nouns sampled, and A is the number of adjectives sampled"
   else:
      allnumbers = True
      for arg in args:
         if not arg.isnumeric:
            allnumbers = False
      if not allnumbers:
         response = "Please input numbers only"
      else:
         numMon = 1
         numNoun = 1
         numAdj = 1
         if(len(args) > 0):
            numMon = int(args[0])
         if(len(args) > 1):
            numNoun = int(args[1])
         if(len(args) > 2):
            numAdj = int(args[2])
            
         monList = getRandItems(randomizerDict["monsters"], numMon)
         nounList = getRandItems(randomizerDict["nouns"], numNoun)
         adjList = getRandItems(randomizerDict["adjectives"], numAdj)
         
         response = "Your Monster Idea:\n\n"
         if(len(monList) > 0):
            response = response + "__*Base Monsters*__ :\n"
            for mon in monList:
               response = response + "\t- " + mon +"\n"
         if(len(nounList) > 0):
            response = response + "\n__*Ideas to Incorporate*__ :\n"
            for noun in nounList:
               response = response + "\t- " + noun +"\n"
         if(len(adjList) > 0):
            response = response + "\n__*Descriptors*__ :\n"
            for adj in adjList:
               response = response + "\t- " + adj +"\n"
      
   await ctx.send(response)

@bot.command(name='getMagicItem', help="Format: ~getMagicItem I N A, where I is number of random items sampled, and N is number of random nouns sampled, and A is the number of adjectives sampled. The default values are 1 item, 1 noun, 1 adjective")
async def getMagicItem(ctx, *args):
   if(len(args) > 3):
      response = "The proper format is ~getMagicItem I N A, where I is number of random items sampled, and N is number of random nouns sampled, and A is the number of adjectives sampled"
   else:
      allnumbers = True
      for arg in args:
         if not arg.isnumeric:
            allnumbers = False
      if not allnumbers:
         response = "Please input numbers only"
      else:
         numItem = 1
         numNoun = 1
         numAdj = 1
         if(len(args) > 0):
            numItem = int(args[0])
         if(len(args) > 1):
            numNoun = int(args[1])
         if(len(args) > 2):
            numAdj = int(args[2])
            
         itList = getRandItems(randomizerDict["items"], numItem)
         nounList = getRandItems(randomizerDict["nouns"], numNoun)
         adjList = getRandItems(randomizerDict["adjectives"], numAdj)
         
         response = "Your Item Idea:\n\n"
         if(len(itList) > 0):
            response = response + "__*Base Items*__ :\n"
            for it in itList:
               response = response + "\t- " + it +"\n"
         if(len(nounList) > 0):
            response = response + "\n__*Ideas to Incorporate*__ :\n"
            for noun in nounList:
               response = response + "\t- " + noun +"\n"
         if(len(adjList) > 0):
            response = response + "\n__*Descriptors*__ :\n"
            for adj in adjList:
               response = response + "\t- " + adj +"\n"
      
   await ctx.send(response)

@bot.command(name='getSubclass', help="Format: ~getSubclass N A, where N is number of random nouns sampled, and A is the number of adjectives sampled. The default values are 1 noun, 1 adjective")
async def getSubclass(ctx, *args):
   if(len(args) > 2):
      response = "The proper format is ~getSubclass N A, where N is number of random nouns sampled, and A is the number of adjectives sampled"
   else:
      allnumbers = True
      for arg in args:
         if not arg.isnumeric:
            allnumbers = False
      if not allnumbers:
         response = "Please input numbers only"
      else:
         numClass = 1
         numNoun = 1
         numAdj = 1
         if(len(args) > 1):
            numNoun = int(args[1])
         if(len(args) > 2):
            numAdj = int(args[2])
            
         classList = getRandItems(randomizerDict["classes"], numClass)
         nounList = getRandItems(randomizerDict["nouns"], numNoun)
         adjList = getRandItems(randomizerDict["adjectives"], numAdj)
         
         response = "Your Subclass Idea:\n\n"
         if(len(classList) > 0):
            response = response + "__*Base Class*__ :\n"
            for cla in classList:
               response = response + "\t- " + cla +"\n"
         if(len(nounList) > 0):
            response = response + "\n__*Ideas to Incorporate*__ :\n"
            for noun in nounList:
               response = response + "\t- " + noun +"\n"
         if(len(adjList) > 0):
            response = response + "\n__*Descriptors*__ :\n"
            for adj in adjList:
               response = response + "\t- " + adj +"\n"
      
   await ctx.send(response)

@bot.command(name='getSpell', help="Format: ~getSpell N A, where N is number of random nouns sampled, and A is the number of adjectives sampled. The default values are 1 noun, 1 adjective")
async def getSpell(ctx, *args):
   if(len(args) > 2):
      response = "The proper format is ~getSpell N A, where N is number of random nouns sampled, and A is the number of adjectives sampled"
   else:
      allnumbers = True
      for arg in args:
         if not arg.isnumeric:
            allnumbers = False
      if not allnumbers:
         response = "Please input numbers only"
      else:
         numSchool = 1
         numGoal = 1
         numNoun = 1
         numAdj = 1
         if(len(args) > 1):
            numNoun = int(args[1])
         if(len(args) > 2):
            numAdj = int(args[2])
            
         schoolList = getRandItems(randomizerDict["spells"], numSchool)
         goalList = getRandItems(randomizerDict["spellGoals"], numGoal)
         nounList = getRandItems(randomizerDict["nouns"], numNoun)
         adjList = getRandItems(randomizerDict["adjectives"], numAdj)
         
         response = "Your Spell Idea:\n\n"
         if(len(schoolList) > 0):
            response = response + "__*Spell School*__ :\n"
            for sch in schoolList:
               response = response + "\t- " + sch +"\n"
         if(len(goalList) > 0):
            response = response + "\n__*Spell Goal*__ :\n"
            for goal in goalList:
               response = response + "\t- " + goal +"\n"
         if(len(nounList) > 0):
            response = response + "\n__*Ideas to Incorporate*__ :\n"
            for noun in nounList:
               response = response + "\t- " + noun +"\n"
         if(len(adjList) > 0):
            response = response + "\n__*Descriptors*__ :\n"
            for adj in adjList:
               response = response + "\t- " + adj +"\n"
      
   await ctx.send(response)

@bot.command(name='getTrinket', help="Format: ~getTrinket N A, where N is number of random nouns sampled, and A is the number of adjectives sampled. The default values are 1 noun, 1 adjective")
async def getTrinket(ctx, *args):
   if(len(args) > 2):
      response = "The proper format is ~getSubclass N A, where N is number of random nouns sampled, and A is the number of adjectives sampled"
   else:
      allnumbers = True
      for arg in args:
         if not arg.isnumeric:
            allnumbers = False
      if not allnumbers:
         response = "Please input numbers only"
      else:
         numTrink = 1
         numNoun = 1
         numAdj = 1
         if(len(args) > 1):
            numNoun = int(args[1])
         if(len(args) > 2):
            numAdj = int(args[2])
            
         trinkList = getRandItems(randomizerDict["trinket"], numTrink)
         nounList = getRandItems(randomizerDict["nouns"], numNoun)
         adjList = getRandItems(randomizerDict["adjectives"], numAdj)
         
         response = "Your Trinket Idea:\n\n"
         if(len(trinkList) > 0):
            response = response + "__*Base Class*__ :\n"
            for trink in trinkList:
               response = response + "\t- " + trink +"\n"
         if(len(nounList) > 0):
            response = response + "\n__*Ideas to Incorporate*__ :\n"
            for noun in nounList:
               response = response + "\t- " + noun +"\n"
         if(len(adjList) > 0):
            response = response + "\n__*Descriptors*__ :\n"
            for adj in adjList:
               response = response + "\t- " + adj +"\n"
      
   await ctx.send(response)

@bot.command(name='getNPC', help="Format: ~getNPC R, where R is optional and putting anything in R makes the name generator generate a completely random name from consonants and then inserting vowels")
async def getNPC(ctx, *args):
   if(len(args) > 1):
      response = "The proper format is ~getNPC R, where R is optional and putting anything in R makes the name generator generate a completely random name from consonants and then inserting vowels"
   else:
      if False:
         response = "Please input numbers only"
      else:
         if(len(args) > 0):
            numCons = random.randint(3,10)
            numVow = random.randint(3, 7)
            numCons2 = random.randint(3,10)  
            numVow2 = random.randint(3, 7)
            
            firstNameL = getRandItems(randomizerDict["cons"], numCons)
            firstVow = getRandItems(randomizerDict["vow"], numVow)
            lastNameL = getRandItems(randomizerDict["cons"], numCons2)
            lastVow = getRandItems(randomizerDict["vow"], numVow2)
            print(firstNameL)
            for v1 in firstVow:
               index = random.randint(0, len(firstNameL)-1)
               firstNameL.insert(index, v1)
            for v2 in lastVow:
               index = random.randint(0, len(lastNameL)-1)
               lastNameL.insert(index, v2)
            
            firstName = "".join(firstNameL)
            lastName = "".join(lastNameL)

         else:
            numName = random.randint(1,5)
            numName2 = random.randint(1,5)
            firstName = "".join(getRandItems(randomizerDict["npcnames"], numName))
            lastName = "".join(getRandItems(randomizerDict["npcnames"], numName2)) 
            
         adj = getRandItems(randomizerDict["adjectives"], 1)[0]
         race = getRandItems(randomizerDict["races"], 1)[0]
         background = getRandItems(randomizerDict["backgrounds"], 1)[0]
         pronouns = getRandItems(randomizerDict["npcpronouns"], 1)[0]
         goal = getRandItems(randomizerDict["goals"], 1)[0]
         personality = getRandItems(randomizerDict["personalities"], 1)[0]
         
         response = "Your NPC:\n\n"
         response = response + firstName + " " + lastName + " is a " + adj + " " + race + "\n\n"
         response = response + "**Pronouns:** " + pronouns + "\n\n"
         response = response + "**Background:** " + background + "\n\n"
         response = response + "**Goal:** " + goal + "\n\n"
         response = response + "**Personality:** " + personality + "\n\n"
      
   await ctx.send(response)

@bot.command(name='getRumor', help="Format: ~getRumor")
async def getRumor(ctx, *args):
   if(len(args) > 0):
      response = "The proper format is ~getRumor"
   else:
      if False:
         response = "Please input numbers only"
      else:
         subject = getRandItems(randomizerDict["rumorSubjects"], 1)[0]
         action = getRandItems(randomizerDict["rumorActions"], 1)[0]
         
         response = "Hey pssssst. Did you hear?? " + subject + " " + action
      
   await ctx.send(response)
   
@bot.command(name='getEncounter', help="Format: ~getEncounter M, where M is number of monsters sampled")
async def getEncounter(ctx, *args):
   if(len(args) > 1):
      response = "The proper format is ~getEncounter M, where M is number of monsters sampled"
   else:
      allnumbers = True
      for arg in args:
         if not arg.isnumeric:
            allnumbers = False
      if not allnumbers:
         response = "Please input numbers only"
      else:
         numMon = 1
         if(len(args) > 0):
            numMon = int(args[0])
         
         monList = getRandItems(randomizerDict["rumorSubjects"], numMon)
         noun = getRandItems(randomizerDict["nouns"], 1)[0]
         complication = getRandItems(randomizerDict["complications"], 1)[0]

         response = "Your Encounter:\n\n"
         response = "It's a " + noun + " BUT... " + complication + "\n"
         if(len(monList) > 0):
            response = response + "And the following monsters are present:\n"
            for mon in monList:
               response = response + "\t- " + mon +"\n"
      
   await ctx.send(response)

loadRandomizers()
loadBirthdays()
test2.start()
bot.run(TOKEN)