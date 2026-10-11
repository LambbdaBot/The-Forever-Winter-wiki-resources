import string
import re
import os
import time
import json

# TODO
# FIX RECRUITS
# FIX NONE IN REWARDS
# FIX TRIAL BY EXTRACT 1 / DOWN TO THE LAST DROP 1-3
# FIX JERRYCAN

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

quests = {} 

with open(exportFolder+"\Blueprints\Data\ItemDetailsData.json") as f:
        items = json.load(f)

with open("itemLocalization.json") as f:
        itemLocalization = json.load(f)
        
for table in items:
        rows = table.get("Rows")
        for row in rows:
                if row not in itemLocalization:
                        itemLocalization.update({row:rows[row].get("ItemName").get("LocalizedString")})
        
for root,dirs,files in os.walk(exportFolder+'\FW\Quests\Active',topdown=True): 
                for file in files:
                        if 'DAQuest' not in file:
                                continue
                        with open(os.path.join(root,file), encoding='utf-8') as f:
                                data = json.load(f)
                                for row in data:
                                    props = row.get("Properties")
                                    if not props.get("QuestName"):
                                            print(file+ " no quest name")
                                            continue
                                    else:
                                            questName = props.get("QuestName").get("LocalizedString").lower()
                                    if not props.get("QuestText"):
                                            print(file+ " no quest text")
                                    else:
                                            description = props.get("QuestText").get("LocalizedString")
                                    
                                    tasks = props.get("Tasks")
                                    extractionRequired = 'No'
                                    squadContribution = 'No'
                                    persistProgress = 'No'
                                    taskTypes = set()
                                    objectives = ""
                                    taskType = ""
                                    for task in tasks:
                                            if task.get("Action") == 'EFWQuestTaskAction::Collect':
                                                    taskTypes.add('Collect')
                                            if task.get("Action") == 'EFWQuestTaskAction::Kill':
                                                    taskTypes.add('Kill')
                                            if task.get("Action") == 'EFWQuestTaskAction::Blueprint':
                                                    taskTypes.add('Other')
                                            if task.get("Action") == 'EFWQuestTaskAction::Survive':
                                                    taskTypes.add('Survive')
                                            if task.get("bExtractionRequired"):
                                                    extractionRequired = 'Yes'
                                            if task.get("bPersistAcrossSessions"):
                                                    persistProgress = 'Yes'
                                            if task.get("bSquadContribution"):
                                                    squadContribution = 'Yes'
                                            text = task.get("TaskText")
                                            if text.get("LocalizedString"):
                                                    objectives += "\n# "+text.get("LocalizedString")
                                            else:
                                                    print(file+" no objective text")
                                    if not taskTypes:
                                            taskType = 'Other'
                                    for task in taskTypes:
                                            taskType += task + ", "
                                    taskType = re.sub(r', $','',taskType)

                                    water = 0
                                    xp = 0
                                    creds = 0
                                    rep = {}
                                    reward = ""
                                    rewards = props.get("Rewards") or []
                                    if not rewards:
                                            print(file+" no rewards")
                                    for stuff in rewards:
                                            xp += stuff.get("EarnedXP")
                                            water += stuff.get("DaysOfWater")
                                            reputation = stuff.get("EarnedFactionRep")
                                            if reputation:
                                                    faction = reputation.get("FactionTag").get("TagName")
                                                    if 'Scavenger' in faction:
                                                            faction = 'Scavenger'
                                                    elif faction == 'Scope.Faction.Euruska':
                                                            faction = 'Euruska'
                                                    elif faction == 'Scope.Faction.Europa':
                                                            faction = 'Europa'
                                                    elif faction == 'Scope.Faction.Eurasia':
                                                            faction = 'Eurasia'
                                                    else:
                                                            if faction != 'None':
                                                                    print(faction+ ' unknown faction')
                                                            faction = None
                                                    repAmount = reputation.get("EarnedRep")
                                                    if faction:
                                                            rep.update({faction:repAmount})
                                            item = stuff.get("RewardItemRowHandle").get("RowName")
                                            if item in itemLocalization:
                                                    item = itemLocalization[item]
                                            amount = stuff.get("ItemCount")
                                            if item != 'Credits':
                                                    reward += "\n{{QuestReward|item="+item+"|quantity="+str(int(amount))+"}}"
                                            else:
                                                    creds += amount
                                    if creds:
                                            reward += "\n{{QuestReward|item=Credits|quantity="+str(int(creds))+"}}"
                                    if xp:
                                            reward += "\n{{QuestReward|item=XP|quantity="+str(int(xp))+"}}"
                                    if water:
                                            reward += "\n{{QuestReward|item=Water|quantity="+str(int(water))+"}}"
                                    if rep:
                                            for faction in rep:
                                                    reward += "\n{{QuestReward|item="+faction+" Faction Rating|quantity="+str(int(rep[faction]))+"}}"

                                    author = "Slade"
                                    acceptDialogue = ""
                                    completeDialogue = ""
                                    if not props.get("StartDialogue"):
                                            print(file+" no start dialogue")
                                    else:
                                            startDialogueRef = props.get("StartDialogue").get("ObjectPath").replace("/Game",'').replace("/","\\")
                                            startDialogueRef = re.sub(r'\.[0-9]','.json', startDialogueRef)
                                            with open(exportFolder + startDialogueRef, encoding='utf-8') as g:
                                                    d2 = json.load(g)
                                                    for r2 in d2:
                                                            if 'WBP' not in r2.get("Type"):
                                                                    continue
                                                            p2 = r2.get("Properties")
                                                            if p2.get("Quest Giver Name"):
                                                                    author = p2.get("Quest Giver Name").get("LocalizedString")
                                                            text = p2.get("DialogueText")
                                                            for line in text:
                                                                    if not line.get("LocalizedString"):
                                                                            print(file+" fucked up quest lines")
                                                                    else:
                                                                            acceptDialogue+="\n"+line.get("LocalizedString")+"\n"
                                    if not props.get("PreRewardDialogue"):
                                            print(file+" no end dialogue")
                                    else:
                                            endDialogueRef = props.get("PreRewardDialogue").get("ObjectPath").replace("/Game",'').replace("/","\\")
                                            endDialogueRef = re.sub(r'\.[0-9]','.json', endDialogueRef)
                                            with open(exportFolder + endDialogueRef, encoding='utf-8') as g:
                                                    d2 = json.load(g)
                                                    for r2 in d2:
                                                            if 'WBP' not in r2.get("Type"):
                                                                    continue
                                                            p2 = r2.get("Properties")
                                                            text = p2.get("DialogueText")
                                                            for line in text:
                                                                    if not line.get("LocalizedString"):
                                                                            print(file+" fucked up quest lines")
                                                                    else:
                                                                            completeDialogue+="\n"+line.get("LocalizedString")+"\n"
                                    endRow = {}
                                    endRow.update({"taskType":taskType})
                                    endRow.update({"persistProgress":persistProgress})
                                    endRow.update({"squadContribution":squadContribution})
                                    endRow.update({"extractionRequired":extractionRequired})
                                    endRow.update({"description":description})
                                    endRow.update({"objectives":objectives})
                                    endRow.update({"reward":reward})
                                    endRow.update({"acceptDialogue":acceptDialogue})
                                    endRow.update({"completeDialogue":completeDialogue})
                                    endRow.update({"author":author})
                                    quests.update({questName:endRow})

with open("quests.json", "w") as outfile:
        json.dump(quests, outfile, indent=4)
