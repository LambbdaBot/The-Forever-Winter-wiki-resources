import json
import string
import re
import os
import time

from mwcleric import AuthCredentials
from mwcleric import TemplateModifierBase
from mwcleric import WikiggClient
from mwparserfromhell.nodes import Template

"""
For every item, updates stats like weight and value.

Requirements:
        - Run Gather data\Get item data.py to create items.json
"""

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('test', credentials=credentials)
summary = 'Automatically updating internal item ids'

with open('items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fails = list()
#wins = list()

class TemplateModifier(TemplateModifierBase):
    def update_template(self, template: Template):
        # TemplateModifier is a generic framework for modifying templates
        # It will iterate through all pages containing at least one instance
        # of the specified template in the initialization call below and then
        # update every instance of the template in question with one batched edit per page
        if self.current_page.namespace != 0:
            # don't do anything outside of the main namespace
            # for example, we don't want to modify template documentation or user sandboxes
            return
        try:
            info = data[self.current_page.name]
        except KeyError:
            # if wiki page is not found in source json, log it
            fails.append(self.current_page.name)
            return
        if template.has('buy value'):
            template.remove('buy value')
        template.add('base value', str(info['value']))
        template.add('xp', str(info['xp']))
        template.add('weight', str(info['weight']))
        template.add('volume', str(info['volume']))
        template.add('internalTag', str(info['tag']))
        time.sleep(2)
        #wins.append(self.current_page.name)
        
TemplateModifier(site, 'Infobox ValuableItem',  # relevant templates: Infobox Consumable, Infobox Ammo, Infobox Equipment, Infobox LargeItem, Infobox ValuableItem, Infobox Weapon, HiddenCargoItem, Infobox Grenade, Infobox Attachment
                 summary=summary).run()

print("Failed:")
for page in fails:
    print("\t"+page)
#print()
#print("Not migrated:")
#for item in data:
#    if item not in wins:
#        print("\t"+item)
