import json
import string
import re
import os
import time
import collections
from collections import defaultdict

from mwcleric import AuthCredentials
from mwcleric import WikiggClient

"""
(Re-)creates pages for weapon attachments based on the template below

Requirements:
        - itemLocalization.json - provided in Gather data
        - dropsByCrate.json - generated using Gather data\Get crate loot.py
        - quests.json - generated using Gather data\Get quest info (imi).py
        - extracting data tables in \Blueprints\Data\ and subfolders, as well as in \FW\UI\MainMenu\Blueprints\Data\
        - extracting weapon data in \WPN_Weapons\ and \FW\Weapons\
        Just extract everything to be safe.

Background:
        Attachments go into sockets. Most weapon parts have sockets. The "base weapon" is also a weapon part in this context. Weapons have a default set of parts.
        DT_WeaponCustomizationData holds info on which parts a weapon can have, which sockets these parts have and which parts are default.
        DT_WeaponCustomizationAttachmentsData holds info on attachments, which sockets they fit into and which sockets they have.
        There are exceptions, for example, muzzle devices depend on the weapon's caliber, as dictated in BP_WPN_Config and DT_WPN_Config_Setup.
        
Algorithm:
        For each attachment in ItemDetailsData (category = WepMod):
        Get sockets that it fits into
        Find weapons and parts that allow customizing said sockets
        Skip creating the page if:
                - The attachment cannot be removed or doesn't fit on anything
                - It cannot be obtained from loot, trading or quests
"""

# TODO
# fix AT43 having muzzle devices
# add unobtainable default parts
# add units as drops source

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content' # change this

# page template
WIKITEXT = """{{{{Infobox Attachment
|image={image}.png
|volume={volume}
|weight={weight}
|base value={buyValue}
|xp={xp}

|category={category}, {slot}

|magCapacity={magCapacity}
|suppressed={suppressed}
|fov={fov}
|rof={rof}
|stability={stability}
|accuracy={accuracy}
|recoilFirstPerson={recoilWristRel}
|recoilThirdPerson={recoilArmRel}
|stabilizationSpeed={stabilizeTimeBuff}
|stabilizationLength={stabilizeScalarBuff}
|reloadSpeed={reloadSpeed}
|adsSpeed={adsSpeed}
|damage={damage}{other}
|slot={slot}
|level={level}
|requiredXp={requiredXp}
|hk=No
|internalTag=Inventory.Item.{internalTag}
}}}}

==Description==
{description}{picture}

== Acquisition ==
=== Trading ===
{itemVendor}
=== Loot ===
{drops}
{{{{ItemLoot}}}}
=== Quests ===
{{{{QuestRewards}}}}

==Usage==
{weaponCompatibility}

"""
                
itemLocalization = {}
with open("itemLocalization.json") as f: # wiki names for items
        itemLocalization = json.load(f)

otherStatsDict = {
    "G-L 19 Upper Assmbly B":"Integrated optic sight",
    "G-L 19 Upper Assmbly C":"Integrated optic sight",
    "M16 Upper Assmbly C":"Integrated scope",
    "SVD Upper Assmbly B":"Integrated scope",
    "SOG Receiver B":"Integrated optic sight",
    "VHS2 Upper Assembly B":"Integrated scope"
}

