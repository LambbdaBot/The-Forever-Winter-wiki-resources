import json
import string
import re
import os
import time
import collections
from collections import defaultdict

"""
For every item, lists vendors that sell it.

Requirements:
        - Run Gather data\Get item data.py to create items.json
        - Extract data tables in \Blueprints\Data\ and \FW\WorldVendors\RootObjects\
"""

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

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

vendors = {}
with open(exportFolder+"\Blueprints\Data\VendorDataTable.json") as f:
        vendorData = json.load(f)
        for table in vendorData:
                rows = table.get("Rows")
                vendors.update({"Luca":get_stock(rows.get("WesternWeaponVendor"))})
                vendors.update({"Kane":get_stock(rows.get("EasternWeaponVendor"))})
                vendors.update({"Heisenburg":get_stock(rows.get("MedicalVendor"))})
                vendors.update({"Bundleton":get_stock(rows.get("RigVendor_V2"))})
                vendors.update({"Slade":get_stock(rows.get("RecruitVendor"))})
                vendors.update({"Bunco":get_stock(rows.get("ScavSurplusVendor"))})
                
with open(exportFolder+"\FW\WorldVendors\RootObjects\VendorDataTable_InWorldVendors.json") as f:  # ForeverWinter/Content/FW/WorldVendors/RootObjects/VendorDataTable_InWorldVendors.uasset
        vendorData = json.load(f)
        for table in vendorData:
                rows = table.get("Rows")
                stock = []
                for row, wares in rows.items():
                        if row != "InWorld_RNGVendor_TableMASTER_DONOTASSIGN":
                                stock += get_stock(wares)
                vendors.update({"Auto-Vendor":stock})

items = {}
with open("items.json") as f:
        items = json.load(f)
        
itemNames = {}
for item, data in items.items():
        rowHandle = data.get("id")
        itemNames.update({rowHandle:item})
                
itemToVendors = defaultdict(list)
for vendor, wares in vendors.items():
    for whatever in wares:
            for ware in whatever:
                    output = ""
                    key = ware.get("Value").get("ItemRowHandle").get("RowName")
                    quantity = str(ware.get("Value").get("Quantity"))
                    rep = str(ware.get("Value").get("VendorLevel"))
                    output += "{{VendorStock|vendor="+vendor+"|quantity="+quantity+"|level="+rep+"}}"
                    if key in itemNames:
                        if output not in itemToVendors[itemNames[key]]:
                                itemToVendors[itemNames[key]].append(output)
                    else:
                        print("item "+key+" for vendor "+vendor+" not localized")
                        if output not in itemToVendors[key]:
                                itemToVendors[key].append(output)
stuff = """
== Acquisition ==
=== Trading ===

=== Looting ===
{{ItemLoot}}
=== Quests ===
{{QuestRewards}}
"""
with open("vendors.json", "w") as outfile:
        json.dump(itemToVendors, outfile, indent=4)
