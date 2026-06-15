import json
import glob
import re
import dpath.util
import os

# Use Fmodel to exctract folders from game archives folder : Save Folders Package Properties (json)
unitFiles = [] + glob.glob("E:\Program Files\FModel\Output\Exports\ForeverWinter\Content\FW\Quests\**\*.json", recursive=True)
basePath = r"E:\Program Files\FModel\Output\Exports\ForeverWinter\Content\FW"
questsDict = {}

for fn in unitFiles:
    content = open(fn, "r", encoding="latin1").read()
    parsedJson = json.loads(content)[0]
    name = dpath.util.values(parsedJson, "Name")[0]
    qname = dpath.values(parsedJson, "/Properties/QuestName/SourceString")

    qtext = dpath.values(parsedJson, "/Properties/QuestText/SourceString")
    qimg = dpath.values(parsedJson, "/Properties/QuestImage/AssetPathName")

    tasks = dpath.values(parsedJson, "/Properties/Tasks/*")
    rewards = dpath.values(parsedJson, "/Properties/Rewards/*")
    rewardText = dpath.values(parsedJson, "/Properties/RewardText/SourceString")

    StartDialogue = dpath.values(parsedJson, "/Properties/StartDialogue/ObjectPath")
    preRewardDialogue = dpath.values(parsedJson, "/Properties/PreRewardDialogue/ObjectPath")

    QuestGiverName = None
    startDialogues = None
    preRewardDialogues = None

    if StartDialogue:
        StartDialogue = StartDialogue[0]
        StartDialogue = StartDialogue.replace("/Game/FW/","")
        StartDialogue = StartDialogue.split(".")[0]
        StartDialogue = StartDialogue.replace("/","\\")
        c = open(os.path.join(basePath,StartDialogue+".json"), "r", encoding="latin1").read()
        startDialogueJson = json.loads(c)
        QuestGiverName = dpath.values(startDialogueJson, "*/Properties/Quest Giver Name/SourceString")
        if QuestGiverName: QuestGiverName = QuestGiverName[0]
        startDialogues = dpath.values(startDialogueJson, "*/Properties/DialogueText/*/SourceString")

    if preRewardDialogue:
        preRewardDialogue = preRewardDialogue[0]
        preRewardDialogue = preRewardDialogue.replace("/Game/FW/","")
        preRewardDialogue = preRewardDialogue.split(".")[0]
        preRewardDialogue = preRewardDialogue.replace("/","\\")
        c = open(os.path.join(basePath,preRewardDialogue+".json"), "r", encoding="latin1").read()
        preRewardDialogueJson = json.loads(c)
        QuestGiverName = dpath.values(preRewardDialogueJson, "*/Properties/Quest Giver Name/SourceString")
        if QuestGiverName: QuestGiverName = QuestGiverName[0]
        preRewardDialogues = dpath.values(preRewardDialogueJson, "*/Properties/DialogueText/*/SourceString")







    if not qname: continue
    if name in questsDict: print ("Dupe", name, fn)

    questsDict[name] = {}
    questDict = questsDict[name]



    questTasks = []
    questRewards = []

    questDict["QuestName"]= qname[0]
    if qtext: questDict["QuestText"] = qtext[0]
    if qimg: questDict["QuestImage"] = qimg[0]
    if rewardText: questDict["RewardText"] = rewardText[0]
    questDict["Tasks"] = questTasks
    questDict["QuestRewards"] = questRewards
    if QuestGiverName: questDict["QuestGiverName"] = QuestGiverName
    if startDialogues: questDict["startDialogues"] = startDialogues
    if preRewardDialogues: questDict["preRewardDialogues"] = preRewardDialogues

    questDict["QuestFile"] = fn.replace(r"E:\Program Files\FModel\Output\Exports\ForeverWinter\Content","\Game").replace("\\","/") #ugh

    for t in tasks:
        taskDict = {}
        action = dpath.values(t, "/Action")[0]
        taskDict["TaskAction"] = action
        #print ("\tTask action:", action)

        taskText = dpath.values(t, "/TaskText/SourceString")
        if taskText:
            taskDict["TaskText"] = taskText[0]
            #print ("\tTask text:", taskText[0])


        bExtractionRequired = dpath.values(t, "/bExtractionRequired")[0]
        bPersistAcrossSessions = dpath.values(t, "/bPersistAcrossSessions")[0]
        bSquadContribution = dpath.values(t, "/bSquadContribution")[0]
        if bExtractionRequired:
            taskDict["ExtractionRequired"] = True
            #print ("\t\tExtractionRequired")
        if bPersistAcrossSessions:
            taskDict["PersistAcrossSessions"] = True
            #print ("\t\tPersistAcrossSessions")
        if bSquadContribution:
            taskDict["SquadContribution"] = True
            #print ("\t\tSquadContribution")


        RequiredMap = dpath.values(t, "/RequiredMap/AssetPathName")[0]
        if RequiredMap:
            taskDict["RequiredMap"] = RequiredMap
            #print ("\t\tTask map:", RequiredMap)


        PawnTag = dpath.values(t, "/PawnTag/TagName")[0]
        if "None" not in PawnTag:
            taskDict["PawnTag"] = PawnTag
            #print ("\t\tPawnTag:", PawnTag)

        FactionTag = dpath.values(t, "/FactionTag/TagName")[0]
        if "None" not in FactionTag:
            taskDict["FactionTag"] = FactionTag
            #print ("\t\tFactionTag:", FactionTag)

        CompletionCount = dpath.values(t, "/CompletionCount")[0]
        if CompletionCount>0:
            taskDict["CompletionCount"] = CompletionCount
            #print ("\t\t"+CollectItem,":", CompletionCount)

        CollectItem = dpath.values(t, "/CollectItemRowHandle/RowName")[0]
        if "None" not in  CollectItem:
            taskDict["CollectItem"] = CollectItem

        #CollectItemContext = dpath.values(t, "/CollectItemContext/TagName")[0] # whatistis

        questTasks.append(taskDict)

    #for consistency check
    totalwater = 0
    totalxp = 0
    totalcred = 0

    for r in rewards:
        reward={}
        water = dpath.values(r, "/DaysOfWater")[0]
        xp = dpath.values(r, "/EarnedXP")[0]

        item = dpath.values(r, "/RewardItemRowHandle/RowName")[0]
        itemCount = dpath.values(r, "/ItemCount")[0]

        faction = dpath.values(r, "/EarnedFactionRep/FactionTag/TagName")[0]
        EarnedRep = dpath.values(r, "/EarnedFactionRep/EarnedRep")[0]

        if water>0:
            reward["Water"]=water
            totalwater +=water
        if xp>0:
            reward["Xp"]=xp
            totalxp +=xp
        if itemCount>0:
            reward[item]=itemCount
            if item == "TestCurrency":
                totalcred += itemCount

        if EarnedRep>0:
            reward[faction]=EarnedRep

        questRewards.append(reward)

    #consistency check
    if rewardText:
        tt = []
        for t in rewardText[0].replace(",","").split(" "):
            if len(t)==0: continue
            if "XP" in t and "XP" != t[:2]:
                tt.append(t.split("X")[0])

            tt.append(t)

        tt = [t for t in tt if len(t)>0]

        textxp = -1
        textcred = -1
        textwater = -1
        for i,t in enumerate(tt):
            if "Credit" in t: textcred = int(tt[i-1])
            if "XP" in t: textxp = int(tt[i-1])
            if "days" in t: textwater = int(tt[i-1])
        if textxp!=  totalxp and textxp!=-1:
            print (qname[0], rewardText, "XP",textxp,totalxp )
        if textcred != totalcred and textcred!=-1:
            print (qname[0], rewardText, "Credits",textcred,totalcred )
        if textwater != totalwater and textwater!=-1:
            print (qname[0], rewardText, "water",textwater,totalwater )



print(len(questsDict))
j = json.dumps(questsDict, indent=4)
with open('quests.json', 'w') as fp:
    print(j, file=fp)
