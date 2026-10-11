import string
import re
import os
import time
import json

from mwcleric import AuthCredentials
from mwcleric.page_modifier import PageModifierBase
from mwcleric import WikiggClient
from mwparserfromhell.nodes import Template

"""
Updates rewards on every quest page.

Requirements:
        - Run Gather data\Get quest info (lambbda) to create quests.json
"""

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('test', credentials=credentials)
summary = 'Automatically updating rewards based on extracted game data'

with open("fails.txt", "a") as file:
        file.write("\n===== NEW MIGRATION =====\n")

quests = {}

with open("quests.json") as f: # TODO FIX QUEST PARSING
        quests = json.load(f)
        
class PageModifier(PageModifierBase):
        def update_plaintext(self, text):
                backup = text
                if self.current_page.namespace != 0:
                        # don't do anything outside of the main namespace
                        # for example, we don't want to modify template documentation or user sandboxes
                        return backup
                try:
                        info = quests[self.current_page.name.lower()]
                except KeyError:
                        # if wiki page is not found in source json, log it
                        with open("fails.txt", "a") as file:
                                file.write(self.current_page.name+" - not found in JSON\n")
                        return backup
                rewards = re.findall(r"[\s]*?{{QuestReward.*}}", text)
                text = text.replace(rewards[0],"$$$$")
                for template in rewards:
                        text = text.replace(template,"")
                text = text.replace("$$$$",info.get("reward"))
                return text

PageModifier(site, page_list=site.pages_using('QuestReward'),
			 summary=summary).run()