class Creator:
    summary = 'Automatically creating weapon attachment pages from in-game data'

    def __init__(self):
        credentials = AuthCredentials(user_file="me")
        # the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
        # test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
        # so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
        # then change it to your wiki afterwards
        self.site = WikiggClient('test', credentials=credentials)
        self.itemNames = {}
        
        with open(exportFolder+"\Blueprints\Data\ItemDetailsData.json") as f:
                self.items = json.load(f)
                
        for table in self.items:
                rows = table.get("Rows")
                for row in rows:
                        if row in itemLocalization:
                                rows[row].get("ItemName").update({"LocalizedString":itemLocalization[row]}) # fix duplicated item names
                        self.itemNames.update({row:rows[row].get("ItemName").get("LocalizedString") or "NOT LOCALIZED!"})
                        
        def get_stock(vendor):
                stock = []
                stock.append(vendor.get("MapedItemsSold"))
                stock.append(vendor.get("MapedWeaponsSold"))
                stock.append(vendor.get("MapedRigsSold"))
                stock.append(vendor.get("MapedContainersSold"))
                stock.append(vendor.get("MapedFramesSold"))
                stock.append(vendor.get("MapedDangliesSold"))
                stock.append(vendor.get("MapedBuddiesSold"))
                return stock
        
        with open(exportFolder+"\Blueprints\Data\VendorDataTable.json") as f:
                vendorData = json.load(f)
                for table in vendorData:
                        self.vendors = {}
                        rows = table.get("Rows")
                        self.vendors.update({"Luca":get_stock(rows.get("WesternWeaponVendor"))})
                        self.vendors.update({"Kane":get_stock(rows.get("EasternWeaponVendor"))})
                        self.vendors.update({"Heisenburg":get_stock(rows.get("MedicalVendor"))})
                        self.vendors.update({"Bundleton":get_stock(rows.get("RigVendor_V2"))})
                        self.vendors.update({"Slade":get_stock(rows.get("RecruitVendor"))})
                        self.vendors.update({"Bunco":get_stock(rows.get("ScavSurplusVendor"))})
        
        self.questRewards=set()
        with open("quests.json") as f:  
                quests = json.load(f)
                for k, v in quests.items():
                    if v.get("QuestRewards"):
                        for thing in v.get("QuestRewards"):
                            for k2, v2 in thing.items():
                                if k2 in self.itemNames:
                                    self.questRewards.add(self.itemNames[k2])
                        
        with open(exportFolder+r"\Blueprints\Data\Value\ValueV2_WEAPONS_PARTS.json") as f:
                self.values = json.load(f)
                
        with open(exportFolder+r"\FW\UI\MainMenu\Blueprints\Data\DT_WeaponCustomizationData.json") as f: # get a list of parts for each socket type; get weapons that are compatible with these parts and either allow customization or use this part as default
                self.socketToPartsList = defaultdict(list) # list of parts using this socket
                self.weaponToSocketToCustomizeablePartsList = defaultdict(dict)  # why the fuck are pistol barrels here
                self.partsToWeaponList = defaultdict(list) # weapons using this part
                self.integralPartsSockets = {} 
                weapons = json.load(f)
                for table in weapons: 
                        for weapon, weaponData in table.get("Rows").items():
                                defaultParts = [] # get attachmentcategory and defaultindex in defaultparts, get matching part ids in possibleparts
                                attachmentCategoryToIndex = {}
                                for defaultPart in weaponData.get("DefaultParts"):
                                         attachmentCategoryToIndex.update({defaultPart.get("AttachmentCategory"):defaultPart.get("DefaultIndex")})
                                for partType in weaponData.get("PossibleParts"):
                                         parts = partType.get("Parts")
                                         customizeable = partType.get("PartCustomizeable") and len(parts)>1
                                         attachmentCategory = partType.get("PartType")
                                         if customizeable: # if customizeable get all parts, otherwise get default. Then get their sockets
                                                 for part in parts:
                                                         name = part.get("ItemRowName")
                                                         socket = part.get("PartSocket")
                                                         obtainable = self.get_obtainable(name)
                                                         default = part.get("PartType") == attachmentCategoryToIndex[attachmentCategory]
                                                         if name and (obtainable or default):
                                                             self.integralPartsSockets.update({name:socket})
                                                             self.partsToWeaponList[name].append(weapon)
                                                             for socket in part.get("PartAvailableSockets"):
                                                                     self.socketToPartsList[socket].append(name)
                                                                     if not (default and not obtainable):   # some parts are customizeable but have no obtainable alternatives so we treat them as integral
                                                                         # self.socketToCustomizeablePartsList[socket].append(name)
                                                                         stuff = []
                                                                         if socket in self.weaponToSocketToCustomizeablePartsList[weapon]:
                                                                             stuff = self.weaponToSocketToCustomizeablePartsList[weapon].get(socket)
                                                                         stuff.append(name)
                                                                         self.weaponToSocketToCustomizeablePartsList[weapon].update({socket:stuff})
                                                                             
                                         else:
                                                 for part in parts:
                                                         try:
                                                                 if part.get("PartType") == attachmentCategoryToIndex[attachmentCategory]:
                                                                         self.partsToWeaponList[part.get("ItemRowName")].append(weapon)
                                                                         for socket in part.get("PartAvailableSockets"):
                                                                                 self.socketToPartsList[socket].append(part.get("ItemRowName"))
                                                         except KeyError:
                                                                 print(weapon+" has no default "+attachmentCategory)

        with open(exportFolder+r"\FW\UI\MainMenu\Blueprints\Data\DT_WeaponCustomizationAttachmentsData.json") as f:
                self.attachments = json.load(f)
                
        with open(exportFolder+r"\WPN_Weapons\WPN_ConfigTool\Setup\WPN\DT_WPN_Config_Setup.json") as f: 
                setup = json.load(f)
                self.caliberToMD=defaultdict(list)
                for table in setup:
                        for k, v in table.get("Rows").items():
                                md = re.findall(r'MD[0-9]',v.get("Caliber"))
                                if md:
                                        self.caliberToMD[md[0]].append(k)

        self.stats={}                      
        with open(exportFolder+r"\FW\Weapons\Customizer\WeaponPartStatsData.json") as f:  
                stats = json.load(f)
                for table in stats:
                        for k, v in table.get("Rows").items():
                                self.stats.update({k:v})

        self.unlocks=defaultdict(dict)
        for root,dirs,files in os.walk(exportFolder+r"\FW\Weapons\Weapon_V2",topdown=True): # could be optimized with specific dirs through itertools but whatever
                for file in files:
                        if "WeaponPartUnlocks" in file:
                            with open(os.path.join(root,file)) as f:
                                stuff = json.load(f)
                                for table in stuff:
                                    for k, v in table.get("Rows").items():
                                        level = v.get("Level")
                                        xp = v.get("RequiredXP")
                                        for thing in v.get("UnlockedAttachments"):
                                            item = thing.get("RowName")
                                            self.unlocks[item].update({"Level":level})
                                            self.unlocks[item].update({"XP":xp})

    def run(self):
        for table in self.items:
            for k, v in table.get("Rows").items():
                    if v.get("Category") == "WepMod":
                            page_name = v.get("ItemName").get("LocalizedString")
                            page = self.site.client.pages[page_name]
                            valueInfo = self.get_value(self,v.get("ValueRow").get("RowName"))
                            if not valueInfo:
                                print(k+ " ("+page_name+") no value found, skipping")
                                continue
                            if k not in self.stats:
                                print(k+" ("+page_name+") no stats found, skipping")
                                continue
                            compatibility = self.get_compat(k)
                            if not compatibility: # item is not compatible with anything, useless
                                print(k+" ("+page_name+") not compatible with anything, skipping")
                                continue
                            locations = self.get_drops(page_name)
                            vendor = self.get_vendor(k)
                            if not locations and 'Not obtainable' in vendor: # item not obtainable, but maybe as a quest reward? Last chance...
                                if page_name not in self.questRewards:
                                    print(k+" ("+page_name+") not obtainable, skipping")
                                    continue
                            picture = ''
                            if compatibility[1] in ['Scope','Optic']:
                                picture = '[[File:'+page_name+' 1200p.png|thumb]]'
                            other = ''
                            if page_name in otherStatsDict:
                                other = '\n|other='+otherStatsDict[page_name]
                            page_text = WIKITEXT.format(
                                image= re.findall(r'\.(.*)',v['ItemIcon'].get("AssetPathName"))[0],
                                category=compatibility[2],
                                volume=v['Volume'],
                                weight=v['Weight'],
                                buyValue=valueInfo[0],
                                xp=valueInfo[2],
                                magCapacity=self.stats[k].get("MagazineCapacity"),
                                suppressed=self.stats[k].get("IsSuppressed"),
                                fov=self.stats[k].get("FOV"),
                                rof=self.stats[k].get("FireRate"),
                                stability=self.stats[k].get("Stability"),
                                accuracy=self.stats[k].get("Accuracy"),
                                recoilWristRel=self.stats[k].get("RecoilWristRelBuff"),
                                recoilArmRel=self.stats[k].get("RecoilArmRelBuff"),
                                stabilizeTimeBuff=self.stats[k].get("StabilizeTimeRelBuff"),
                                stabilizeScalarBuff=self.stats[k].get("StabilizeScalarRelBuff"),
                                reloadSpeed=self.stats[k].get("ReloadSpeed"),
                                adsSpeed=self.stats[k].get("ADSSpeed"),
                                damage=self.stats[k].get("Damage"),
                                other=other,
                                slot=compatibility[1],
                                level=self.unlocks[k].get("Level") or 0,
                                requiredXp=self.unlocks[k].get("XP") or 0,
                                internalTag=k,
                                description=v.get("ItemDescription").get("LocalizedString").replace(' Volume: {Volume} Weight: {Weight}',''),
                                picture=picture,
                                itemVendor=vendor,
                                weaponCompatibility=compatibility[0],
                                drops=locations
                            ).strip()
                            print("Saving "+page_name)
                            # print(page_text)
                            time.sleep(2) # this script actually takes 2-3 seconds per item so this is not necessary
                            page.save(page_text, summary=self.summary)

    @staticmethod
    def get_value(self,item):
        for table in self.values:
            for k, v in table.get("Rows").items():
                    if k==item:
                            output = []
                            output.append(str(v.get("Value")))
                            output.append(str(round((v.get("Value")/1.9512195122),0)))
                            output.append(str(v.get("ExtractionExperienceValue")))
                            return output
        print(item+" not found in values")
        return ['0','0','0']
                            
    def get_vendor(self,item):
            output = ""
            for vendor, wares in self.vendors.items():
                    for whatever in wares:
                            for ware in whatever:
                                    key = ware.get("Value").get("ItemRowHandle").get("RowName")
                                    quantity = str(ware.get("Value").get("Quantity"))
                                    rep = str(ware.get("Value").get("VendorLevel"))
                                    if key == item:
                                            output += "{{VendorStock|vendor="+vendor+"|quantity="+quantity+"|level="+rep+"}}\n"
            if output:
                    return output
            return "''Not obtainable through trading''"

    def get_drops(self, item):
        output = None
        with open("dropsByCrate.json") as f:  
                items = json.load(f)
                if item in items:
                    output = ''
                    for element in items[item]:
                        container = element.get("Container")
                        contType = element.get("ContainerType")
                        maps = re.sub(r'["\'\[\]]','',str(element.get("Locations")))
                        condition = element.get("Condition")
                        chance = element.get("Chance")
                        output += "{{ItemLocation | container = "+container
                        if contType:
                            output += " | containerType = "+contType
                        elif container == "Ground":
                            output += " | containerType = Ground"
                        else:
                            output += " | containerType = Crate"
                        output += " | maps = "+maps
                        if condition:
                            output += " | condition = "+condition
                        output += " | chance = "+str(chance)
                        output +="}}\n"
        if not output:
            return ''
        return output

    def get_obtainable(self,item):
        try:
            name = self.itemNames[item]
        except KeyError:
            return False
        locations = self.get_drops(name)
        if locations:
            return True
        else:
            vendor = self.get_vendor(item)
            if not 'Not obtainable' in vendor:
                return True
            elif name in self.questRewards:
                return True
        return False
    
    def get_compat(self, item):
        def get_part(item):
            for table in self.items:
                for row in table.get("Rows"):
                        if row == item:
                            locale = table.get("Rows")[row].get("ItemName").get("LocalizedString")
                            if not locale:
                                print(item+" NOT LOCALIZED!")
                                return item
                            return locale
            print(item+" NOT FOUND!")
            return item
        
        slotLocalization = {
            "S_BCG":"Receiver",
            "S_BLR":"Receiver",
            "S_BRL":"Barrel",
            "S_CHG":"Charging handle",
            "S_FMS":"Front sight",
            "S_PGR":"Grip",
            "S_RLS":"Rear sight",
            "S_STK":"Stock",
            "S_TRG":"Trigger",
            "S_UPP":"Upper assembly",
            "S_MAG":"Magazine",
            "S_HGD":"Handguard",
            "S_BLT":"Bolt",
            "S_GAS":"Gas Tube",
            "S_OPT":"Optic",
            "S_RES":"Rear sight",
            "S_SCP":"Scope",
            "S_MZD":"Muzzle Device",
            "S_FGR":"Foregrip",
            "S_FRS":"Front sight",
            "S_BPD3":"Bipod",
            "S_CHG_END":"Charging handle end",
            "S_HMR":"Hammer",
            "S_STK_FLD":"Stock",
            "S_STK_END":"Stock end",
            "S_BPD":"Bipod",
            "S_MGN":"Magnifier",
            "S_HDL":"Handle"
        }
        weaponLocalization = { # only weapons on the wiki (obtainable in-game) are listed
            "HRF02":"36M AntiTank",
            "PST03":"87 Target",
            "SHG05":"AA12",
            "RFL01":"AK",
            "SMG05":"APC9 Pro",
            "PST04":"C96",
            "RFL16":"G36",
            "PST10":"G-L 19",
            "HRF04":"GM6",
            "GRL01":"Grenade Launcher",
            "HMG01":"Painless",
            "SMG01":"Kriss Vector 45",
            "RFL23":"M16",
            "RFL12":"M4A1",
            "LMG03":"M60",
            "PST07":"M79 Sawed-off",
            "LMG01":"MG34",
            "HRF03":"NTW-20",
            "HRF05":"AT-43 MASS",
            "SMG06":"P90",
            "SMG03":"PM-9",
            "SMG07":"PP-19 Vityaz",
            "SMG02":"PPSH-41",
            "PST05":"R8",
            "LMG04":"RPD",
            "RFL01B":"RPK",
            "SHG01":"S12",
            "RFL15":"SA58",
            "LMG02":"SAW",
            "HRF01":"SCAR",
            "PST02":"SOG",
            "SMG08":"Spectre M4",
            "RFL20":"SVD",
            "RFL30":"TKB-0146",
            "SHG03":"USAS-12",
            "PST01":"USP",
            "SHG04":"VEPR-12",
            "PST06":"Viper",
            "RFL29":"VKS VYKHLOP",
            "SMG04":"WLT MPL",
            "GRL02":"XM25",
            "RFL19":"R11 RSASS",
            "SHG06":"CLAW",
            "SMG09":"PnP-2K",
            "RFL02":"VH-Ambi 2",
            "RFL05":"VIK-32L",
            "RFL10":"47 TYP",
            "LMG06":"LMG-P",
            "PST08":"Mateo Model J"
        }
        weaponCategories = {
            "PST":"Pistols",
            "RFL":"Rifles",
            "HRF":"Heavy rifles",
            "LMG":"Light machineguns",
            "HMG":"Heavy machineguns",
            "SHG":"Shotguns",
            "SMG":"Submachine guns",
            "GRL":"Grenade launchers"
        }
        weapons = set()
        slots = set()
        parts = defaultdict(list)
        cat3 = "Weapon attachments"
        found = False
        for table in self.attachments:
            for k, v in table.get("Rows").items():
                    for option in v.get("AttachmentTypeOptions"):
                            if option.get("ItemRowName") == item:
                                    found = True
                                    sockets = v.get("PossibleAttachSockets") # get sockets that this attachment can fit in
                                    for socket in sockets:
                                            if "S_PIC" in socket:
                                                slots.add("Picatinny attachment")
                                            else:
                                                slots.add(slotLocalization[socket])
                                            weaponWhiteList = []
                                            weaponBlackList = []
                                            if "S_MZD" == socket: # special logic for muzzle devices - they depend on caliber as dictated in BP_WPN_Config and DT_WPN_Config_Setup
                                                    md = re.findall(r'MD[0-9]',k)[0]
                                                    weaponWhiteList = self.caliberToMD.get(md)
                                            for part in self.socketToPartsList[socket]:
                                                    for weapon in self.partsToWeaponList[part]:
                                                            if socket in self.weaponToSocketToCustomizeablePartsList[weapon]:  # if a weapon uses this part AND this part is customizeable
                                                                    if part in self.weaponToSocketToCustomizeablePartsList[weapon][socket]:
                                                                        parts[weapon].append(part)
                                                            if not weaponWhiteList or weapon in weaponWhiteList:
                                                                    weapons.add(weapon)
        if not found and item in self.integralPartsSockets: # assume weapon part if it wasn't found as attachment but is still compatible
            for weapon in self.partsToWeaponList[item]:
                cat3 = "Weapon parts"
                parts[weapon].append(item)
                weapons.add(weapon)
                slots.add(slotLocalization[self.integralPartsSockets[item]])
        weaponCompat = None 
        if weapons:
                categories = defaultdict(list)
                for weapon in weapons: # we need a list of weapons that use this part, with speficic weapon parts if these are required
                        if weapon in weaponLocalization: # only show currently available weapons
                            if not weaponCompat: # init value when we know it's getting used
                                weaponCompat = "=== Compatible with: ===\n"
                            partsCompat = ""
                            if parts[weapon]:
                                partsCompat = "|parts="
                                for part in sorted(set(parts[weapon])):
                                    if part != item: # some parts fit on themselves somehow
                                        partsCompat += get_part(part) +", "
                                partsCompat = re.sub(r', $','',partsCompat)
                            for k, v in weaponCategories.items():
                                if k in weapon:
                                    categories[v].append("{{WeaponCompatibility|weapon="+weaponLocalization[weapon]+partsCompat+"}}\n")
                for category, array in sorted(categories.items()):
                    weaponCompat += "===="+ category+"====\n"
                    for template in sorted(array):
                        weaponCompat += template
        if not weaponCompat: # not compatible with anything, will be skipped
                return
        slot = ""
        if slots:
            slot = list(slots)[0]
            if len(slots)>1:
                print(item+" has too many slots!")
        return [weaponCompat,slot,cat3]


if __name__ == '__main__':
    Creator().run()
