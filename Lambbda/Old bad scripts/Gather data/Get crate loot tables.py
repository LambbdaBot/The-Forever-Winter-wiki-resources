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
with open(exportFolder+"\Blueprints\Data\RandomContainerLootData.json", encoding='utf-8') as f: # get random loot
        data = json.load(f)
        for table in data:
                rows = table.get("Rows")
                for itemSet in rows:
                        for details in rows[itemSet].get("ItemDetails"):
                                item = details.get("Item").get("RowName")
                                itemToContainerList[item].append(itemSet)

# RareLootManager and other post-factum bullshit checklist
# Any container no condition
tunnelsLoot=set()       # tunnels exclusive     # any container
healthItems=set()       # only spawn in tunnels # any container
surfaceLoot=set()       # surface exclusive     # any container
anywhereLoot=set()      # spawn anywhere duh    # any container
droneItems=set()        # spawn anywhere        # any container
upgradeItems=set()      # spawn anywhere        # any container
transTaps=set()         # any map               # any container
# Conditional loot
octoTools=defaultdict(list) # UC only           # container list
levelSpecific=set()     # map specific          # storage
at43parts=set()         # map list              # any container 
alcoVault = set()       # map list              # alco vaults
with open(exportFolder+"\FW\LootObjects\Containers\BP_RareLootManager.json", encoding='utf-8') as f:
        data = json.load(f)
        for thing in data:
                if thing.get("Name") == "Default__BP_RareLootManager_C":
                        props = thing.get("Properties")
                        for item in props.get("Tunnel Options"): 
                                tunnelsLoot.add(item.get("ItemToDrop").get("RowName"))
                        for item in props.get("Region Options"): 
                                surfaceLoot.add(item.get("ItemToDrop").get("RowName"))
                        for item in props.get("Both Tunnel and Region Options"): 
                                anywhereLoot.add(item.get("ItemToDrop").get("RowName"))
                        for item in props.get("HRF05 Parts"): 
                                at43parts.add(item.get("ItemToDrop").get("RowName"))
                        for item in props.get("Health Items"): 
                                healthItems.add(item.get("ItemToDrop").get("RowName"))
                        for item in props.get("TransTower 01 Items"): 
                                transTaps.add(item.get("ItemToDrop").get("RowName"))
                        for item in props.get("TransTower 03 Items"):
                                name = item.get("ItemToDrop").get("RowName")
                                container = item.get("RandomLootRow").get("RowName")
                                octoTools[name].append(container)
upgradeTags = set()
for root,dirs,files in os.walk(exportFolder+r"\FW\HUB\MetaDataTables",topdown=True): 
        for file in files:
                if file == "DT_HubUpgrades_Water.json" or file == "DT_HubUpgrades_Default.json": # could go through RareLootManager's HubTags but whatever
                        with open(os.path.join(root,file), encoding='utf-8') as f:
                                data = json.load(f)
                                for table in data:
                                        rows = table.get("Rows")
                                        for row in rows:
                                                for tag in rows[row].get("ItemCostTags"):
                                                        upgradeTags.add(tag.get("Key").get("TagName"))
droneTags = set()
with open(exportFolder+r"\FW\UI\Manufactoring\Data\DT_ManufactoringRecipies.json") as f: 
        drones = ['Drone_FastTravel','Drone_Recovery', 'Drone_Construction'] # could go through RareLootManager's DroneTags but whatever
        data = json.load(f)
        for table in data:
                rows = table.get("Rows")
                for row in rows:
                        if row in drones:
                                for component in rows[row].get("UsedComponents"):
                                        droneTags.add(component.get("ItemTag").get("TagName"))
                        
with open(exportFolder+r"\Blueprints\Data\DataReference\DT_TagToRowHandle.json") as f:
        blacklist=['Drone_Construction','Drone_FastTravel','Drone_Recovery']
        data = json.load(f)
        for table in data:
                rows = table.get("Rows")
                for row in rows:
                        if row in droneTags:
                                droneItems.add(rows[row].get("DataRow").get("RowName"))
                        if row in upgradeTags:
                                upgradeItems.add(rows[row].get("DataRow").get("RowName"))

