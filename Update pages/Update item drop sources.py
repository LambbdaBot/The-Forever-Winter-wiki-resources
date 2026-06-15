import json
import string
import re
import os
import time

from mwcleric import AuthCredentials
from mwcleric import PageModifierBase
from mwcleric import WikiggClient
from mwparserfromhell.nodes import Template

"""
Updates drop sources on item pages.
Run Gather data\Get crate loot tables.py to create dropsByCrate.json
"""

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('test', credentials=credentials)
summary = 'Automatically updating crate drop tables'

with open('dropsByCrate.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

class PageModifier(PageModifierBase):
    def update_plaintext(self, text):
        backup = text
        page = self.current_page.name
        if self.current_page.namespace != 0:
            # don't do anything outside of the main namespace
            # for example, we don't want to modify template documentation or user sandboxes
            return backup
        oldTemplates = re.findall(r'{{ItemLocation.*}}\n', text)
        for template in oldTemplates:
            text = text.replace(template, "")
        if page in data:
            oldTemplates = re.findall(r'{{ItemLoot}}', text)
            if not oldTemplates:
                print("what the fuck "+page)
                return backup
            text = text.replace(oldTemplates[0], "$$$$${{ItemLoot}}")
            newstuff = ""
            for info in data[page]:
                container = info.get("Container")
                maps = ""
                locations = info.get("Locations")
                for location in locations:
                    maps+=location+", "
                maps = re.sub(r", $","",maps)
                condition = info.get("Condition")
                chance = str(info.get("Chance"))
                newstuff += "{{ItemLocation"
                newstuff += " | container = "+container
                if container == "Ground":
                    newstuff += " | containerType = Ground"
                else:
                    newstuff += " | containerType = Crate"
                newstuff += " | maps = "+maps
                if condition:
                    newstuff += " | condition = "+condition
                if chance:
                    newstuff += " | chance = "+chance
                else:
                    newstuff += " | chance = 10000"
                newstuff += "}}\n"
            text = text.replace("$$$$$", newstuff)
        else:
            # print(page+": location data not found")
            time.sleep(2)
            return backup
        time.sleep(2)
        return text
    
# PageModifier(site, page_list=site.pages_using('ItemLocation'),
PageModifier(site, page_list=site.pages_using('ItemLoot'), 
             summary=summary).run()
