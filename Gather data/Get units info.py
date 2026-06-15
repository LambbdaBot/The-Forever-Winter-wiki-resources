import string
import re
import os
import json
import collections
import itertools
from collections import defaultdict
from itertools import chain

"""
Get unit stats, loot and locations. Script is outdated and broken.
"""

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content' # got everything exported as jsons. At minimum you need all files starting with BP_, BPC_, AIDEF_, or DA_, and everything in /Maps and /FW/Maps, and AI_Scav_MaskMan
def getFile(name):
        for root,dirs,files in os.walk(exportFolder,topdown=True): # could be optimized with specific dirs through itertools but whatever
                for file in files:
                        if (file == name):
                                return os.path.join(root,file)
        print("getFile: could not find "+name)
        return

def getStatWithSuper(text, stat):
        stats=re.findall(r'"'+stat+'": ([^,]*)',text)
        if len(stats)>0:
                return float(stats[0])
        else:
                # come on, everybody has %STAT%. Better check super
                superClass = re.findall(r'Super": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)_C', text)
                if len(superClass)>0:
                        with open(getFile(superClass[0]+".json")) as f:
                                text = f.read()
                                return getStatWithSuper(text, stat)
                else:
                        return 0.0

codexEnemies={  # codex containers are hardcoded in BPC_IncomingDamageMod apparently? 
"BP_AI_Euruska_Stalker_C":"BP_LootContainer_Drill_Codex_Grabber_C",
"BP_AI_Euruska_Stalker_HK_C":"BP_LootContainer_Drill_Codex_Grabber_C",
"BP_AI_Euruska_Stalker_Pregnant_Quest_C":"BP_LootContainer_Drill_Codex_Grabber_C",
"BP_AI_Euruska_Stalker_Underground_C":"BP_LootContainer_Drill_Codex_Grabber_C",
"BP_Mech_Eurasia_MediumMech_C":"BP_LootContainer_Drill_Codex_MediumMech_C",
"BP_Mech_Europa_MediumMech_C":"BP_LootContainer_Drill_Codex_MediumMech_C",
"BP_AI_Eurasia_MotherCourage_C":"BP_LootContainer_Drill_Codex_MotherCourage_C",
"BP_Mech_Scav_RatKing_C":"BP_LootContainer_Drill_Codex_RatKing_C",
"BP_Mech_Toothy_C":"BP_LootContainer_Drill_Codex_Toothy_C",
"BP_Mech_MedMech_C":"BP_LootContainer_Drill_Codex_MediumMech_C",
"BP_Mech_MedMech_HK_C":"BP_LootContainer_Drill_Codex_MediumMech_C",
"BP_Euruska_MedMech_C":"BP_LootContainer_Drill_Codex_MediumMech_C",
"BP_AI_Euruska_OrgaMech_C":"BP_LootContainer_Drill_Codex_Orga_C",
"BP_AI_Euruska_OrgaMech_HK_C":"BP_LootContainer_Drill_Codex_Orga_C",
"BP_AI_Eurasia_Opal_C":"BP_LootContainer_Drill_Codex_Opal_C",
"BP_AI_Euruska_ShieldOfficer_C":"BP_LootContainer_Drill_Codex_ShieldOfficer_C",
"BP_AI_Euruska_ShieldOfficer_HK_C":"BP_LootContainer_Drill_Codex_ShieldOfficer_C",
"BP_AI_Eurasia_Opal_HK_C":"BP_LootContainer_Drill_Codex_Opal_C"
}
def getLootWithSuper(text, file):
        unit = file.replace(".json","_C")
        loot = set() # set because I don't care about number of containers, only their loot pool
        if any(key == unit for key in codexEnemies):
                loot.add(codexEnemies.get(unit))
        containers = re.findall(r'Loot(?: Object)?(?: Class)?": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)\'',text)     # some things have 'Loot Object', some have 'Loot Class', some have 'Loot Object Class', and weapon debris is a separate thing
        if len(containers)>0:
                for container in containers:
                        loot.add(container)
        if len(loot)==0:
                superClass = re.findall(r'Super": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)_C', text)
                if len(superClass)>0:
                        with open(getFile(superClass[0]+".json")) as f:
                                text = f.read()
                                return getLootWithSuper(text, file)
        return loot

