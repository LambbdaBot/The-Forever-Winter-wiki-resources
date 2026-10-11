import re
import os

lookup=r'Toothy' # Change your regex lookup word here
print("Searching for "+lookup)
for root,dirs,files in os.walk('E:\Program Files\FModel\Output\Exports\ForeverWinter\Content',topdown=True): # Change your export folder here
        for file in files:
                if 'json' not in file:
                        continue
                with open(os.path.join(root,file), encoding='utf-8') as f:
                        try:
                                text = f.read()
                                if len(re.findall(lookup,text))>0:
                                        print(root+'\\'+file) # Or print some other info
                        except UnicodeDecodeError:
                                continue
