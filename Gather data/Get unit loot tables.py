import string
import re
import os
import json
import collections
import itertools
from collections import defaultdict
from itertools import chain
import statistics

# When I started writing this, only God and I knew how this code works.
# Now, only God knows.
#               - anonymous

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

def getFile(name):
        for root,dirs,files in os.walk(exportFolder,topdown=True): # could be optimized with specific dirs through itertools but whatever
                for file in files:
                        if (file == name):
                                return os.path.join(root,file)
        return

itemData={}
with open(exportFolder+"\Blueprints\Data\ItemDetailsData.json", encoding='utf-8') as f:
        itemData = json.load(f)
with open(exportFolder+"\Blueprints\Data\DanglyDetailsData.json", encoding='utf-8') as f: # merging all data tables
        itemData += json.load(f)
with open(exportFolder+"\Blueprints\Data\QuestItemDetailsData.json", encoding='utf-8') as f: 
        itemData += json.load(f)
                        
def getItem(key):
        for table in itemData:
                rows = table.get("Rows")
                for row in rows:
                        if row == key:
                                if rows[row].get("ItemName"):
                                        return rows[row].get("ItemName").get("LocalizedString")
                                if rows[row].get("DanglyName"):
                                        return rows[row].get("DanglyName").get("LocalizedString")
        return

itemToContainerList=defaultdict(list)
itemToContainerToChanceDict=defaultdict(dict) # Redundant but it's a late addition, TODO rework
with open(exportFolder+"\Blueprints\Data\RandomContainerLootData.json", encoding='utf-8') as f: # get random loot
        data = json.load(f)
        for table in data:
                rows = table.get("Rows")
                for itemSet in rows:
                        for details in rows[itemSet].get("ItemDetails"):
                                item = details.get("Item").get("RowName")
                                chance = details.get("Chance")
                                if chance:
                                        itemToContainerList[item].append(itemSet)
                                        itemToContainerToChanceDict[item].update({itemSet:chance})
                                elif chance is None: # 0 is not logged
                                        print("no chance for item "+item+" in "+itemSet)

lootClasses = dict()
containerClasses = set()
lootArrayToContainers = defaultdict(set)
lootToWhatever = defaultdict(set)
for root,dirs,files in os.walk(exportFolder+"\FW\LootObjects",topdown=True):  # get container classes because its impossible to tell which map prop is a container
        for file in files:
                if '\\FromCorpses' in root: 
                        with open(os.path.join(root,file)) as f:
                                text = f.read()
                                lookup = re.findall(r'"RowName": "(.*)"',text)
                                if len(lookup)>0:
                                        for container in lookup:
                                                lootArrayToContainers[file.replace(".json","_C")].add(container)
                                        
questNames={}
for root,dirs,files in os.walk(exportFolder+"\FW\Quests\Active",topdown=True):
    for file in files:
        if "DAQuest" in file:
            with open(os.path.join(root,file)) as f:
                text = f.read()
                tag = re.findall(r'QuestTag": {[\s]*?"TagName": "(.*)"',text)
                if tag:
                    questName = re.findall(r'SourceString": "(.*)"',text)
                    if questName:
                        questNames.update({tag[0]:questName[0]})
                else:
                    print("NO TAGS FOR QUEST "+file)
                                     
containerToUnitsList = defaultdict(list) # we need maps AND condition for it
containerLocalization = defaultdict(list) # list because in case of units one container drops from several guys           
with open("units.json") as f: # get container to unit and unit to maps mappings
        data = json.load(f)
        for k, v in data.items():
                lootArrays = v.get("Loot").split(', ') 
                maps = v.get("Locations")
                wikiName = v.get("WikiName")
                if lootArrays:
                        for lootArray in lootArrays:
                                if lootArray in lootArrayToContainers:
                                        for container in lootArrayToContainers[lootArray]:
                                                if wikiName:
                                                        containerLocalization[container].append(wikiName)
                                                containerToUnitsList[container].append(v)
                else:
                        print("loot container list not found for "+k)

# at this point we should somehow have data on every single item and container. Amen

itemLocalization = {}
with open("itemLocalization.json") as f: # wiki names for items
        itemLocalization = json.load(f)

finalOutput = defaultdict(list) # we need an output of rows like {Item:[{Container,Locations,Conditions}]} for every item
for table in itemData:
        rows = table.get("Rows").items()
        for item, v in rows:
                name = None
                if item in itemLocalization:
                        name = itemLocalization[item]
                elif v.get("ItemName"):
                        name = v.get("ItemName").get("LocalizedString")
                elif v.get("DanglyName"):
                        name = v.get("DanglyName").get("LocalizedString")
                if name:
                        if "Codex" in name:
                                name = "Codex"
                        if item in itemToContainerList:
                                contToLocations = defaultdict(set)
                                for container in itemToContainerList[item]:
                                        row = {"Item":name}
                                        chance = 9999
                                        if item in itemToContainerToChanceDict and name != "Codex":
                                                chance = itemToContainerToChanceDict[item].get(container)
                                        row.update({"Chance":chance})
                                        if container in containerToUnitsList:
                                                for unit in containerToUnitsList[container]:
                                                        wikiName = unit.get("WikiName")
                                                        if wikiName:
                                                                if chance > 200:
                                                                        print("chance > 200 "+item+" from "+wikiName)
                                                                if row not in finalOutput[wikiName]:
                                                                        finalOutput[wikiName].append(row)

# step 1: remove duplicates and find highest chance for each item and unit pair
finalOutput2 = defaultdict(list)
highest = {} # chance per unit per item
for unit, items in finalOutput.items():
        seen = set()
        new_l = []
        for itemRow in items:
            stuff = str(itemRow.items()) # item+chance
            improvHash = unit + itemRow.get("Item")
            chance = itemRow.get("Chance")
            if improvHash in highest:
                    if chance > highest[improvHash]:
                            highest.update({improvHash:chance})
            else:
                    highest.update({improvHash:chance})
            if stuff not in seen:
                seen.add(stuff)
                finalOutput2[unit].append(itemRow)

# step 2: remove items that don't have the highest chance 
finalOutput = defaultdict(list)
for unit, items in finalOutput2.items():
        for itemRow in items:
                improvHash = unit + itemRow.get("Item")
                if itemRow.get("Chance") == highest[improvHash]:
                        finalOutput[unit].append(itemRow)

# missed a few things, not gonna bother reworking all for these 
#finalOutput['Europan HK Suit Fragment'].append({"Container":"Europan EOD HunterKiller","Locations":surfaceMaps})
#finalOutput['Pilot'].append({"Container":"Europan Exo","ContainerType":"Unit","Locations":['Ashen Mesa','Elephant Mausoleum','Scorched Enclave','Downtown Lost Angels','Frozen Swamp','Mech Trenches','Babel','Stairway Gate','Tunnels'],"Condition":"Bring Her In"})
#finalOutput['Pilot'].append({"Container":"Europan Exo","ContainerType":"Unit","Locations":['Underground Cemetery'],"Condition":"Rust in Peace, Bring Her In"})
#finalOutput['Pilot'].append({"Container":"Europan Red Baron Exo","ContainerType":"Unit","Locations":['Elephant Mausoleum'],"Condition":"Red Baron\'s Legacy, Bring Her In"})

#for unit in finalOutput:
#        finalOutput[unit].sort()

with open("dropsByUnit.json", "w") as outfile:
        json.dump(finalOutput, outfile, indent=4)
