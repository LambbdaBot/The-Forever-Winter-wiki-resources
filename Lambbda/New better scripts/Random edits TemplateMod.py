import json
import string
import re
import os
import time

from mwcleric import AuthCredentials
from mwcleric import TemplateModifierBase
from mwcleric import WikiggClient
from mwparserfromhell.nodes import Template

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('theforeverwinter', credentials=credentials)
summary = 'Automatically updating infoboxes'

with open('items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


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
        name = self.current_page.name
        info = None
        for table in data:
            if name in data[table]:
                info = data[table][name]
                break
        if not info:
            # if wiki page is not found in source json, log it
            print(name + " not found")
            return
        template.add('damage', str(info['WeaponData']['WeaponDamage']))
        time.sleep(2)
        return


TemplateModifier(site, 'Infobox Weapon',
                 # relevant templates: Infobox Consumable, Infobox Ammo, Infobox Equipment, Infobox LargeItem, Infobox ValuableItem, Infobox Weapon, HiddenCargoItem, Infobox Grenade, Infobox Attachment
                 summary=summary).run()