waterThiefRaiders = ["BP_AI_WaterThief_Looter_C","BP_AI_WaterThief_Berzerker_C","BP_AI_WaterThief_Skirmisher_C","BP_AI_WaterThief_Quest_Riptide_C","BP_AI_WaterThief_Turret_C"]
def getLocations(unit):
        with open(exportFolder+"/FW/AI/Spawners/ScenarioSystem/ScenarioDataTables/DT_ScenarioEncounters_NPCs.json") as f:
                text = f.read()
                maps = []
                if unit in encounterReferences: # units without encounters (direct reference from the map, usually HK) are saved as themselves
                        for location in encounters[unit]:
                                maps.append(location)
                for encounter in encounterReferences: # units that have encounters
                        if unit in encounterReferences[encounter]:
                                for location in encounters[encounter]:
                                        maps.append(location)
                tags = re.findall(r''+unit+'[\s\S]*?\[[\s\S]*?\]', text)
                if len(tags)>0:
                        tags = set(re.findall(r'TagName": "(.*)"', tags[0]))
                        for encounter in encounterTags: # encounterTags contains a list of sets of tags corresponding to an encounter. In other words, an encounter has several units and each of them has several tags (tagsGroup)
                                for tagsSet in encounterTags[encounter]:
                                        if tagsSet.issubset(tags): # tags match, unit is eligible to spawn in encounter. Now to find where it spawns
                                                for location in encounters[encounter]:
                                                        maps.append(location)
                if len(maps)<1:
                        print(unit+" not found on any location!")
                        return maps
                else:
                        seen = set()
                        seenWoCondition = set() 
                        seenActivated = set() 
                        new_l = []
                        for d in maps: # removing duplicates from list of dicts
                            condition = d.get("Condition") 
                            activated = d.get("Activated")
                            if activated is None: # only for units with direct references
                                    d.update({"Activated":True})
                                    activated = True
                            if not condition and activated:
                                seenWoCondition.add(d.get("Map"))
                            if activated:
                                seenActivated.add(d.get("Map"))
                            t = tuple(d.items())
                            if t not in seen:
                                seen.add(t)
                                new_l.append(d)
                        toRemove = []
                        for d in new_l:
                            condition = d.get("Condition") # if a unit spaws unconditionally AND with a condition, remove the conditional entry cause whatever
                            activated = d.get("Activated") 
                            if condition:
                                if d.get("Map") in seenWoCondition:
                                        toRemove.append(d)
                            if not activated:
                                if d.get("Map") in seenActivated:
                                        toRemove.append(d)
                                if unit in waterThiefRaiders:  # exception handling for Shifting Tide 5 and Liberate the Innards
                                        if d.get("Map") in ["Elephant Mausoleum", "Frozen Swamp", "Stairway Gate"]:
                                                d.update({"Condition":"destroy 8 [[Water Thief Drone]]s in [[Frozen Swamp]]"})
                                        if d.get("Map") == "Downtown Lost Angels":
                                                d.update({"Condition":"Shifting Tide Pt.5"})
                                                d.update({"Activated":True})
                                        if d.get("Map") == "Innards":
                                                d.update({"Condition":"Liberate the Innards"})
                                                d.update({"Activated":True})
                                if unit == "BP_AI_Eurasia_Opal_HK_C":
                                        d.update({"Condition":"[[Radar Walker]]s hacked"})
                                        d.update({"Activated":True})
                                if unit == "BP_AI_Europa_EOD_Officer_Quest_C":
                                        d.update({"Condition":"Psycho on the Loose"})
                                        d.update({"Activated":True})
                                        
                        new_l = [elem for elem in new_l if elem not in toRemove]
                        return new_l
                
def getPrimaryWeaponWithSuper(text):
        weapon = None
        if "BP_Squadv2_Euruska_FemaleOfficer_RFL01_C" in text: # this one chick uses overrides her super's UseRandomWeapon prop and I dont want to modify the method to pass overridden props into super just for her
                return "BP_WPN_AI_RFL01_C"
        weaponIsRandom = len(re.findall(r'"UseRandomWeapon\?": true',text))>0
        if weaponIsRandom:
                weapons = re.findall(r'RandomPrimaryWeapons[\s\S]*?\]', text)
                if len(weapons)>0:
                        weapon = set(re.findall(r'ObjectName": "BlueprintGeneratedClass\'(.*)\'',weapons[0]))
                        return weapon
        weapon = re.findall(r'Primary Weapon": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)\'', text)
        if len(weapon)>0:
                return weapon[0]
        weapon = re.findall(r'My Weapon": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)\'', text)
        if len(weapon)>0:
                return weapon[0]
        superClass = re.findall(r'Super": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)_C', text)
        if len(superClass)>0:
                with open(getFile(superClass[0]+".json")) as f:
                        text = f.read()
                        return getPrimaryWeaponWithSuper(text)
        return

