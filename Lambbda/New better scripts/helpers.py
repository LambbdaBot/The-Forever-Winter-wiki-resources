import json
import re

exportFolder = r'E:/Program Files/FModel/Output/Exports/ForeverWinter'

# optional file with in-game-to-wiki names translation
try:
    with open("wikiLocalization.json") as f:
        wikiLocalization = json.load(f)
except FileNotFoundError:
    wikiLocalization = {}

factionTags = {}
with open(
        exportFolder + r"/Content/FW/UI/MainMenu/UMG/Buttons/FactionScopeToName/DT_FactionScopeToFactionName.json") as f:
    factions = json.load(f)[0]["Rows"].values()
    for faction in factions:
        factionTags.update({faction["FactionScope_3_DF9E8BA14509C109498B98B0303D644A"]["TagName"]:
                                faction["FactionName_6_94D24EFB480EA07AC851A7B7AF8AA8BD"]["LocalizedString"]})

def getFile(path):
    subPath = re.findall(r'\.(.*)$', path)
    arrayIndex = None
    arrayName = None

    if subPath and subPath[0].isdigit():
        arrayIndex = int(subPath[0])
    elif subPath:
        arrayName = subPath[0]
    else:
        arrayIndex = 0
    with open(exportFolder + re.sub(r'\.(.*)$', '.json', path).replace("/Game", "/Content")) as f:
        stuff = json.load(f)
        if arrayIndex is not None:
            stuff = stuff[arrayIndex]
        elif arrayName:
            for thing in stuff:
                if thing.get("Name") == arrayName:
                    stuff = thing
                    break
        if "ClassDefaultObject" in stuff:
            return getFile(stuff["ClassDefaultObject"]["ObjectPath"])
        if stuff.get("Type") == "DataTable":
            return stuff["Rows"]
        else:
            return stuff["Properties"]

def getItem(itemHandle, tablePath):
    if itemHandle == "TestCurrency":
        return "Credits"
    itemData = getFile(tablePath)[itemHandle]
    for field in itemData:
        # each detailsData table has a custom field for item name, generally the first thing with a "Name" in it works
        if "Name" in field:
            if "CultureInvariantString" in itemData[field]:
                return itemData[field]["CultureInvariantString"]
            if "LocalizedString" in itemData[field]:
                return itemData[field]["LocalizedString"]
    print("Unknown item " + itemHandle)
    return "UNKNOWN"
