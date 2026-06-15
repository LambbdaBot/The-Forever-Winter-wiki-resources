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
Creates page stubs for the whole new tutorial questline.

Requirements:
        - itemLocalization.json - for rewards, provided in Gather data
        - quests.json - generated using Gather data\Get quest info (lambbda).py
        - extracting data tables in \Blueprints\Data\ and subfolders
        - extracting quest data in \FW\Quests\
        Just extract everything to be safe.
"""

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

WIKITEXT = """{{{{InfoboxQuest
  | image = {questName} quest thumbnail.png
  | faction = [[Scavengers]]
  | location = Any
  | taskType = {taskType}
  | extractionRequired = {extractionRequired}
  | squadContribution = {squadContribution}
  | persistProgress = {persistProgress}
  | objectives = {objectives}
  | questline = Tutorial
  | questlineStep = 1
  | replayable = 0
}}}}

== Description ==
{description}

== Objectives ==
{{{{Objectives}}}}

== Rewards =={reward}

== Dialogue ==
When accepting the quest:
{{{{Quote
  | text = {acceptDialogue}
  | author = {author}
}}}}

When turning in the quest:
{{{{Quote
  | text = {completeDialogue}
  | author = {author}
}}}}

== Guide ==
"""

class Creator:
    summary = 'Automatically creating quest page stubs'

    def __init__(self):
        credentials = AuthCredentials(user_file="me")
        # the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
        # test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
        # so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
        # then change it to your wiki afterwards
        self.site = WikiggClient('test', credentials=credentials)
        self.itemNames = {}
        self.quests = {}
        
        with open(exportFolder+"\Blueprints\Data\ItemDetailsData.json") as f:
                self.items = json.load(f)

        with open("itemLocalization.json") as f:
                itemLocalization = json.load(f)
                
        for table in self.items:
                rows = table.get("Rows")
                for row in rows:
                        if row not in itemLocalization:
                                itemLocalization.update({row:rows[row].get("ItemName").get("LocalizedString")})

        banned = ['Defy & Deny','Teach the Innards','Onward & Outward']
        for root,dirs,files in os.walk(exportFolder+'\FW\Quests\Active\MainQuests',topdown=True):   
                for file in files:
                        with open(os.path.join(root,file), encoding='utf-8') as f:
                                data = json.load(f)
                                for row in data:
                                    props = row.get("Properties")
                                    questName = props.get("QuestName").get("LocalizedString")
                                    if questName in banned:
                                            continue
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
                                            objectives += "\n# "+text.get("LocalizedString")
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
                                    rewards = props.get("Rewards")
                                    for stuff in rewards:
                                            xp += stuff.get("EarnedXP")
                                            water += stuff.get("DaysOfWater")
                                            reputation = stuff.get("EarnedFactionRep")
                                            if reputation:
                                                    faction = reputation.get("FactionTag").get("TagName")
                                                    if 'Scavenger' in faction:
                                                            faction = 'Scavenger'
                                                    else:
                                                            if faction != 'None':
                                                                    print(faction+ ' IDK')
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
                                    startDialogueRef = props.get("StartDialogue").get("ObjectPath").replace("/Game",'').replace(".1",".json").replace("/","\\")
                                    endDialogueRef = props.get("PreRewardDialogue").get("ObjectPath").replace("/Game",'').replace(".1",".json").replace("/","\\")
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
                                                            acceptDialogue+="\n"+line.get("LocalizedString")+"\n"
                                    with open(exportFolder + endDialogueRef, encoding='utf-8') as g:
                                            d2 = json.load(g)
                                            for r2 in d2:
                                                    if 'WBP' not in r2.get("Type"):
                                                            continue
                                                    p2 = r2.get("Properties")
                                                    text = p2.get("DialogueText")
                                                    for line in text:
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
                                    self.quests.update({questName:endRow})
                            
    def run(self):
        for quest, data in self.quests.items():  
            page = self.site.client.pages[quest]
            page_text = WIKITEXT.format(
                questName = quest,
                taskType = data["taskType"],
                persistProgress = data["persistProgress"],
                squadContribution = data["squadContribution"],
                extractionRequired = data["extractionRequired"],
                description = data["description"],
                objectives = data["objectives"],
                reward = data["reward"],
                acceptDialogue = data["acceptDialogue"],
                completeDialogue = data["completeDialogue"],
                author = data["author"]
            ).strip()
            #print(quest)
            #print(page_text)
            time.sleep(2) # this script actually takes 2-3 seconds per item so this is not necessary
            page.save(page_text, summary=self.summary)

if __name__ == '__main__':
    Creator().run()
