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
Get basic info for all items. Likely outdated after changes to values
"""

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

def getFile(name):
        for root,dirs,files in os.walk(exportFolder,topdown=True): # could be optimized with specific dirs through itertools but whatever
                for file in files:
                        if (file == name):
                                return os.path.join(root,file)
        return

#get detailsdata tables
items=defaultdict(dict)
with open(exportFolder+"\Blueprints\Data\ItemDetailsData.json") as f:
        itemData = json.load(f)
with open(exportFolder+"\Blueprints\Data\DanglyDetailsData.json") as f: # merging all data tables
        itemData += json.load(f)
with open(exportFolder+"\Blueprints\Data\QuestItemDetailsData.json") as f: 
        itemData += json.load(f)
with open(exportFolder+"\Blueprints\Data\WeaponsDetailsData.json") as f: 
        itemData += json.load(f)

rowToTag = dict()
with open(exportFolder+"\Blueprints\Data\DataReference\DT_TagToRowHandle.json") as f:  #ForeverWinter/Content/Blueprints/Data/DataReference/DT_TagToRowHandle.uasset
        data = json.load(f)
        for table in data:
                rows = table.get("Rows")
                for tag, info in rows.items():
                        if not info.get("DataRow") or not info.get("DataRow").get("RowName"):
                                print("row error "+tag)
                                continue
                        rowName = re.sub(r'_C$','',info.get("DataRow").get("RowName"))
                        rowToTag.update({rowName:tag})

#get value override tables
valueData={}
for root,dirs,files in os.walk(exportFolder+r"\Blueprints\Data\Value\\",topdown=True): 
        for file in files:
                with open(os.path.join(root,file), encoding='utf-8') as f:
                        stuff = json.load(f)
                        for table in stuff:
                                rows = table.get("Rows")
                                valueData = valueData | rows

itemLocalization = {}
with open("itemLocalization.json") as f: # wiki names for items
        itemLocalization = json.load(f)
        
for table in itemData:
        rows = table.get("Rows")
        for item, data in rows.items():
                name = None
                if item in itemLocalization:
                        name = itemLocalization[item]
                elif data.get("ItemName"):
                        name = data.get("ItemName").get("LocalizedString")
                elif data.get("DanglyName"):
                        if data.get("DanglyName").get("LocalizedString"):
                                name = data.get("DanglyName").get("LocalizedString")
                        elif data.get("DanglyName").get("CultureInvariantString"):
                                name = data.get("DanglyName").get("CultureInvariantString")
                if name:
                        if name in items:
                                print("dupe! "+item+"/"+name)
                                continue
                        value = None
                        xp = None
                        valueRow = data.get("ValueRow")
                        if valueRow:
                                rowName = data.get("ValueRow").get("RowName")
                                if rowName in valueData:
                                        value = valueData.get(rowName).get("Value")
                                        xp = valueData.get(rowName).get("ExtractionExperienceValue")
                                else:
                                        print("not in value data: "+rowName+"/"+item)
                        else:
                                value = data.get("Value")
                        volume = data.get("Volume")
                        weight = data.get("Weight")
                        description = None
                        if data.get("ItemDescription"):
                                if data.get("ItemDescription").get("LocalizedString"):
                                        description = data.get("ItemDescription").get("LocalizedString").replace(" Volume: {Volume} Weight: {Weight}","")
                                else:
                                        print("no localized string "+item)
                        elif data.get("DanglyDescription"):
                                if data.get("DanglyDescription").get("LocalizedString"):
                                        description = data.get("DanglyDescription").get("LocalizedString")
                                else:
                                        print("no localized string "+item)
                        else:
                                print("no description "+item)
                        items[name].update({"description":description})
                        items[name].update({"volume":volume})
                        items[name].update({"weight":weight})
                        items[name].update({"value":value})
                        items[name].update({"xp":xp})
                        items[name].update({"id":item})
                        if item in rowToTag:
                                items[name].update({"tag":rowToTag[item]})
                        else:
                                print("NO TAG "+item)
                                items[name].update({"tag":"?"})
                else:
                        print("no name bruh "+item)
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

with open("items.json", "w") as outfile:
        json.dump(items, outfile, indent=4)
        