weaponLocalization={ # wiki names for weapons. Only for bot guns since that's what we're working with here
        "BP_Mech_AK_C":"Mech AK",
        "BP_WPN_20mmTurret_C":"Europan Turret",
        "BP_WPN_20mmTurret_Innards_C":"Innards Turret",
        "BP_WPN_AI_HRF01a_C":"SCAR (AI version)",
        "BP_WPN_AI_HRF01b_C":"SCAR (sniper build)",
        "BP_WPN_AI_LMG01_C":"MG34 (AI)",
        "BP_WPN_AI_LMG02_C":"SAW (AI)",
        "BP_WPN_AI_Recruit_LMG02_C":"SAW (scav build)",
        "BP_WPN_AI_RFL01_C":"AK (drum build)",
        "BP_WPN_AI_RFL01_LowTech_C":"AK (AI)",
        "BP_WPN_AI_RFL01_Recruits_C":"AK (scav build)",
        "BP_WPN_AI_RFL01_SniperBuild_C":"AK (sniper build)",
        "BP_WPN_AI_RFL01_v2_C":"AK (bayonet build)",
        "BP_WPN_AI_SHG01_C":"S12 (AI)",
        "BP_WPN_ChopperMachinegun_C":"Chopper machinegun",
        "BP_WPN_ChopperMachinegun_C":"Chopper machinegun",
        "BP_WPN_ChopperMissileLauncher_C":"Rocket pods",
        "BP_WPN_ChopperMissileLauncher_C":"Rocket pods",
        "BP_WPN_Drone_C":"Drone machinegun",
        "BP_WPN_Europa_Merkava_Machinegun_C":"Tank machinegun",
        "BP_WPN_Euruska_T90_MachineGun_C":"Tank machinegun",
        "BP_WPN_Exo_LeftStubbyGun_C":"Exo machinegun",
        "BP_WPN_Exo_LeftStubbyGun_C":"Exo machinegun",
        "BP_WPN_Exo_RedBarron_LeftStubbyGun_C":"Exo machinegun",
        "BP_WPN_Exo_RedBarron_LeftStubbyGun_C":"Exo machinegun",
        "BP_WPN_Exo_RedBarron_RightArm_C":"Exo arm cannon",
        "BP_WPN_Exo_RedBarron_RightArm_C":"Exo arm cannon",
        "BP_WPN_Exo_RightArm_C":"Exo arm cannon",
        "BP_WPN_GRL01_AI_C":"Grenade Launcher (AI)",
        "BP_WPN_GRL01b_AI_C":"Grenade Launcher (custom build)",
        "BP_WPN_HRF02_AI_C":"36M AntiTank (AI)",
        "BP_WPN_HRF03_AI_C":"NTW-20 (AI)",
        "BP_WPN_LMG03_AI_C":"M60 (AI)",
        "BP_WPN_LMG04_AI_Recruits_C":"RPD (scav build)",
        "BP_WPN_MediumMech_LongRifle_C":"Mech rifle",
        "BP_WPN_MediumMech_LongRifle_HK_C":"Mech rifle",
        "BP_WPN_MediumMech_LongRifle_Ratking_C":"Mech rifle",
        "BP_WPN_MediumMech_MiniGun_Center_C":"Mech minigun",
        "BP_WPN_MediumMech_MiniGun_Center_Ratking_C":"Mech minigun",
        "BP_WPN_MediumMech_QuadGun_Left_C":"Rocket pods",
        "BP_WPN_MediumMech_QuadGun_Left_Ratking_C":"Rocket pods",
        "BP_WPN_Opal_GunHand_C":"Opal machinegun",
        "BP_WPN_RFL01B_v2_AI_C":"RPK (AI)",
        "BP_WPN_RFL01B_v3_AI_Recruit_C":"RPK (AI)",
        "BP_WPN_RFL12_AI_C":"M4A1 (AI)",
        "BP_WPN_RFL20_AI_C":"SVD (AI)",
        "BP_WPN_RFL23AI_C":"M16 (AI)",
        "BP_WPN_RFL23b_AI_C":"M16 (custom build)",
        "BP_WPN_Rook_C":"Scav Turret",
        "BP_WPN_SHG03_AI_C":"USAS-12 (AI)",
        "BP_WPN_SHG04_AI_C":"VEPR-12 (AI)",
        "BP_WPN_SHG04_AI_Recruits_C":"VEPR-12 (scav build)",
        "BP_WPN_SHG05_AI_C":"AA12 (AI)",
        "BP_WPN_SMG01AI_C":"Kriss Vector 45 (AI)",
        "BP_WPN_SMG05AI_C":"APC9 Pro (AI)",
        "BP_WPN_SMG05AI_ExoPilotRecruit_C":"APC9 Pro (scav build)",
        "BP_WPN_SMG06AI_C":"P90 (AI)",
        "BP_WPN_SMG07AI_C":"PP-19 Vityaz (AI)",
        "BP_WPN_SMG07AI_Recruits_C":"PP-19 Vityaz (scav build)",
        "BP_WPN_StiltWalker_MiniGun_C":"Walker Minigun",
        "BP_WPN_StiltWalker_Missile_Outer_Left_C":"Missile launcher",
        "BP_WPN_Toothy_RailGun_C":"Toothy railgun",
        "BP_WPN_Toothy_ShoulderMachineGun_C":"Toothy machinegun"
}
ammoLocalization={ # wiki names for ammo
        "556":"556x45MM Ammo",
        "127":"127x55MM Ammo",
        "545":"[[5.45mm Ammo SURPLUS]]<br>[[545x39MM Ammo]]<br>[[5.45mm Cryo Ammo]]",
        "762":"762x39MM Ammo",
        "357":"357 Ammo",
        "40mmHE":"40MM Ammo",
        "919":"9x19MM Ammo",
        "57x28":"57x28MM Ammo",
        "NitroExpress":"Nitro Express Ammo",
        "45ACP":"45 ACP Ammo",
        "308":"308 Ammo",
        "50cal":"50cal Ammo",
        "12g":"12-Gauge Ammo",
        "Thrown":"Grenade",
        "54R":"762x54MMR Ammo",
        "50PST":"50PST Ammo",
        "20mm":"20x105MM Ammo"
}
tanks={
        "BP_AI_Europa_Merkava_Quest_BodyBoss_C":{"BP_MainTurret_Projectile_Quest_BodyBoss_C":{"BP_TankWeapon_NEW_C":{"Damage":11666.0,"FireRate":1.0,"Splash": 0.0,"Knockdown": False,"Pellets": 1,"Magazine": 999999999,"InternalName": "BP_MainTurret_Projectile_Quest_BodyBoss_C","WikiName": "Corpse tank cannon"}}},
        "BP_AI_Europa_Merkava_C":{"BP_TankWeapon_NEW_C":{"Damage":8750.0,"FireRate":1.0,"Splash": 0.0,"Knockdown": False,"Pellets": 1,"Magazine": 999999999,"InternalName": "BP_TankWeapon_NEW_C","WikiName": "Tank cannon"}},
        "BP_AI_Europa_AA_Quest_C":{"BP_TankWeapon_NEW_C":{"Damage":8750.0,"FireRate":1.0,"Splash": 0.0,"Knockdown": False,"Pellets": 1,"Magazine": 999999999,"InternalName": "BP_TankWeapon_NEW_C","WikiName": "Tank cannon"}},
        "BP_AI_Euruska_T90_C":{"BP_TankWeapon_NEW_C":{"Damage":8750.0,"FireRate":1.0,"Splash": 0.0,"Knockdown": False,"Pellets": 1,"Magazine": 999999999,"InternalName": "BP_TankWeapon_NEW_C","WikiName": "Tank cannon"}}
}
weaponData = {}
headshotMults = {}
with open(exportFolder+"\FW\Weapons\Weapon_V2\DT_CaliberToHeadshotMulti.json") as f:
        stuff = json.load(f)
        for thing in stuff:
                rows = thing.get("Rows")
                for row in rows:
                        headshotMults.update({row:rows[row].get("HeadshotMulti_2_9B53E75048FB0CC727824C8EFEF643F0")})
