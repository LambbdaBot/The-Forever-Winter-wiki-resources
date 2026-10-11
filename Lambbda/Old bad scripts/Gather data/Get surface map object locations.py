import string
import re
import os
import json
import collections
import itertools
from collections import defaultdict
from itertools import chain
import statistics

"""
Get coordinates of every item and container on the map.

To be used with https://theforeverwinter.wiki.gg/wiki/Aerial_maps
"""

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

                      
containerClasses = set()
containerToMapList = defaultdict(set) # Theres stuff like BP_LootContainer_Shanti_Random_Quest_Memento_C but thats not quest only, so why is it a separate container? Do only some containers spawn mementos?
lootArrayToContainers = defaultdict(set)
lootToWhatever = defaultdict(set)
for root,dirs,files in os.walk(exportFolder+"\FW\LootObjects",topdown=True):  # get container classes because its impossible to tell which map prop is a container
        for file in files:
                containerClasses.add(file.replace(".json","_C"))

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

containerLocalization = {
"BP_ActivityItem_Jerrycan_C":"Jerrycan",
"BP_BaseItem_BuncoQuest_AmmoComponent_C":"Railgun-Ammo-Component",
"BP_BaseItem_BuncoQuest_BreechComponent_C":"Railgun-Breech-Component",
"BP_BaseItem_BuncoQuest_ControlStructuralFrameworkComponent_C":"Railgun-Framework-Component",
"BP_BaseItem_BuncoQuest_LegComponent_C":"Railgun-Leg-Component",
"BP_BaseItem_Drill_C":"Drill",
"BP_BaseItem_Quest_CommsDevice_C":"Comms-Device",
"BP_BaseItem_Quest_DogTags_C":"Dog-Tags",
"BP_BaseItem_Quest_Logbook_C":"Logbook",
"BP_BaseItem_Quest_PersonnelData_C":"Personnel-Data",
"BP_BaseItem_Quest_SewersPlans_C":"Sewers-Plans",
"BP_BrokenWeaponSpawner_C":"Broken-Weapons",
"BP_DrillDevice_C":"Drill-Device-IDK",
"BP_DrillObject_Container_FS_C":"Drillable-Container",
"BP_DrillObject_RollerShutter_C":"Drillable-Shutter",
"BP_DrillObject_TrainDoor_C":"Drillable-Door",
"BP_Gacha_HighValueRandom_West_C":"Gacha-Box",
"BP_Intel_QuestItem_C":"Europan-Radio",
"BP_LockBox_Large_C":"Lockbox",
"BP_Loot_Explosives_C":"Explosives",
"BP_Loot_Water_C":"Water",
"BP_LootContainer_Armament_T1_C":"Armaments-Bin-T1",
"BP_LootContainer_Armament_T2_C":"Armaments-Bin-T2",
"BP_LootContainer_Armament_T3_C":"Armaments-Bin-T3",
"BP_LootContainer_Armament_T4_C":"Armaments-Bin-T4",
"BP_LootContainer_Army_T1_C":"Military-Crates-T1",
"BP_LootContainer_Army_T2_C":"Military-Crates-T2",
"BP_LootContainer_Army_T3_C":"Military-Crates-T3",
"BP_LootContainer_Army_T4_C":"Military-Crates-T4",
"BP_LootContainer_Civilian_ShantiMemento_C":"Civil-Goods-Canister-Memento",
"BP_LootContainer_Civilian_T1_C":"Civil-Goods-Canister-T1",
"BP_LootContainer_Civilian_T2_C":"Civil-Goods-Canister-T2",
"BP_LootContainer_Civilian_T3_C":"Civil-Goods-Canister-T3",
"BP_LootContainer_Civilian_T4_C":"Civil-Goods-Canister-T4",
"BP_LootContainer_FrozenSwamp_Random_Activity_WaterThiefMask_C":"Storage-WT-Mask",
"BP_LootContainer_Material_T1_C":"Materials-Bin-T1",
"BP_LootContainer_Material_T2_C":"Materials-Bin-T2",
"BP_LootContainer_Material_T3_C":"Materials-Bin-T3",
"BP_LootContainer_Material_T4_C":"Materials-Bin-T4",
"BP_LootContainer_Medical_T1_C":"Medical-Bin-T1",
"BP_LootContainer_Medical_T2_C":"Medical-Bin-T2",
"BP_LootContainer_Medical_T3_C":"Medical-Bin-T3",
"BP_LootContainer_Medical_T4_C":"Medical-Bin-T4",
"BP_LootContainer_Provision_T1_C":"Provisions-Cache-T1",
"BP_LootContainer_Provision_T2_C":"Provisions-Cache-T2",
"BP_LootContainer_Provision_T3_C":"Provisions-Cache-T3",
"BP_LootContainer_Provision_T4_C":"Provisions-Cache-T4",
"BP_LootContainer_Random_QuestDeadOrga_C":"Dead-Orgamech",
"BP_LootContainer_TargetingComp_C":"AA-Gun-Supplies",
"BP_LootContainerDrillTest_Quest_Shanti_C":"Drillable-Medical-Crate",
"BP_LootContainerDrone_C":"Drone-Courier",
"BP_QuestItem_MechPart_C":"Mech-Part",
"BP_QuestItem_SparePart_C":"Spare-Part",
"BP_RigEquipment_PneumaticJump_C":"Pneumatic-Jump",
"BP_RigEquipment_RigLight_C":"Rig-Light",
"BP_SpawnBartenderSupplies_C":"Bar-Supplies",
"BP_SpawnUnlockedBooze_C":"Alcohol-Vault",
"BP_CrateSpawner_ForQuests_TransTower_Tools_C":"Octotools-crate"
}

looseLootToMapList = defaultdict(set)
mapContainerCoords = defaultdict(dict)
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
                                                name = stuff.get("Name")
                                                if propType in containerLocalization:
                                                        locale = containerLocalization[propType]
                                                for stuff2 in mapData:
                                                        pt2 = stuff2.get("Type")
                                                        if pt2 == 'SceneComponent':
                                                                outer = stuff2.get("Outer")
                                                                if outer == name:
                                                                        if locale:
                                                                                propType = locale
                                                                        #containers.add(propType)
                                                                        try:
                                                                                x = stuff2.get("Properties").get("RelativeLocation").get("X")
                                                                                y = stuff2.get("Properties").get("RelativeLocation").get("Y")
                                                                                z = stuff2.get("Properties").get("RelativeLocation").get("Z")
                                                                        except AttributeError:
                                                                                continue
                                                                        row = {}
                                                                        row.update({"x":x})
                                                                        row.update({"y":y})
                                                                        row.update({"name":"z: "+str(z)})
                                                                        if mapName in mapContainerCoords:
                                                                                array = mapContainerCoords[mapName].get(propType)
                                                                                if array:
                                                                                        array.append(row)
                                                                                        mapContainerCoords[mapName].update({propType:array})
                                                                                else:
                                                                                        mapContainerCoords[mapName].update({propType:[row]})
                                                                        else:
                                                                                mapContainerCoords[mapName].update({propType:[row]})

for mapName in mapContainerCoords:
        with open(mapName+".json", "w") as outfile:
                json.dump(mapContainerCoords[mapName], outfile, indent=4)
