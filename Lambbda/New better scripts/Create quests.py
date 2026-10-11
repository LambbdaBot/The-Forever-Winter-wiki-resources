import json
import re
import time

from mwcleric import AuthCredentials
from mwcleric import WikiggClient

exportFolder = 'E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

Template = """{{{{Infobox Quest
  | Image = {questName} quest thumbnail.png
  | Faction = [[{faction}]]
  | Location = Any
  | Replayable = 1
}}}}
'''{{PAGENAME}}''' is a [[Quests|quest]] in '''{{Gamename}}'''.

== Description ==
{description}

== Objectives ==
{objectives}

== Rewards ==
{rewards}

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

with open("quests.json") as f:
    quests = json.load(f)

whitelist = [
    "HIDDEN Dr quest 4",
    "HIDDEN Dr quest 3",
    "HIDDEN Dr quest 2",
    "HIDDEN Dr quest 1",
    "HIDDEN TBD Side Quest for Trans Tower"
]


class Creator:
    summary = 'Automatically creating quest page stubs'

    def __init__(self):
        credentials = AuthCredentials(user_file="me")
        self.site = WikiggClient('theforeverwinter', credentials=credentials)

    def run(self):
        for quest, data in quests.items():
            if quest not in whitelist:
                continue
            page = self.site.client.pages[quest]

            objectives = ""
            for objective in data["Objectives"]:
                objectives += "{{Quest Objective"
                objectives += "\n  | Text = " + str(objective.get("Text"))
                objectives += "\n  | Type = " + objective["Type"]
                if "Object" in objective:
                    objectives += "\n  | Object = " + objective["Object"]
                    objectives += "\n  | Amount = " + str(objective["Amount"])
                objectives += "\n  | Extraction = " + str(int(objective["Extraction"]))
                objectives += "\n  | Persist = " + str(int(objective["Persist"]))
                objectives += "\n  | Squad = " + str(int(objective["Squad"]))
                objectives += "\n}}\n"

            rewards = "{{Quest Rewards |"
            for reward in data["Rewards"]:
                rewards += "\n  " + str(reward["Amount"]) + " " + reward["Object"] + ","
            rewards = re.sub(r",$", "", rewards)
            rewards += "\n}}"

            page_text = Template.format(
                questName=quest,
                faction=data["Giver"],
                description=data["Description"],
                objectives=objectives,
                rewards=rewards,
                acceptDialogue=data["StartDialogue"],
                completeDialogue=data["EndDialogue"],
                author=data.get("Author") or ""
            ).strip()
            print(quest)
            print(page_text)
            time.sleep(2)
            # page.save(page_text, summary=self.summary)


if __name__ == '__main__':
    Creator().run()
