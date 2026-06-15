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
On every item page, lists vendors that sell it.

Requirements:
    - Run Gather data\Get vendor stock.py to create vendors.json
"""

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('test', credentials=credentials)
summary = 'Automatically updating vendor data'

with open('vendors.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

class PageModifier(PageModifierBase):
    def update_plaintext(self, text):
        backup = text
        page = self.current_page.name
        if self.current_page.namespace != 0:
            # don't do anything outside of the main namespace
            # for example, we don't want to modify template documentation or user sandboxes
            return backup
        oldTemplates = re.findall(r'{{VendorStock.*}}\n', text)
        if page in data:
            text = text.replace(oldTemplates[0], "$$$$$")
            for template in oldTemplates:
                text = text.replace(template,"")
            newstuff = ""
            for info in data[page]:
                newstuff += info + "\n"
            text = text.replace("$$$$$", newstuff)
        else:
            print(page+": vendor data not found")
            return backup
        time.sleep(2)
        return text
    
PageModifier(site, page_list=site.pages_using('VendorStock'), 
             summary=summary).run()
