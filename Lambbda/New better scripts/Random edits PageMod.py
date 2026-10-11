import string
import re
import os
import time
import json

from mwcleric import AuthCredentials
from mwcleric.page_modifier import PageModifierBase
from mwcleric import WikiggClient
from mwparserfromhell.nodes import Template

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('theforeverwinter', credentials=credentials)
summary = 'Doing random bot things'


class PageModifier(PageModifierBase):
    def update_plaintext(self, text):
        backup = text
        name = self.current_page.name
        if self.current_page.namespace != 0:
            # don't do anything outside the main namespace
            # for example, we don't want to modify template documentation or user sandboxes
            return backup
        text = text.re

        time.sleep(5)
        return text


PageModifier(site, page_list=site.pages_using('Infobox Quest'),
             summary=summary).run()
