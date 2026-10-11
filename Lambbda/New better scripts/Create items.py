import json
import time

from mwcleric import AuthCredentials
from mwcleric import WikiggClient

exportFolder = 'E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

Template = """{{{{Infobox ValuableItem
  | image = {image}.png
  | category = {category}
  | volume = {volume}
  | weight = {weight}
  | base value = {value}
  | slot = {slot}
  | hk = {hk}
  | xp = {xp}
  | internalTag = {tag}
}}}}

==Description==
{description}

== Acquisition ==
=== Loot ===


==Usage==
{{{{ItemUsage}}}}
"""

with open("items.json") as f:
    items = json.load(f)

whitelist = [
    "Inventory.Item.Quest_CombatDrug"
]


class Creator:
    summary = 'Automatically creating item page stubs'

    def __init__(self):
        credentials = AuthCredentials(user_file="me")
        self.site = WikiggClient('theforeverwinter', credentials=credentials)

    def run(self):
        for tag, data in items.items():
            if tag not in whitelist:
                continue
            item = data["Name"]
            page = self.site.client.pages[item]
            slot = "Small"
            if data["Volume"] is None:
                slot = "Large"

            page_text = Template.format(
                image=data["Icon"],
                category=data["Category"],
                volume=data["Volume"] or 0,
                weight=data["Weight"] or 0,
                value=data["Value"] or 0,
                slot=slot,
                hk=data["HK"],
                xp=data["XP"],
                tag=tag,
                description=data["Description"] or "No description available."
            ).strip()
            print(item)
            print("\\\\\\\\\\\\\\")
            print(page_text)
            print("\\\\\\\\\\\\\\")
            time.sleep(2)
            # page.save(page_text, summary=self.summary)


if __name__ == '__main__':
    Creator().run()
