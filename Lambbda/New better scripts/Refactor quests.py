import json
import re
import time

from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwcleric.page_modifier import PageModifierBase

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('theforeverwinter', credentials=credentials)
summary = 'Migrating quests to new format'

# see "Get quest info.py" for how to form this file
with open("quests.json") as f:
    quests = json.load(f)

allowHidden = True


class PageModifier(PageModifierBase):
    def update_plaintext(self, text):
        backup = text
        name = self.current_page.name
        if self.current_page.namespace != 0:
            # don't do anything outside the main namespace
            # for example, we don't want to modify template documentation or user sandboxes
            return backup
        if not allowHidden:
            if name not in quests:
                print("QUEST NOT FOUND: " + name)
                return backup
            data = quests[name]
        else:
            if name in quests:
                data = quests[name]
            elif "HIDDEN " + name in quests:
                data = quests["HIDDEN " + name]
            else:
                print("QUEST NOT FOUND: " + name)
                return backup

        lead = "\n'''{{PAGENAME}}''' is a [[Quests|quest]] in '''{{Gamename}}'''."
        questline = re.findall(r"questline ?= ?(.*)", text)
        if questline:
            lead += " It is part of the '''" + questline[0] + "''' questline."
        oldBox = re.findall(r"{{ ?InfoboxQuest[\s\S]*?}}", text)[0]
        oldBox = oldBox.replace("InfoboxQuest", "Infobox Quest")
        oldBox = re.sub(r"\| ?objectives=[\s\S]*?\n[\s]*\|", "\n|", oldBox)
        oldBox = re.sub(
            r"[\s]*\| ?taskType.*\n|[\s]*\| ?extractionRequired.*\n|[\s]*\| ?squadContribution.*\n|[\s]*\| ?persistProgress.*\n|[\s]*\| ?related.*",
            "", oldBox)
        oldBox = re.sub(r"\n\| ?", "\n  | ", oldBox)
        oldBox = re.sub(r"(?<=[^\s])=(?=[^\s])", " = ", oldBox)
        oldBox = oldBox.replace("image =", "Image =")
        oldBox = oldBox.replace("faction =", "Faction =")
        oldBox = oldBox.replace("location =", "Location =")
        oldBox = oldBox.replace("questline =", "Questline =")
        oldBox = oldBox.replace("questlineStep =", "QuestlineStep =")
        oldBox = oldBox.replace("replayable =", "Replayable =")
        text = re.sub(r"{{ ?InfoboxQuest[\s\S]*?}}", oldBox + lead, text)
        text = text.replace("[[Category:Quests]]", "")

        # replacing objectives
        objectives = ""
        for objective in data["Objectives"]:
            objectives += "{{Quest Objective"
            objectives += "\n  | Text = " + objective["Text"]
            objectives += "\n  | Type = " + objective["Type"]
            if "Object" in objective:
                objectives += "\n  | Object = " + objective["Object"]
                objectives += "\n  | Amount = " + str(objective["Amount"])
            objectives += "\n  | Extraction = " + str(int(objective["Extraction"]))
            objectives += "\n  | Persist = " + str(int(objective["Persist"]))
            objectives += "\n  | Squad = " + str(int(objective["Squad"]))
            objectives += "\n}}\n"
        text = text.replace("{{Objectives}}\n", objectives)
        if re.findall(r"{{ ?Objectives ?}}", text):
            print("error replacing objectives in " + name)

        # replacing rewards
        rewards = "{{Quest Rewards |"
        for reward in data["Rewards"]:
            rewards += "\n  " + str(reward["Amount"]) + " " + reward["Object"] + ","
        rewards = re.sub(r",$", "", rewards)
        rewards += "\n}}"
        text = text.replace(re.findall(r"{{ ?QuestReward.*}}", text)[0], "$$$$")
        text = re.sub(r"{{ ?QuestReward.*}}\n", "", text)
        text = text.replace("$$$$", rewards)
        if re.findall(r"{{ ?QuestReward", text):
            print("error replacing rewards in " + name)

        # print("Saving " + name)
        # print(text)
        time.sleep(5)
        return text


PageModifier(site, page_list=site.pages_using('InfoboxQuest'),
             summary=summary).run()
