import requests
import numpy as np
import GroupRankPrivateInfo #defines variable AccessToken

#Specify Constants
GroupIndex=0 #Modify for different Group
AuthorizationLink=GroupRankPrivateInfo.AuthorizationLink
BaseRequestURL="https://api.groupme.com/v3"
AccessToken=GroupRankPrivateInfo.AccessToken
Filler="?token="

#Request first block of messages from group
def FRequest(RequestType,Params):
    global BaseRequestURL, AccessToken, Filler
    RequestURL=BaseRequestURL+RequestType+Filler+AccessToken
    return requests.get(RequestURL,params=Params).json()["response"]
AllGroups=FRequest("/groups",{"per_page":(GroupIndex+1)})
Group=AllGroups[GroupIndex]
ID=Group["id"]
CountMessages=FRequest("/groups/"+str(ID)+"/messages",{})["count"]
ParsedMessages=0
NumMembers=0
BlockOfMessages=FRequest("/groups/"+str(ID)+"/messages",{"limit":100})["messages"]

#Iterate through all messages, fill in Likes and IDs
LikesAdjList=[]
IDtoIndex={}
IndexToName={}
while (True):
    ParsedMessages+=len(BlockOfMessages)
    for Message in BlockOfMessages:
        if (Message["sender_type"]=="system"):
            continue
        Sender=Message["sender_id"]
        AllLikes=Message["favorited_by"]
        if not (Sender in IDtoIndex):
            IDtoIndex[Sender]=len(LikesAdjList)
            LikesAdjList.append([])
        SenderIndex=IDtoIndex[Sender]
        NumMembers=max(NumMembers,SenderIndex+1)
        if not (SenderIndex in IndexToName):
            IndexToName[SenderIndex]=Message["name"]
        for Like in AllLikes:
            if not (Like in IDtoIndex):
                IDtoIndex[Like]=len(LikesAdjList)
                LikesAdjList.append([])
            LikeIndex=IDtoIndex[Like]
            LikesAdjList[SenderIndex].append(LikeIndex)
            NumMembers=max(NumMembers,LikeIndex+1)
    if (ParsedMessages==CountMessages):
        break
    LastID=BlockOfMessages[len(BlockOfMessages)-1]["id"]
    Params={"limit":100,"before_id":LastID}
    try:
        BlockOfMessages=FRequest("/groups/"+str(ID)+"/messages",Params)["messages"]
    except:
        break

#Convert previous data structures into MemberList and LikesProbability
MemberList=["?"]*NumMembers
for Index in IndexToName:
    MemberList[Index]=IndexToName[Index]
LikesMatrix=np.zeros((NumMembers,NumMembers))
for MemberIndex in range(NumMembers):
    MemberLikes=LikesAdjList[MemberIndex]
    for Like in MemberLikes:
        LikeIndex=int(Like)
        if (LikeIndex!=MemberIndex):
            LikesMatrix[LikeIndex][MemberIndex]+=1
LikesProbability=np.zeros((NumMembers,NumMembers))
for Row in range(NumMembers):
    LikesSum=0
    for Col in range(NumMembers):
        LikesSum+=LikesMatrix[Row][Col]
    if (LikesSum==0):
        for Col in range(NumMembers):
            if (Row!=Col):
                LikesProbability[Row][Col]=1/(NumMembers-1)
    else:
        for Col in range(NumMembers):
            LikesProbability[Row][Col]=LikesMatrix[Row][Col]/LikesSum

#Convert results into more readable format and print
class MemberRank:
    def __init__(self,Member,Value):
        self.Member=Member
        self.Value=Value
    def __lt__(self,other):
        return (self.Value<other.Value)
Ranks=[1/NumMembers]*NumMembers
for Iteration in range(100):
    NewRanks=[0]*NumMembers
    for Row in range(NumMembers):
        for Col in range(NumMembers):
            NewRanks[Col]+=Ranks[Row]*LikesProbability[Row][Col]
    Ranks=NewRanks
ResultClass=[]
for Row in range(NumMembers):
    MemberName="?"
    if (Row in IndexToName):
        MemberName=IndexToName[Row]
    ResultClass.append(MemberRank(MemberName,Ranks[Row]))
ResultClass.sort()
ResultClass.reverse()
Result=[]
for Row in range(min(NumMembers,50)):
    ResultRow=[ResultClass[Row].Member,100*ResultClass[Row].Value]
    print(ResultClass[Row].Member,round(100*ResultClass[Row].Value,1))
    Result.append(ResultRow)