for root,dirs,files in itertools.chain(os.walk(exportFolder+"\FW\Weapons\Weapon_V2",topdown=True), os.walk(exportFolder+"\FW\Mechs\MechWeapons",topdown=True), os.walk(exportFolder+"\FW\AI\Vehicles",topdown=True), os.walk(exportFolder+"\FW\AI\Rooks",topdown=True), os.walk(exportFolder+"\Character\Euruska\Med_Mech\Mech_AK")):
        for file in files:  # get ALL weapon data for damage info
                if (file.startswith("BP_WPN_") or file == "BP_Mech_AK.json"): # AK's the only weapon in /Character
                        stats = {}
                        definition = ""         # DA stuff here
                        superName = None        
                        damage = 0.0
                        splash = 0.0
                        fireRate = 0.0
                        knockdown = False
                        pellets = 1
                        ammo = None
                        headshotModifier = 0.0
                        mag = 0
                        threat = None
                        category = None
                        fireModes = "Semi"      # BP stuff here
                        allowBurst = None
                        allowAuto = None
                        with open(os.path.join(root,file)) as f:
                                text = f.read()
                                definitions = re.findall(r'WeaponDefinition": {[\s]*"ObjectName": "FWWeaponDefinition\'(.*)\'', text)
                                projectile = re.findall(r'ProjectileClass": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)_C\'', text)
                                lootableDebris = 'BPC_LootableArmorAndWeapons_C' in text
                                if 'Allow Burst?": false' in text:
                                        allowBurst = False
                                if 'Allow Auto?": false' in text:
                                        allowAuto = False
                                superClass = re.findall(r'Super": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)_C', text)
                                if len(superClass)>0: # check super, if anything isn't in main class it might be there
                                        superName = superClass[0]+"_C"
                                        with open(getFile(superClass[0]+".json")) as h:
                                                textSuper = h.read()
                                                if len(definitions) == 0:
                                                        definitions = re.findall(r'WeaponDefinition": {[\s]*"ObjectName": "FWWeaponDefinition\'(.*)\'', textSuper)
                                                if len(projectile) == 0:
                                                        projectile = re.findall(r'ProjectileClass": {[\s]*"ObjectName": "BlueprintGeneratedClass\'(.*)_C\'', textSuper)
                                                if not lootableDebris:
                                                        lootableDebris = 'BPC_LootableArmorAndWeapons_C' in textSuper
                                                if allowBurst is None:
                                                        if 'Allow Burst?": false' in text:
                                                                allowBurst = False
                                                if allowAuto is None:
                                                        if 'Allow Auto?": false' in text:
                                                                allowAuto = False
                                if allowBurst is None:
                                        allowBurst = True
                                if allowAuto is None:
                                        allowAuto = True
                                if len(definitions) > 0:
                                        definition = definitions[0]
                                        with open(getFile(definition+".json")) as g:
                                                textDefinition = g.read()
                                                buckshots = re.findall(r'"NumberOfBuckshots": ([^,]*)', textDefinition)
                                                if len(buckshots)>0:
                                                        pellets = int(buckshots[0])
                                                damages = re.findall(r'"WeaponDamage": ([^,]*)',textDefinition)
                                                if len(damages)>0:
                                                        damage = float(damages[0])
                                                if len(re.findall(r'bKnockDownPlayerWhenHit', textDefinition))>0:
                                                        knockdown = True
                                                fireRates = re.findall(r'"FireRate": ([^,]*)',textDefinition)
                                                if len(fireRates)>0:
                                                        fireRate = 1/float(fireRates[0])
                                                elif allowBurst:
                                                        burstRoF = re.findall(r'"BurstFireRate": ([^,]*)',textDefinition)
                                                        if len(burstRoF)>0:
                                                                fireRate = 1/float(burstRoF[0])
                                                mags = re.findall(r'"MaxAmmo": ([0-9]*),?',textDefinition)
                                                if len(mags)>0:
                                                        mag = int(mags[0])
                                                threats = re.findall(r'Weapon\.Threat\.(.*)"',textDefinition)
                                                if len(threats)>0:
                                                        threat = threats[0]
                                                categories = re.findall(r'Weapon\.Type\.(.*)"',textDefinition)
                                                if len(categories)>0:
                                                        category = categories[0]
                                                ammos = re.findall(r'(Item\.Ammo\..*)"',textDefinition)
                                                if len(ammos)>0:
                                                        ammo = ammoLocalization.get(re.findall(r'\..*\.(.*)$',ammos[0])[0])
                                                        headshotModifier = headshotMults.get(ammos[0])
                                if len(projectile) > 0:
                                        with open(getFile(projectile[0]+".json")) as g:
                                                textProjectile = g.read()
                                                if len(re.findall(r'BPC_Explosion_Grenade_C',textProjectile))>0: # only way to add splash, guns that do not have this dont have aoe AFAIK
                                                        splash = 10000.0
                                if lootableDebris:
                                        stats.update({"Loot":"BP_RandomLoot_ExoDebris_C"}) # all weapon debris have this loot table AFAIK
                        if allowBurst:
                                fireModes+=", Burst"
                        if allowAuto:
                                fireModes+=", Auto"
                        stats.update({"Damage":damage})
                        stats.update({"Splash":splash})
                        stats.update({"FireRate":fireRate})
                        stats.update({"Knockdown":knockdown})
                        stats.update({"FireModes":fireModes})
                        stats.update({"Pellets":pellets})
                        stats.update({"Ammo":ammo})
                        stats.update({"Magazine":mag})
                        stats.update({"HeadshotModifier":headshotModifier})
                        stats.update({"Definition":definition})
                        stats.update({"Threat":threat})
                        stats.update({"Category":category})
                        stats.update({"InternalName":file.replace(".json","")})
                        name = file.replace(".json","_C")
                        if name in weaponLocalization:
                                stats.update({"WikiName":weaponLocalization.get(name)})
                        else:
                                stats.update({"WikiName":weaponLocalization.get(superName)})
                        weaponData.update({name : stats})

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
                    