# at this point we should have every item in the game. Join sets that use any container unconditionally. Handle others individually
anywhereLoot = anywhereLoot.union(droneItems)
anywhereLoot = anywhereLoot.union(upgradeItems)
anywhereLoot = anywhereLoot.union(transTaps)
tunnelsLoot = tunnelsLoot.union(healthItems)
tunnelsLoot = tunnelsLoot.union(anywhereLoot)
surfaceLoot = surfaceLoot.union(anywhereLoot)

lootClasses = dict()
containerClasses = set()
lootArrayToContainers = defaultdict(set)
lootToWhatever = defaultdict(set)
for root,dirs,files in os.walk(exportFolder+"\FW\LootObjects",topdown=True):  # get container classes because its impossible to tell which map prop is a container
        for file in files:
                if '.json' not in file:
                        continue
                if '\\Containers\\' in root or file == 'BP_SpawnUnlockedBooze.json':
                        containerClasses.add(file.replace(".json","_C"))
                        with open(os.path.join(root,file), encoding='utf-8') as f:
                                text = f.read()
                                lookup = re.findall(r'"RowName": "(.*)"',text)
                                if len(lookup)>0:
                                        for container in lookup:
                                                lootToWhatever[container].add(file.replace(".json","_C"))
                elif '\\FromCorpses' in root: 
                        with open(os.path.join(root,file), encoding='utf-8') as f:
                                text = f.read()
                                lookup = re.findall(r'"RowName": "(.*)"',text)
                                if len(lookup)>0:
                                        for container in lookup:
                                                lootArrayToContainers[file.replace(".json","_C")].add(container)
                elif file == 'BP_SpawnBartenderSupplies.json':
                        lootClasses.update({file.replace(".json","_C"):"Bar Supplies"})
                elif 'DrillObject' not in file:
                        with open(os.path.join(root,file)) as f:
                                text = f.read()
                                lookup = re.findall(r'"RowName": "(.*)"',text)
                                if len(lookup)>0:
                                        lootClasses.update({file.replace(".json","_C"):lookup[0]})

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

maps = { # localized wiki names. Dont care about PlayerCheckinTests
        "AI_Validation_Map":"Scorched Enclave",
        "AI_Awareness_Map":"Scrapyard Nexus",
        "AshenMesa":"Ashen Mesa",
        "DowntownLostAngels":"Downtown Lost Angels",
        "ElephantMausoleum":"Elephant Mausoleum",
        "MechTrenches":"Mech Trenches",
        "StairwayGate":"Stairway Gate",
        "UndergroundCemetery":"Underground Cemetery",
        "Hub_ThunderDome":"Innards",
        "FrozenSwamp":"Frozen Swamp",
        "Shanti_rooftops":"Babel",
        "ProceduralTunnels":"Tunnels" 
}
containerToMapList = defaultdict(set) # Theres stuff like BP_LootContainer_Shanti_Random_Quest_Memento_C but thats not quest only, so why is it a separate container? Do only some containers spawn mementos?
looseLootToMapList = defaultdict(set)
for root,dirs,files in itertools.chain(os.walk(exportFolder+"\FW\Maps",topdown=True), os.walk(exportFolder+"\Maps",topdown=True)): # get a list of container names per map. Or the other way around actually
        for file in files:
                mapName = None
                for i in maps:
                        if i in root:
                                mapName = maps.get(i)
                if mapName:
                        with open(os.path.join(root,file)) as f:
                                mapData = json.load(f)
                                for stuff in mapData:
                                        propType = stuff.get("Type")
                                        if propType in containerClasses:
                                                containerToMapList[propType].add(mapName)
                                        elif propType in lootClasses:
                                                looseLootToMapList[lootClasses[propType]].add(mapName)
                                                
