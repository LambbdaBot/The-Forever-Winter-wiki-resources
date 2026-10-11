import time

from mwcleric import AuthCredentials, WikiClient
from mwcleric import WikiggClient
from mwcleric.page_modifier import PageModifierBase

credentials = AuthCredentials(user_file="me")
# the following login has been changed to edit test.wiki.gg rather than theforeverwinter.wiki.gg
# test.wiki.gg is a sandbox wiki that anyone may edit for any reason to test scripts
# so while you are testing your code, you can leave this as-is and view changes at test.wiki.gg
# then change it to your wiki afterwards
site = WikiggClient('theforeverwinter', credentials=credentials)
old = "Trial by Extraction Pt."
new = "Trial by Extraction Pt. "
summary = 'Renaming [' + old + "] to [" + new + ']'

titles = [
    "Bunco",
    "Scavengers",
    "Mech Trenches",
    "Elephant Mausoleum",
    "Trial by Extraction Pt.1",
    "Down to the Last Drop Pt. 1",
    "Down to the Last Drop Pt. 2",
    "Down to the Last Drop Pt. 3",
    "Bunco's Bounties Pt. 1",
    "Bunco's Bounties Pt. 2",
    "Bunco's Bounties Pt. 3",
    "Ghosts of the Enclave",
    "Dead Men Walking",
    "Electro-Magnetic Railway Pt. 1",
    "Electro-Magnetic Railway Pt. 2",
    "Electro-Magnetic Railway Pt. 3",
    "Electro-Magnetic Railway Pt. 4",
    "Electro-Magnetic Railway Pt. 5",
    "Electro-Magnetic Railway Pt. 6",
    "Electro-Magnetic Railway Pt. 7",
    "Electro-Magnetic Railway Pt. 8",
    "Electro-Magnetic Railway Pt. 9"
]

skipTo = None


class PageModifier(PageModifierBase):
    def __init__(self, site: WikiClient, **data):
        super().__init__(site, **data)
        self.skipped = False

    def update_plaintext(self, text):
        name = self.current_page.base_name
        if not self.skipped and skipTo:
            if name != skipTo:
                time.sleep(2)
                return text
            else:
                self.skipped = True
                return text
        # if "Map:" in name:
        #    return text

        text = text.replace(old, new)
        stuff = old.replace(" ", "_")
        text = text.replace(stuff, new)

        # print("Saving " + name)
        # print(text)
        time.sleep(2)
        return text


PageModifier(site, title_list=titles,
             summary=summary).run()