encounters=defaultdict(list)
maps = { # localized wiki names
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
for root,dirs,files in itertools.chain(os.walk(exportFolder+"\FW\Maps",topdown=True), os.walk(exportFolder+"\Maps",topdown=True)): # get every possible encounter on every map
        for file in files:
                mapName = "UNKNOWN" # dev test map is unknown
                for i in maps:
                        if i in root:
                                mapName = maps.get(i)
                with open(os.path.join(root,file), encoding='utf-8') as f:
                        mapData = json.load(f) # FINE I wont use regex this time
                        for stuff in mapData:
                                if stuff.get("Type") == "ScenarioSpawner" or "BP_SpawnController" in stuff.get("Type"):
                                        props = stuff.get("Properties")
                                        if props:
                                                activated = props.get("bActivated")
                                                spawnerEncounters = list(itertools.chain.from_iterable((props.get("Encounters") or [], props.get("ReinforcementEncounters") or [])))
                                                for encounter in spawnerEncounters:
                                                        row = {}
                                                        if activated is False: # None is acceptable too
                                                                row.update({"Activated":False})
                                                        else:
                                                                row.update({"Activated":True})
                                                        if mapName == "UNKNOWN":
                                                                print("UNKNOWN MAP: "+root+"\\"+file) # only relevant if we found Encounters in the file
                                                                continue
                                                        encounterClass = re.findall(r'\.(.*)', encounter.get("EncounterClass").get("AssetPathName"))
                                                        questTags = encounter.get("QuestTags")
                                                        if len(encounterClass)>0:
                                                                row.update({"Map":mapName})
                                                                if questTags:
                                                                    if len(questTags)>1:
                                                                        print("TOO MANY TAGS FOR "+encounterClass[0]+" ON "+mapName)
                                                                    questName = ""
                                                                    try:
                                                                        questName = questNames[questTags[0]] # always 1 tag
                                                                    except KeyError:
                                                                        print("QUEST NOT FOUND BY TAG "+str(questTags))
                                                                    row.update({"Condition":questName})
                                                                encounters[encounterClass[0]].append(row)
                                                definitions = props.get("UnitDefinitions")
                                                if definitions:
                                                        for definition in definitions:
                                                                unit = re.findall(r'\.(.*)',definition.get("PawnClassPtr").get("AssetPathName"))[0] # no out of bounds index, trust
                                                                row = {}
                                                                row.update({"Map":mapName}) # never any quest tags for these
                                                                if mapName == "UNKNOWN":
                                                                        print("UNKNOWN MAP: "+root+"\\"+file) # only relevant if we found Encounters in the file
                                                                        continue
                                                                encounters[unit].append(row)


encounterReferences={} # some units are referenced directly while others are selected procedurally based on tags
encounterTags=defaultdict(list)
for encounter in encounters: 
        if "BP_Enc_" not in encounter: # sometimes units dont even have an encounter. Just write them in as themselves
                encounterReferences.update({encounter:encounter})
                continue
        with open(getFile(re.sub(r'_C$',".json",encounter))) as f: # get unit tag groups from encounter definitions
                  text = f.read()
                  references = re.findall(r'PawnClassPtr": {[\s]*"AssetPathName"[\s\S]*?\.(.*)"', text)
                  if len(references)>0:
                          encounterReferences.update({encounter:references})
                  tagGroups = re.findall(r'AllRequiredTags[\s\S]*?\[[\s\S]*?\]',text)
                  for group in tagGroups:
                          tags = re.findall(r'TagName": "(.*)"', group)
                          encounterTags[encounter].append(set(tags))
                          
unitLocalization = { # wiki infobox ids
"BP_AI_Eurasia_MotherCourage_BlindMother_C":"Blind Mother",
"BP_AI_Scav_Civilian_C":"Civilian",
"BP_AI_Scav_Civilian_ShantiQuest_C":"Civilian",
"BP_AI_Scav_Civilian_WaterThief_Skirmisher_C":"Civilian",
"BP_AI_Cultist_HeavyWeapons_C":"Cultist HeavyWeapons",
"BP_AI_Cultist_Pursuer_C":"Cultist Pursuer",
"BP_AI_Cultist_Soldier_C":"Cultist Soldier",
"BP_AI_Eurasia_Crawler_C":"Cyborg Crawler",
"BP_AI_Eurasia_Cyborg_C":"Cyborg Runner",
"BP_AI_Eurasia_Cyborg_A1_C":"Cyborg Runner",
"BP_AI_Eurasia_Cyborg_A2_C":"Cyborg Runner",
"BP_AI_Eurasia_Cyborg_A3_C":"Cyborg Runner",
"BP_AI_Eurasia_Scrambler_C":"Cyborg Scrambler",
"BP_Squadv2_Eurasia_Brawler_RFL01B_C":"Eurasian Brawler",
"BP_AI_Eurasia_Chopper_C":"Eurasian Chopper",
"BP_AI_Eurasia_Chopper_RiseFromBelow_C":"Eurasian Chopper",
"BP_Squadv2_Eurasia_Cyborg_SMG06_C":"Cyborg P90 Skull Face",
"BP_Squadv2_Eurasia_CyborgOfficer_SMG06_C":"Cyborg P90 Skull Face",
"BP_Squadv2_Eurasia_Female_SMG06_C":"Cyborg P90",
"BP_AI_Eurasia_Drone_C":"Eurasian Drone",
"BP_AI_Euruska_Drone_C":"Euruskan Drone",
"BP_AI_Eurasia_Soldier_Sniper_God_Quest_C":"Eurasian God Sniper",
"BP_Squadv2_Eurasia_BrawlerNoHelm_C":"Helmless Heavy Brawler",
"BP_AI_Eurasia_Heavy_Brawler_C":"Heavy Brawler",
"BP_AI_Eurasia_Heavy_Brawler_Elite_Quest_C":"-",
"BP_AI_Eurasia_MotherCourage_C":"Eurasian MotherCourage",
"BP_Squadv2_Eurasia_FemaleOfficer_SHG05_C":"Eurasian Officer AA12",
"BP_Squadv2_Eurasia_FemaleOfficer_SMG06_C":"Eurasian Officer P90",
"BP_AI_Eurasia_Soldier_Assaulter_Quest_C":"Eurasian Assaulter",
"BP_AI_Eurasia_Opal_C":"Eurasian Opal",
"BP_Squadv2_Eurasia_Cyborg_RFL01_C":"Eurasian Pack Leader",
"BP_Squadv2_Eurasia_CyborgPackLeader_RFL01_C":"Eurasian Pack Leader",
"BP_AI_Europa_Turret_C":"Europan Turret",
"BP_AI_Europa_Turret_20mm_C":"Europan Turret",
"BP_AI_Scav_Turret_20mm_C":"Scav Turret",
"BP_AI_WaterThief_Turret_C":"Water Thief Turret",
"BP_Squadv2_Europa_BodyGuard_HeavyShotgunner_Quest_C":"Europan Heavy Shotgunner",
"BP_Squadv2_Europa_BodyGuard_HRF01Tech_C":"Europan Bodyguard SCAR",
"BP_Squadv2_Europa_BodyGuard_SHG03_C":"Europan Bodyguard USAS-12",
"BP_AI_Europa_Drone_C":"Europan Drone",
"BP_AI_Europa_Drone_RiseFromBelow_C":"Europan Drone",
"BP_Squadv2_Europa_EliteSoldier_RFL12_C":"Europan Heavy Elite",
"BP_Squadv2_Europa_SleevelessElite_RFL23b_C":"Europan Light Elite",
"BP_AI_Europa_EOD_C":"Europan EOD MG34",
"BP_AI_Europa_EOD_HunterKiller_C":"Europan EOD HunterKiller",
"BP_Squadv2_Europa_EOD_SHG03_C":"Europan EOD USAS-12",
"BP_Mech_Exo_V2_C":"Europan Exo",
"BP_Squadv2_Europa_Grinn_HRF01_C":"GRINN SCAR",
"BP_Squadv2_Europa_Grinn_SHG01_C":"GRINN S12",
"BP_AI_Europa_Pursuer_Assassin_Quest_C":"Europan Assassin",
"BP_Mech_MedMech_C":"Europan Medium Mech",
"BP_Mech_MedMech_HK_C":"Europan Mech HK",
"BP_AI_Europa_Merkava_Quest_BodyBoss_C":"Europan Merkava Body Tank",
"BP_AI_Europa_AA_Quest_C":"-",
"BP_AI_Europa_Merkava_C":"Europan Merkava Tank",
"BP_Squadv2_Europa_Officer_LMG01_C":"Europan Officer",
"BP_AI_Europa_Female_Pilot_Quest_C":"Europan Pilot AK",
"BP_Squadv2_Europa_Pilot_SMG05_C":"Europan Pilot APC9",
"BP_AI_Europa_EOD_Pyro_C":"Europan Pyro",
"BP_Mech_Exo_V2_RedBarron_C":"Europan Red Baron Exo",
"BP_Squadv2_Europa_Sniper_HRF01b_C":"Europan Sniper SCAR",
"BP_Squadv2_Europa_Soldier_HRF03_C":"Europan Sniper NTW-20",
"BP_Squadv2_Europa_SleevelessSoldier_LMG03_C":"Europan Soldier M60",
"BP_Squadv2_Europa_SleevelessSoldier_RFL23_C":"Europan Conscript",
"BP_Squadv2_Europa_Soldier_HRF01_C":"Europan Soldier SCAR",
"BP_Squadv2_Europa_Soldier_RFL23b_C":"GRINN M16",
"BP_Squadv2_Europa_Spotter_SMG01_C":"Europan Spotter",
"BP_Mech_StiltWalker_C":"Europan Stilt Walker",
"BP_AI_Europa_Egghead_AlcoholQuest_C":"Europan Thief",
"BP_Squadv2_Europa_Tormentor_C":"Europan Tormentor",
"BP_AI_Europa_Soldier_StairwayVIP_C":"Europan VIP",
"BP_AI_Euruska_Rider_Commander_Quest_C":"Euruskan Commander",
"BP_AI_Euruska_Stalker_C":"Euruskan Grabber",
"BP_AI_Euruska_Stalker_HK_C":"Euruskan Stalker",
"BP_AI_Euruska_Stalker_Pregnant_Quest_C":"-",
"BP_AI_Euruska_Stalker_Underground_C":"Euruskan Grabber",
"BP_Squadv2_Euruska_Female_RFL01_C":"Euruskan Light AK",
"BP_Squadv2_Euruska_Infantry_LMG04_C":"Euruskan Heavy RPD",
"BP_Squadv2_Euruska_Infantry_RFL01_C":"Euruskan Heavy AK",
"BP_Squadv2_Euruska_Infantry_RFL01B_C":"Euruskan Heavy RPK",
"BP_Euruska_MedMech_C":"Euruskan Medium Mech",
"BP_Squadv2_Euruska_FemaleOfficer_RFL01_C":"Euruskan Light Officer",
"BP_Squadv2_Euruska_NamedOfficer01_GRL01_C":"Euruskan Heavy Officer GL",
"BP_Squadv2_Euruska_Officer_RFL01_C":"Euruskan Heavy Officer AK",
"BP_AI_Euruska_OrgaMech_C":"Euruskan OrgaMech",
"BP_AI_Euruska_OrgaMech_HK_C":"Euruskan OrgaMech HK",
"BP_Squadv2_Euruska_Rider_SMG07_C":"Euruskan Rider",
"BP_Squadv2_Euruska_Rider_SMG07_Quest_Tissue_C":"Infected Euruskan Rider",
"BP_AI_Euruska_Rider_Stairs_Quest_C":"Drugged Euruskan Rider",
"BP_AI_Euruska_ShieldOfficer_HK_C":"Euruskan Shield Officer",
"BP_Squadv2_Euruska_Sniper_RFL20_C":"Euruskan Sniper SVD",
"BP_Euruska_Sniper_Shanti_Quest_C":"Euruskan Sniper AntiTank",
"BP_Euruska_Sniper_Stairs_Quest_C":"Euruskan Sniper AntiTank",
"BP_Squadv2_Euruska_Spotter_SMG07_C":"Euruskan Spotter",
"BP_AI_Euruska_T90_C":"Euruskan T-90 Tank",
"BP_Mech_Toothy_C":"Euruskan Toothy Mech",
"BP_Euruska_Sniper_Quest_C":"Goldbrick",
"BP_AI_Recruitable_CultOfR_C":"Recruit Cultist",
"BP_AI_Recruitable_ExoPilot_C":"Recruit Pilot",
"BP_AI_Recruitable_ScavDog_C":"Recruit Scav Mule",
"BP_AI_Recruitable_OldMan_AK_C":"Recruit Skirmisher",
"BP_AI_Recruitable_OldMan_SAW_C":"Recruit Support",
"BP_Mech_Scav_RatKing_C":"The Rat King",
"BP_AI_WaterThief_NormalRegions_Berzerker_C":"Water Thief Berzerker Camp",
"BP_AI_WaterThief_Drone_C":"Water Thief Drone",
"BP_AI_WaterThief_NormalRegions_Looter_C":"Water Thief Looter Camp",
"BP_AI_WaterThief_NormalRegions_Skirmisher_C":"Water Thief Skirmisher Camp",
"BP_AI_WaterThief_Skirmisher_C":"Water Thief Skirmisher Raider",
"BP_AI_WaterThief_Sniper_Quest_C":"Water Thief Sniper",
"BP_AI_Europa_EOD_Officer_Quest_C":"Sadistic Europan EOD",
"BP_Squadv2_Europa_EOD_Warden_C":"Europan Warden",
"BP_AI_Europa_Pursuer_C":"Europan Pursuer",
"BP_AI_Europa_Egghead_C":"Europan Egghead",
"BP_AI_Cultist_Grenadier_C":"Cultist Grenadier",
"BP_AI_Europa_Signaler_C":"Europan Signaler",
"BP_AI_WaterThief_Quest_Riptide_C":"Riptide",
"BP_AI_WaterThief_Berzerker_C":"Water Thief Berzerker Raider",
"BP_AI_WaterThief_Looter_C":"Water Thief Looter Raider"
}
data = {}
banned=["Destroyed", "Spawner", "BP_Mech_AK", "_Enc_", "Projectile", "Debug", "WPN", "Marker", "Noise", "SplineManeuver", "Scenario", "Encounter", "Persistence", "Skel", "Controller", "Tracker", "Player"]
for root,dirs,files in itertools.chain(os.walk(exportFolder+"\FW\AI",topdown=True), os.walk(exportFolder+"\FW\Mechs",topdown=True), os.walk(exportFolder+"\Character",topdown=True)): # get every unit
        for file in files:
                if (file.startswith("BP_") and not any(word in file for word in banned)): # I wish I did startswith BP_AI but some legacy units simply start with BP_
                        row = {}
                        name = file.replace(".json","_C")
                        with open(os.path.join(root,file)) as f:
                                text = ""
                                try:
                                        text = f.read()
                                except UnicodeDecodeError:
                                        continue
                                health = getStatWithSuper(text, "DefaultHealth")
                                if health == 0.0:
                                        continue # found something weird
                                row.update({"Health":health})
                                pawn = re.findall(r'PawnDefinition": {[\s]*"ObjectName": "FWAIPawnDefinition\'(.*)\'', text)
                                if len(pawn)>0:
                                        with open(getFile(pawn[0]+".json")) as g:
                                                textPawn = g.read()
                                                row.update({"Experience":getStatWithSuper(textPawn, "KillExperienceValue")}) 
                                speed = getStatWithSuper(text, "Max ?Speed") # vehicles first. Flying things have 'MaxSpeed' but driving things have 'Max Speed'. What gives?
                                if speed == 0 or speed is None:
                                        speed = getStatWithSuper(text, "MaxWalkSpeed") # non-vehicles
                                if speed == 0 or speed is None:
                                        speed = getStatWithSuper(text, "MaxWalkSpeedCrouched") # freaks like the Scrambler
                                row.update({"Speed":speed})
                                loot = getLootWithSuper(text, file) # not setting loot in row yet, it depends on weapons for mech
                                row.update({"Locations":getLocations(name)})
                                weapon = getPrimaryWeaponWithSuper(text) # for units with only one gun
                                index = 1
                                if weapon:
                                        if type(weapon) is set:
                                                weapons = weapon
                                                for weapon in weapons:
                                                        row.update({"Weapon"+str(index):weapon})
                                                        row.update({weapon:weaponData[weapon]})
                                        else:
                                                row.update({"Weapon1":weapon})
                                                row.update({weapon:weaponData[weapon]})
                                else:
                                        # assume melee if we got no primary
                                        damage = getStatWithSuper(text, "MeleeAttackDamage")
                                        if damage > 0:
                                                row.update({"MeleeDamage":damage})
                                        # either a melee unit or a mech with several guns
                                        if len(pawn)>0:
                                                with open(getFile(pawn[0]+".json")) as g:
                                                        textPawn = g.read()
                                                        if not damage > 0:
                                                                if len(re.findall(r'AIMeleeMontage', textPawn))>0: # dont feel like figuring out what exactly gives melee attacks. If it has an anim set default value
                                                                        row.update({"MeleeDamage":2500.0})    
                                                        weapons = re.findall(r'WeaponClass": {[\s]*.*?\.(.*)"', textPawn) # btw we cant detect cannons for tanks, that stuff I add manually
                                                        # wikiNames = set() 
                                                        for weapon in weapons: 
                                                                #if weaponData[weapon].get("WikiName") not in wikiNames: # removing duplicates cause no one cares if a mech has exactly 4 identical misisle launchers
                                                                row.update({"Weapon"+str(index):weapon})
                                                                row.update({weapon:weaponData[weapon]})
                                                                if weaponData[weapon].get("Loot") is not None:
                                                                        loot.add(weaponData[weapon].get("Loot"))
                                                                index += 1
                                                                #wikiNames.add(weaponData[weapon].get("WikiName"))
                                if name in tanks: # exception handling for tanks
                                        row.update(list(tanks.values())[0]) # add first and only value in a dict
                                row.update({"Loot":re.sub(r"set\(\)|[{}']","",str(loot))}) # converting to string cause sets are not json serializable
                        with open(exportFolder+"\FW\Player\LocationMarker\BP_LocationMarker.json") as g: # getting ping name
                                text = g.read()
                                names = re.findall(r'Value.*?'+name+'[\s\S]*?SourceString[\s\S]*?Value": "(.*)"', text)
                                if len(names)>0:
                                        row.update({"Ping":names[0]})
                                else:
                                        row.update({"Ping":"Hostile"})
                        wikiName = unitLocalization.get(name)
                        if wikiName != '-' and wikiName is not None:
                                row.update({"WikiName":wikiName})
                        name = re.sub(r'_C$','',name)
                        data.update({name : row})
                        
with open("units.json", "w") as outfile:
        json.dump(data, outfile, indent=4)
