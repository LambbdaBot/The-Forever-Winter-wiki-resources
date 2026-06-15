import json
import string
import re
import os
import time
import collections
import itertools
from collections import defaultdict
from itertools import chain

from mwcleric import AuthCredentials
from mwcleric import PageModifierBase
from mwcleric import WikiggClient
from mwparserfromhell.nodes import Template

"""
Apparently there is a problem with large gallery images overflowing on small phone screens.
The only adequate solution is to make max width smaller and make users click on pictures.
"""

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('test', credentials=credentials)
summary = 'Adjusting max image widths to prevent overflow on mobile'

class PageModifier(PageModifierBase):
    def update_plaintext(self, text):
        backup = text
        if self.current_page.namespace != 0:
            # don't do anything outside of the main namespace
            # for example, we don't want to modify template documentation or user sandboxes
            return backup
        galleries = re.findall(r'<gallery.*>', text)
        for gallery in galleries:
            width = re.findall(r'widths ?= ?(.*?) ?px', gallery)
            if width:
                width = int(width[0])
            height = re.findall(r'heights ?= ?(.*?) ?px', gallery)
            if height:
                height = int(height[0])
            if width and width > 300:
                replacement = re.sub(r'widths ?= ?(.*?) ?px', 'widths=300px', gallery)
                if height:
                    replacement = re.sub(r'heights ?= ?(.*?) ?px', 'heights='+str(int(height*(300/width)))+'px', replacement)
                text = text.replace(gallery, replacement)
        images = re.findall(r'\[\[File:.*\]\]', text)
        for image in images:
            size = re.findall(r'\| ?([0-9]*) ?px', image)
            responsive = "responsive-image" in image
            if size:
                size = int(size[0])
            if size and size > 300 and not responsive:
                replacement = image.replace("]]","|class=responsive-image]]")
                text = text.replace(image, replacement)
        time.sleep(2)
        return text
    
PageModifier(site, page_list=site.pages_using('Infobox Character'), # relevant templates: Infobox Quest, Infobox Character, any other template you can think of
             summary=summary).run()
