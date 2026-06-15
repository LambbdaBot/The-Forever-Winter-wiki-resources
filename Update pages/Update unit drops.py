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
Updates drop tables on unit pages.
Run Gather data\Get unit loot tables.py to create dropsByUnit.json
"""

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('test', credentials=credentials)
summary = 'Automatically updating drops based on extracted game data'

with open("dropsByUnit.json") as f:
    drops = json.load(f)

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
        unit = ''
        if template.has('unit'):
            unit = str(template.get("unit").value).strip()
        else:
            unit = self.current_page.name
        if unit in drops:
            if len(drops[unit]) < 1:
                print("\t"+self.current_page.name+" / "+unit+" : no drops found")
                fails.append("\t"+self.current_page.name+" / "+unit+" : no drops found")
            else:
                template.remove("items")
                output = ''
                for drop in drops[unit]:
                    output += drop.get("Item")+"/"+str(drop.get("Chance"))+", "
                output = re.sub(r", $","",output)
                template.add("items",output)
        else:
            print("\t"+self.current_page.name+" / "+unit+" : not in drops")
            fails.append("\t"+self.current_page.name+" / "+unit+" : not in drops")
        time.sleep(2)
        
TemplateModifier(site, 'Drops', 
                 summary=summary).run()

if len(fails)>0:
    print("Failed:")
else:
    print("Completed successfully")
for page in fails:
    print(page)