containerToMapList['BP_LootContainer_RareBooze_C'] = containerToMapList['BP_SpawnUnlockedBooze_C'] # I dont know anymore I just want this to end 
looseLootToMapList['BP_Eurasian_LockBox_Large_Quest'].add('Scrapyard Nexus') # this little shit spawns through encounters like a unit instead of being a normal item

itemToConditionDict = { # tried pulling this from map data but there are too many types of quest related props, this is easier. Also RG parts are not technically conditional but they only spawn as loose loot during quests, gotta account for that
	"Quest_SewersPlans":"Shifting Tide Pt.3",
	"Bar Supplies":"Fetch Bar Supplies",
	"Quest_WeaponSchematics":"Manufactured Heist",
	"BP_QuestItem_Jammer":"Clear Skies",
	"BP_QuestItem_MechPart":"Mechanical Momentum",
	"BP_QuestItem_SparePart":"Food Chain Interrupted",
	"Quest_DogTags":"Bond of Brothers",     
	"Quest_PersonnelData":"VIP Treatment Pt.1",
	"Quest_CommsDevice":"Lost Signals",
	"Quest_Logbook":"Burying Secrets",
        "QUEST_Totem":"Icon at Stake, The People's Icon",
        "BP_Eurasian_LockBox_Large_Quest":"Summon the Pain pt.2",
        "Quest_MedicalSupplies":"Scav's Prescription"
}
for item in at43parts:
        itemToConditionDict.update({item:"AT-43 Blueprint unlocked"})
for item in octoTools:
        itemToConditionDict.update({item:"Transmission Tower Pt.3"})

containerToConditionDict = defaultdict(set)
containerToConditionDict["BP_SpawnUnlockedBooze_C"].add("Bar constructed")
containerToConditionDict["RandomLoot_BoozeForDebugBar"].add("Bar constructed")
containerToUnitsList = defaultdict(list) # we need maps AND condition for it
containerLocalization = defaultdict(list) # list because in case of units one container drops from several guys
containerLocalization['BP_LootContainer_AshenMesa_Random_C'].append('Storage')  # Im not scared of copypasting
containerLocalization['BP_LootContainer_Meds_HighProbability_C'].append('Medical Supplies')
containerLocalization['BP_LootContainer_WeaponMods_HighProbability_C'].append('Weapon Mods')
containerLocalization['BP_LootContainer_Ammo_HighProbability_C'].append('Ammunition')
containerLocalization['BP_LootContainer_City_Random_C'].append('Supplies')
containerLocalization['BP_SpawnUnlockedBooze_C'].append('Alcohol Vault')
containerLocalization['BP_LootContainer_RareBooze_C'].append('Alcohol Vault')
containerLocalization['BP_LootContainer_Ammo_C'].append('Ammunition')
containerLocalization['BP_LootContainer_MedicalSupplies_C'].append('Medical Supplies')
containerLocalization['BP_LootContainer_EM_Random_C'].append('Storage')
containerLocalization['BP_LootContainer_EM_1MTrenches_C'].append('Supplies')
containerLocalization['BP_LootContainerDrone_C'].append('Drone Courier')
containerLocalization['BP_LootContainer_Random_QuestDeadOrga_C'].append('Dead OrgaMech')
containerLocalization['BP_LootContainer_FrozenSwamp_Random_Quest_Schedule_C'].append('Storage')
containerLocalization['BP_LootContainer_FrozenSwamp_Random_C'].append('Storage')
containerLocalization['BP_LootContainer_MechTrenches_Random_C'].append('Storage')
containerLocalization['BP_LootContainer_Tunnels_Cylinder_C'].append('Supplies')
containerLocalization['BP_LootContainer_Tunnels_MechChest_C'].append('Supplies')
containerLocalization['BP_LootContainer_Shanti_Random_Quest_Memento_C'].append('Storage')
containerLocalization['BP_LootContainerDrillTest_Quest_Shanti_C'].append('Medical Supplies')
containerLocalization['BP_LootContainer_Awareness_Random_C'].append('Storage')
containerLocalization['BP_LootContainer_Validation_Random_C'].append('Storage')
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

