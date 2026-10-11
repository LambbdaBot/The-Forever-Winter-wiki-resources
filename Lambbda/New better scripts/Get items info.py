import json
import re
import helpers

# List of items that provoke HKs, likely outdated
hkItems = set()
hkData = helpers.getFile("/Content/FW/AI/Spawners/SpawnController/BP_SpawnController_HunterKillers.0")
for stuff in hkData["TestData"]:
    items = stuff.get("Items")
    if items:
        for item in items:
            hkItems.add(item["ItemName"])

headshotMults = {}
with open(helpers.exportFolder + r"/Content/FW/Weapons/Weapon_V2/DT_CaliberToHeadshotMulti.json") as f:
    stuff = json.load(f)
    for thing in stuff:
        rows = thing.get("Rows")
        for row in rows:
            headshotMults.update({row: rows[row].get("HeadshotMulti_2_9B53E75048FB0CC727824C8EFEF643F0")})

with open(helpers.exportFolder + r"/Content/Blueprints/Data/DataReference/DT_TagToRowHandle.json") as f:
    tagsData = json.load(f)

output = {}

for tag, reference in tagsData[0]["Rows"].items():
    newRow = {}
    newRow.update({"Tag": tag})

    handle = reference["DataRow"]["RowName"]
    table = reference["DataRow"]["DataTable"]["ObjectPath"]
    tableName = re.sub(r"DataTable|'", "", reference["DataRow"]["DataTable"]["ObjectName"])
    if tableName not in output:
        output.update({tableName: {}})
    itemData = helpers.getFile(table)[handle]
    name = "UNKNOWN ITEM"
    description = None
    icon = None
    for field in itemData:
        # each detailsData table has a custom field for item name, generally the first thing with a "Name" in it works
        if "Name" in field:
            if "CultureInvariantString" in itemData[field]:
                name = itemData[field]["CultureInvariantString"]
            if "LocalizedString" in itemData[field]:
                name = itemData[field]["LocalizedString"]
        if "Description" in field:
            if "CultureInvariantString" in itemData[field]:
                description = itemData[field]["CultureInvariantString"]
            if "LocalizedString" in itemData[field]:
                description = itemData[field]["LocalizedString"]
        if re.findall("Icon$", field) and itemData[field]["AssetPathName"] != '':
            icon = re.findall(r"\.(.*)$", itemData[field]["AssetPathName"])[0]
    if description:
        description = description.replace(" Volume: {Volume} Weight: {Weight}", "")
    newRow.update({"GameName": name})
    if tag in helpers.wikiLocalization:
        name = helpers.wikiLocalization[tag]
    newRow.update({"Name": name})
    newRow.update({"RowName": handle})
    newRow.update({"Description": description})
    newRow.update({"Icon": icon})
    newRow.update({"Weight": itemData.get("Weight")})
    newRow.update({"Volume": itemData.get("Volume")})
    newRow.update({"Durability": itemData.get("Durability")})
    newRow.update({"Stack": itemData.get("MaxStack")})
    newRow.update({"Category": itemData.get("Category")})
    newRow.update({"HK": handle in hkItems})

    value = None
    xp = None
    if "ValueRow" in itemData and itemData["ValueRow"]["RowName"] != "None":
        handle = itemData["ValueRow"]["RowName"]
        table = itemData["ValueRow"]["DataTable"]["ObjectPath"]
        valueData = helpers.getFile(table)[handle]
        value = valueData["Value"]
        xp = valueData["ExtractionExperienceValue"]
    else:
        value = itemData.get("Value")
    newRow.update({"XP": xp})
    newRow.update({"Value": value})

    if "DataAsset" in itemData and itemData["DataAsset"]["AssetPathName"] != '':
        dataAsset = helpers.getFile(itemData["DataAsset"]["AssetPathName"])
        weaponRow = {}

        weaponRow.update({"FireRate": 1 / (dataAsset.get("FireRate") or 1)})
        weaponRow.update({"BurstFireRate": 1 / (dataAsset.get("BurstFireRate") or 1)})
        weaponRow.update({"WeaponDamage": dataAsset.get("WeaponDamage")})
        weaponRow.update({"NumberOfBuckshots": dataAsset.get("NumberOfBuckshots")})
        if "AmmoTypeCaliber" in dataAsset:
            ammoTag = dataAsset["AmmoTypeCaliber"]["TagName"]
            if ammoTag in headshotMults:
                weaponRow.update({"HeadshotMult": headshotMults[ammoTag]})
            else:
                weaponRow.update({"HeadshotMult": 1})

        newRow.update({"WeaponData": weaponRow})

    # for ease of access use wiki names as ids, and use wikiLocalization file to deduplicate
    if name in output[tableName]:
        print("duplicate name " + name + " in " + tableName)
    output[tableName].update({name: newRow})

with open("items.json", "w") as outfile:
    json.dump(output, outfile, indent=4)
