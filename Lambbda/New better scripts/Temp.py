import json

"""# update wikiLocalization ids
with open(r"wikiLocalization.json") as f:
    wikiLocalization = json.load(f)

for key, value in wikiLocalization.items():
    if "_5" in key:
        wikiLocalization[key] = value + " (alt)"

with open("wikiLocalization.json", "w") as outfile:
    json.dump(wikiLocalization, outfile, indent=4)

"""
# list items with duplicate names
with open(r"items.json") as f:
    items = json.load(f)

dupes = {}
seen = {}
for table in items.values():
    for item in table.values():
        if item["Name"] in seen:
            if seen[item["Name"]] not in dupes:
                dupes.update({seen[item["Name"]]: item["Name"]})
            dupes.update({item["Tag"]: item["Name"]})
        else:
            seen.update({item["Name"]: item["Tag"]})

for k, v in dupes.items():
    print('"' + k + '": "' + v + '",')