at43Maps = sorted(['Frozen Swamp', 'Scrapyard Nexus', 'Scorched Enclave', 'Downtown Lost Angels', 'Babel', 'Underground Cemetery', 'Ashen Mesa', 'Stairway Gate', 'Elephant Mausoleum', 'Mech Trenches'])
surfaceMaps = sorted(['Frozen Swamp', 'Scrapyard Nexus', 'Scorched Enclave', 'Downtown Lost Angels', 'Babel', 'Underground Cemetery', 'Ashen Mesa', 'Stairway Gate', 'Elephant Mausoleum', 'Mech Trenches'])
allMaps = sorted(['Frozen Swamp', 'Scrapyard Nexus', 'Scorched Enclave', 'Downtown Lost Angels', 'Babel', 'Underground Cemetery', 'Ashen Mesa', 'Stairway Gate', 'Elephant Mausoleum', 'Mech Trenches', 'Tunnels'])
finalOutput = defaultdict(list) # we need an output of rows like {Item:[{Container,Locations,Conditions}]} for every ite
altOutput = defaultdict(list)
wikiToLocations = defaultdict(set)
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
                        if item in looseLootToMapList:
                                row = {}
                                row.update({"Container":"Ground"})
                                row.update({"Locations":list(looseLootToMapList[item])})
                                if item in itemToConditionDict:
                                        row.update({"Condition":itemToConditionDict[item]})
                                finalOutput[name].append(row)
                        if item in itemToContainerList:
                                contToLocations = defaultdict(set)
                                for container in itemToContainerList[item]:
                                        if container in containerToUnitsList:
                                                for unit in containerToUnitsList[container]:
                                                        wikiName = unit.get("WikiName")
                                                        if wikiName:
                                                                if name not in altOutput[wikiName]:
                                                                        altOutput[wikiName].append(name)
                                                                maps = unit.get("Locations") # TODO group unconditional locations by wikiname
                                                                if maps:
                                                                        conditions = set()
                                                                        conditionToLocations = defaultdict(set)
                                                                        for location in maps:
                                                                                if location.get("Activated"):
                                                                                        condition = location.get("Condition") or False
                                                                                        conditions.add(condition)
                                                                                        conditionToLocations[condition].add(location.get("Map"))
                                                                                        if not condition:
                                                                                                wikiToLocations[wikiName].add(location.get("Map"))
                                                                        for condition in conditions:
                                                                                row = {}
                                                                                row.update({"Container":wikiName})
                                                                                row.update({"ContainerType":"Unit"})
                                                                                row.update({"Locations":sorted(list(conditionToLocations[condition]))})
                                                                                if condition:
                                                                                        row.update({"Condition":condition})
                                                                                #if row not in finalOutput[name]:
                                                                                        #finalOutput[name].append(row)
                                                                if "Scav Turret" in wikiName or "Recruit" in wikiName: # these have no maps but need loot info
                                                                        row = {}
                                                                        row.update({"Container":wikiName})
                                                                        row.update({"ContainerType":"Unit"})
                                                                        #if row not in finalOutput[name]:
                                                                                #finalOutput[name].append(row)
                                        if containerToMapList[container]:
                                                for contName in containerLocalization[container]:
                                                        contToLocations[contName] = contToLocations[contName] | set(ontainerToMapList[container])
                                        for thing in lootToWhatever[container]:
                                                for contName in containerLocalization[thing]:
                                                        contToLocations[contName] = contToLocations[contName] | set(containerToMapList[thing])
                                for contName in contToLocations:
                                        row = {}
                                        row.update({"Container":contName})
                                        row.update({"Locations":sorted(list(contToLocations[contName]))})
                                        if contName == "Drone Courier":
                                                row.update({"Condition":"Electro-Magnetic Railway Pt.1"})
                                        if name == "Medical Supplies":
                                                row.update({"Condition":"Scav's Prescription"})
                                        if row not in finalOutput[name]:
                                                finalOutput[name].append(row)
                        if item in anywhereLoot:
                                row = {}
                                row.update({"Container":"Any container"})
                                row.update({"Locations":allMaps})
                                finalOutput[name].append(row)
                        elif item in tunnelsLoot:
                                row = {}
                                row.update({"Container":"Any container"})
                                row.update({"Locations":['Tunnels']})
                                finalOutput[name].append(row)
                        elif item in surfaceLoot:
                                row = {}
                                row.update({"Container":"Any container"})
                                row.update({"Locations":surfaceMaps})
                                finalOutput[name].append(row)
                        if item in at43parts:
                                row = {}
                                row.update({"Container":"Any container"})
                                row.update({"Locations":at43Maps})
                                row.update({"Condition":"AT-43 Blueprint unlocked"})
                                finalOutput[name].append(row)
                        if item in octoTools:
                                row = {}
                                row.update({"Container":"Supplies"})
                                row.update({"Locations":['Underground Cemetery']})
                                row.update({"Condition":itemToConditionDict[item]})
                                finalOutput[name].append(row)
                                row = {}
                                row.update({"Container":"Ammunition"})
                                row.update({"Locations":['Underground Cemetery']})
                                row.update({"Condition":itemToConditionDict[item]})
                                finalOutput[name].append(row)
                                row = {}
                                row.update({"Container":"Medical Supplies"})
                                row.update({"Locations":['Underground Cemetery']})
                                row.update({"Condition":itemToConditionDict[item]})
                                finalOutput[name].append(row)

