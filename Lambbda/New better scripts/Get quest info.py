import json
import re
import helpers

factionTags = {}
with open(
        helpers.exportFolder + r"/Content/FW/UI/MainMenu/UMG/Buttons/FactionScopeToName/DT_FactionScopeToFactionName.json") as f:
    factions = json.load(f)[0]["Rows"].values()
    for faction in factions:
        factionTags.update({faction["FactionScope_3_DF9E8BA14509C109498B98B0303D644A"]["TagName"]:
                                faction["FactionName_6_94D24EFB480EA07AC851A7B7AF8AA8BD"]["LocalizedString"]})


def getFile(path):
    arrayIndex = int(re.findall(r'\.([0-9]*)$', path)[0]) or 0
    with open(helpers.exportFolder + re.sub(r'\.[0-9]*$', '.json', path).replace("/Game", "/Content")) as f:
        stuff = json.load(f)[arrayIndex]
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


def parseData(questData):
    for quest in questData[0]["Rows"].values():
        questId = str(quest["QuestID"])

        newRow = {}
        newRow.update({"Giver": quest["QuestGiver"].replace("EQuestGiver::", "")})
        newRow.update({"ID": quest["QuestID"]})

        questData = getFile(quest["QuestDataAsset"]["ObjectPath"])
        questName = questData["QuestName"]["LocalizedString"]

        if quest["bHideInGame"]:
            questName = "HIDDEN " + questName

        newRow.update({"Tag": questData["QuestTag"]["TagName"]})
        description = ""
        try:
            description = questData["QuestText"]["LocalizedString"]
        except KeyError:
            print("Quest " + questId + " (" + questName + ") no description")
        newRow.update({"Description": description})

        startDialogue = ""
        try:
            dialogue = getFile(questData["StartDialogue"]["ObjectPath"])
            lines = dialogue["DialogueText"]
            for line in lines:
                startDialogue = startDialogue + line["LocalizedString"] + "\n"
            startDialogue = re.sub(r"\n$", "", startDialogue)
            try:
                newRow.update({"Author": dialogue["Quest Giver Name"]["LocalizedString"]})
            except KeyError:
                print("Quest " + questId + " (" + questName + ") no dialogue author, using Slade by default")
                newRow.update({"Author": "Slade"})

        except KeyError:
            print("Quest " + questId + " (" + questName + ") no start dialogue")
        newRow.update({"StartDialogue": startDialogue})

        endDialogue = ""
        try:
            lines = getFile(questData["StartDialogue"]["ObjectPath"])["DialogueText"]
            for line in lines:
                endDialogue = endDialogue + line["LocalizedString"] + "\n"
            endDialogue = re.sub(r"\n$", "", endDialogue)
        except KeyError:
            print("Quest " + questId + " (" + questName + ") no end dialogue")
        newRow.update({"EndDialogue": endDialogue})

        newRow.update({"Objectives": []})
        newRow.update({"Rewards": []})

        for task in questData["Tasks"]:
            newTask = {}
            newTask.update({"Type": task["Action"].replace("EFWQuestTaskAction::", "")})
            if newTask["Type"] == "Blueprint":
                newTask["Type"] = "Other"
            if "LocalizedString" in task["TaskText"]:
                newTask.update({"Text": task["TaskText"]["LocalizedString"]})
            if "CultureInvariantString" in task["TaskText"]:
                newTask.update({"Text": task["TaskText"]["CultureInvariantString"]})
            newTask.update({"Amount": task["CompletionCount"]})

            if "CollectItemRowHandle" in task and task["CollectItemRowHandle"]["RowName"] != "None":
                itemName = getItem(task["CollectItemRowHandle"]["RowName"],
                                   task["CollectItemRowHandle"]["DataTable"]["ObjectPath"])
                if itemName in helpers.wikiLocalization:
                    itemName = helpers.wikiLocalization[itemName]
                newTask.update({"Object": itemName})

            newTask.update({"Extraction": task["bExtractionRequired"] or False})
            newTask.update({"Persist": task["bPersistAcrossSessions"] or False})
            newTask.update({"Squad": task["bSquadContribution"] or False})

            newRow["Objectives"].append(newTask)

        if "Rewards" not in questData:
            print("Quest " + questId + " (" + questName + ") no rewards")
        else:
            for reward in questData["Rewards"]:
                if "RewardItemRowHandle" in reward and reward["RewardItemRowHandle"]["RowName"] != "None":
                    newReward = {}
                    table = reward["RewardItemRowHandle"]["DataTable"]
                    if table:
                        table = table["ObjectPath"]
                    itemName = getItem(reward["RewardItemRowHandle"]["RowName"],
                                       table)
                    if itemName == "UNKNOWN":
                        print(questId + " " + questName)
                    if itemName in helpers.wikiLocalization:
                        itemName = helpers.wikiLocalization[itemName]
                    newReward.update({"Object": itemName})
                    newReward.update({"Amount": reward["ItemCount"]})
                    newRow["Rewards"].append(newReward)

                if "EarnedXP" in reward and reward["EarnedXP"] > 0:
                    newReward = {"Object": "XP", "Amount": reward["EarnedXP"]}
                    newRow["Rewards"].append(newReward)

                if "DaysOfWater" in reward and reward["DaysOfWater"] > 0:
                    newReward = {"Object": "Water", "Amount": reward["DaysOfWater"]}
                    newRow["Rewards"].append(newReward)

                if "EarnedFactionRep" in reward and reward["EarnedFactionRep"]["EarnedRep"] > 0:
                    newReward = {}
                    newReward.update(
                        {"Object": factionTags[
                                       reward["EarnedFactionRep"]["FactionTag"]["TagName"]] + " faction rating"})
                    newReward.update({"Amount": reward["EarnedFactionRep"]["EarnedRep"]})
                    newRow["Rewards"].append(newReward)

        # moving Water, Credits, XP and faction rep to the bottom
        movingRewards = []
        for reward in newRow["Rewards"]:
            if reward["Object"] == "Water":
                movingRewards.append(reward)
        for reward in newRow["Rewards"]:
            if reward["Object"] == "Credits":
                movingRewards.append(reward)
        for reward in newRow["Rewards"]:
            if reward["Object"] == "XP":
                movingRewards.append(reward)
        for reward in newRow["Rewards"]:
            if "faction rating" in reward["Object"]:
                movingRewards.append(reward)
        for toMove in movingRewards:
            # remove from list
            newRow["Rewards"] = [reward for reward in newRow["Rewards"] if reward.get("Object") != toMove.get("Object")]
        newRow["Rewards"] += movingRewards

        if questName in output:
            print(questName + " - duplicate quest (old ID " + str(output[questName]["ID"]) + ", new ID " + str(
                newRow["ID"]) + ")")

        output.update({questName: newRow})


with open(helpers.exportFolder + r"/Content/FW/Quests/DT_QuestData.json") as f:
    questData = json.load(f)

output = {}

parseData(questData)

with open(helpers.exportFolder + r"/Content/FW/Quests/DT_QuestData_SideQuests.json") as f:
    questData = json.load(f)

parseData(questData)

with open("quests.json", "w") as outfile:
    json.dump(output, outfile, indent=4)
