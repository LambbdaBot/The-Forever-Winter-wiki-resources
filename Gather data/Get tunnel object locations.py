import json
import string
import re
import os
import time

import collections
import itertools
from collections import defaultdict
from itertools import chain

"""
Get coordinates of every crate and vendor in the tunnels.

Usage:
# Open a test map https://theforeverwinter.wiki.gg/wiki/Map:Tunnels_Aerial
# Get the id of the tunnel you're interested in https://theforeverwinter.wiki.gg/wiki/Guides/Wiki/Extracting_game_data#Game_file_structure
# Find the corresponding id in tunnels.json, copy the contents
# Return to the test map, paste contents into the "markers" container

Wiki maps are not 1:1 compared to in-game, but with this method, and scaling and moving the map around a bit, you can get a pretty good idea on where everything is on the map.
"""

exportFolder='E:\Program Files\FModel\Output\Exports\ForeverWinter\Content'

tunnelToThingToLocation = defaultdict(dict)
containerDict={
    "BP_TunnelLoot_Spawner":"Random",
    "BP_LootContainer_Tunnels_MechChest":"Provisions",
    "BP_LootContainer_Meds_HighProbability":"Medical",
    "BP_LootContainer_Tunnels_Cylinder":"Civil",
    "BP_LootContainer_Ammo_HighProbability":"Ammo",
    "Vendor":"Vendor",
    "BP_LootContainer_AshenMesa_Random":"Materials"
}
for root,dirs,files in os.walk(exportFolder+'\FW\Maps\ProceduralTunnels\Dungeons',topdown=True):  
        for file in files:
                tunnel = re.findall(r'L_Dungeon_(.*)\.json', file)[0]
                thingToLocation = defaultdict(list)
                with open(os.path.join(root,file), encoding='utf-8') as f:
                        data = json.load(f)
                        vendorTargets = set()
                        for component in data:
                               typ = component.get("Type")
                               if typ == 'TargetPoint':
                                       name = component.get("Name")
                                       props = component.get("Properties")
                                       tags = None
                                       if props:
                                               tags = str(props.get("Tags"))
                                       if tags and 'Vendor' in tags:
                                               vendorTargets.add(name)
                        for component in data:
                                typ = component.get("Type")
                                if typ == 'SceneComponent':
                                        outer = component.get("Outer")
                                        props = component.get("Properties")
                                        if component.get("Template"):
                                            template = component.get("Template").get("ObjectPath")
                                        loc = None
                                        row = dict()
                                        if props:
                                               loc = props.get("RelativeLocation")
                                               if loc:
                                                       x = loc.get("X")/10
                                                       y = loc.get("Y")/10
                                                       z = loc.get("Z")/10
                                                       row.update({"x":x})
                                                       row.update({"y":y})
                                                       row.update({"name":"z: "+str(z)})
                                        if outer in vendorTargets and loc:
                                                thingToLocation['Vendor'].append(row)
                                        elif template and 'Loot' in template and loc:
                                                cont = re.findall(r".*\/(.*)\.",template)
                                                if cont:
                                                    cont = containerDict[cont[0]]
                                                    thingToLocation[cont].append(row)
                                elif typ == 'DungeonLevelInstance':
                                        props = component.get("Properties")
                                        if props:
                                            if props.get("DungeonLevel"):
                                                level = props.get("DungeonLevel").get("ObjectPath")
                                                if 'Treasure' in level: #YARR
                                                    wt = props.get("WorldTransform")
                                                    if wt:
                                                        loc = wt.get("Translation")
                                                        if loc:
                                                               row = dict()
                                                               x = loc.get("X")/10
                                                               y = loc.get("Y")/10
                                                               row.update({"x":x})
                                                               row.update({"y":y})
                                                               thingToLocation['Treasure'].append(row)
                if thingToLocation:
                        tunnelToThingToLocation[tunnel].update(thingToLocation)
                                                        
with open("tunnels.json", "w") as outfile:
        json.dump(tunnelToThingToLocation, outfile, indent=4)