# missed a few things, not gonna bother reworking all for these 
finalOutput['Mystical Tech Totem'].append({"Container":"Ground","Locations":['Scrapyard Nexus'],"Condition":"Icon at Stake, The People's Icon"})
#finalOutput['Europan HK Suit Fragment'].append({"Container":"Europan EOD HunterKiller","Locations":surfaceMaps})
finalOutput['Bar Supplies'].append({"Container":"Ground","Locations":['Downtown Lost Angels'],"Condition":"Fetch Bar Supplies"})
#finalOutput['Pilot'].append({"Container":"Europan Exo","ContainerType":"Unit","Locations":['Ashen Mesa','Elephant Mausoleum','Scorched Enclave','Downtown Lost Angels','Frozen Swamp','Mech Trenches','Babel','Stairway Gate','Tunnels'],"Condition":"Bring Her In"})
#finalOutput['Pilot'].append({"Container":"Europan Exo","ContainerType":"Unit","Locations":['Underground Cemetery'],"Condition":"Rust in Peace, Bring Her In"})
#finalOutput['Pilot'].append({"Container":"Europan Red Baron Exo","ContainerType":"Unit","Locations":['Elephant Mausoleum'],"Condition":"Red Baron\'s Legacy, Bring Her In"})

for item in finalOutput: # find duplicate containers without condition, add locations to first, remove others
        duped = []
        for row in finalOutput[item]:
                container = row.get("Container")
                condition = row.get("Condition")
                if condition:
                        if "â€™" in condition:
                                row.update({"Condition":condition.replace("â€™","'")}) # Tormenorâ€™s Trail is a bitch
                if container in wikiToLocations and container not in duped and not condition:
                        duped.append(container)
                        row.update({"Locations":sorted(list(wikiToLocations[container]))})
                elif container in wikiToLocations and container in duped and not condition:
                        finalOutput[item].remove(row)

print("total items: "+str(len(finalOutput))) # stats
m = 0
xs = []
f = []
winnter = None
for k,v in finalOutput.items():
        xs.append(len(v))
        if len(v) >= 50:
                f.append(k)
        if len(v) > m:
                m = len(v)
                winner = k
print("max rows per one item: "+str(m)+" for "+winner)
print("average rows per item: "+str(statistics.mean(xs)))
print("items with >= 50 rows: "+str(len(f)))

for unit in altOutput:
        altOutput[unit].sort()

with open("dropsByCrate.json", "w") as outfile:
        json.dump(finalOutput, outfile, indent=4)
        
with open("dropsByUnit.json", "w") as outfile:
        json.dump(altOutput, outfile, indent=4)
