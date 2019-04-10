'''
Created on 20.11.2018

@author: ernstm
'''


#suche nach : <div class="player-section profile">

import io           # file op
import os           # file op
import glob         # file op
import re           # regular exp
from html.parser import HTMLParser
from enum import Enum

############################### DEBUG FLAG ########################################
__debug = False

#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------

class dto_item() :
    def __init__(self) :         
        self.attribute = dict()
        return
    
    def appendAttribut(self, key, value) :
        self.attribute[key] = value
        return

#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------

class dto_player() :
    def __init__(self):
        self.config = dict()
        self.playername = ""
        self.dps = 0    
        self.items = dict()
    
    def getDps(self) :
        return self.dps
    
    def getName(self) :
        return self.playername
        
    def extractNameAndDps(self, data):        
        data = data.split(sep=" ")         
        data = data[0]                      # first word is = Nexxyana_0013\xa0:\xa016857
        data = data.split(sep=":")          # results in ['Nexxyana_0013\xa0', '\xa016857']
        data[0] = data[0].replace("\xa0","")
        data[1] = data[1].replace("\xa0","")        
        self.playername = data[0]
        self.dps = int(data[1])
        print("Name: " + self.playername + "\tDPS:" + str(self.dps))
        pass

    def addConfig (self, data) :
        if (data == "") :
            return
        data = data.replace("\"", "")
        data = data.split(sep="=")
        try :                
            self.config[data[0]] = data[1]
        except :
            pass
        #print(data)    
        #print(self.playername)
        #list(self.config.keys())[0]
        return
    
    def addItem(self, data) :
        item = dto_item()
        data = data.split(sep=",")  # head=stormlurkers_cowl,id=159244,bonus_id=5062/1557/4786,azerite_powers=478/30/83
        slot_and_name = data[0].split(sep="=")    # fetch slot .. this is the slot and the name of the item
        item.slot = slot_and_name[0]
        if (item.slot == "shoulder") :
            item.slot = "shoulders"             # dont get why but simc ingame output has shoulder and simc has schoulders
        if (item.slot == "wrist") :
            item.slot = "wrists"                # same goes for wrist
            
        item.appendAttribut("name",slot_and_name[1])
        skipfirst_element = True
        for element in data :   
            if skipfirst_element :                
                skipfirst_element = False
                continue         
            attributeSet = element.split(sep="=")            
            item.appendAttribut(attributeSet[0], attributeSet[1])                
        self.items[item.slot] = item        
        return
    
    def __lt__ (self, other) :
        return self.dps > other.dps;
    
    def compare (self, other) :  
        diff = False
        print ("-----------------" + self.getName() + " -vs- " + other.getName() + " (dps: " + str(other.getDps()) + ")----------------------------")        
        for slot in other.items.keys() :            
            if (not slot in self.items) :
                print("add item at ", slot , " -> " , other.items[slot].attribute["id"] , "(" + other.items[slot].attribute["name"] + ")") 
                continue           
            for itemattribute in other.items[slot].attribute.keys() :               
                if (itemattribute == "name") :  #ignore name !
                    continue 
                if (not itemattribute in self.items[slot].attribute) :
                    continue
                if self.items[slot].attribute[itemattribute] != other.items[slot].attribute[itemattribute] :                    
                    diff = True
                    print ("diffslot : " + slot , "\tchange id : " + self.items[slot].attribute["id"] + " -> "  + other.items[slot].attribute["id"] , "(" + other.items[slot].attribute["name"] + ")")
                    #print ("diff attribute : " + itemattribute + " diff : " + self.items[slot].attribute[itemattribute] + " -> " + other.items[slot].attribute[itemattribute])
                    break; 
        # part 2 : Talentscanning
        if (self.config["talents"] != other.config["talents"]) :
            print ("Talents have been changed from ", self.config["talents"], " to " , other.config["talents"])
            diff = True
        if (diff != True) :
            print ("\t\t-- This is your current eq -- ")       
        return;
#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------

class eStatus(Enum):
    SEARCH_DIV_PLAYER_SECTION = 1
    SEARCH_DIV_PROFILE_SECTION = 2
    SEARCH_NAME_IN_PLAYER_SECTION = 3
    PRINT_PLAYER_NAME = 4
    SEARCH_PROFILE_TEXT_SECTION = 5
    PRINT_PROFILE_TEXT = 6
    
#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------
                                    # Globales
playerList = []

#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------
                                    # Html Parsing Class

class SimCHTMLParser(HTMLParser):   
    def __init__(self):                                 ## Konstruktor
        super().__init__()                              # Superkonstruktor
        self.status = eStatus.SEARCH_DIV_PLAYER_SECTION    # lokale Var
        self.divCounter = 0                             # div counter                
        
    #------------------------------------------------------------------------------
    
    def handle_starttag(self, tag, attrs):  
        
        #print(self.status)
        if (self.status == eStatus.SEARCH_DIV_PLAYER_SECTION) :
            self.handle_starttag_search_div_player(tag, attrs)
        elif (self.status == eStatus.SEARCH_DIV_PROFILE_SECTION) :
            self.handle_starttag_search_div_profile(tag, attrs)
        elif (self.status == eStatus.SEARCH_NAME_IN_PLAYER_SECTION) :    
            self.handle_starttag_search_player_name(tag, attrs)
        elif (self.status == eStatus.SEARCH_PROFILE_TEXT_SECTION):
            self.handle_starttag_search_profile_text_section(tag, attrs)
        else :
            pass
        #print("Encountered a start tag:", tag)
        
    #------------------------------------------------------------------------------
    
    def handle_starttag_search_div_player(self, tag, attrs) :
        if (tag == "div") :            
            #print(attrs)            
            for element in attrs:                     
                if ('class' in element) :                    
                    if (str(element[1]) == "player section grouped-first" or str(element[1]) == "player section section-open") :
                        #print(element)  
                        dprint("Found Player Section");
                        self.status = eStatus.SEARCH_NAME_IN_PLAYER_SECTION
                        return      

    #------------------------------------------------------------------------------
    
    def handle_starttag_search_div_profile(self, tag, attrs) :
        if (tag == "div") :            
            #print(attrs)            
            for element in attrs:                     
                if ('class' in element) :                    
                    if (str(element[1]) == "player-section profile") :                        
                        dprint("Found Profile Section")
                        self.status = eStatus.SEARCH_PROFILE_TEXT_SECTION
                        #print("Class: " + str(element[1]))
                        return
            
                         
    #------------------------------------------------------------------------------
    
    def handle_starttag_search_player_name(self, tag, attrs) :
        #print(tag)
        #print(attrs)
        if (tag == "h2") :
            #print("h2 found")
            self.status = eStatus.PRINT_PLAYER_NAME          
            
            
    
    #------------------------------------------------------------------------------
    
    def handle_starttag_search_profile_text_section(self, tag, attrs) :        
        if (tag == "p") :        
            self.status = eStatus.PRINT_PROFILE_TEXT         
        return
            
            
        
    #------------------------------------------------------------------------------    

    def handle_endtag(self, tag) :        
        if (self.status == eStatus.PRINT_PROFILE_TEXT) :
            if (tag == "p") :        
                curPlayer = playerList[playerList.__len__()-1]                
                dprint(curPlayer.playername)
                for key in curPlayer.items.keys() :
                    dprint(key, curPlayer.items[key].attribute)                                    
                dprint(curPlayer.config)                    
                
                self.resetStatus()
        return
        
    #------------------------------------------------------------------------------

    def handle_data(self, data) :
        if (self.status == eStatus.SEARCH_PROFILE_TEXT_SECTION) :
            return            
        elif (self.status == eStatus.SEARCH_NAME_IN_PLAYER_SECTION) :
            return                     
        elif (self.status == eStatus.PRINT_PLAYER_NAME) :
            newPlayer = dto_player()
            newPlayer.extractNameAndDps(data)
            playerList.append(newPlayer)
            self.status = eStatus.SEARCH_DIV_PROFILE_SECTION             #-> will be set in endtag <p>
            dprint("->", data);
            return;
        elif (self.status == eStatus.SEARCH_DIV_PROFILE_SECTION) :
            return;
        elif (self.status == eStatus.PRINT_PROFILE_TEXT) :                
            # if there is only 1 dps entry in that html it wont create a entry in playerList -> thus we have to create it
            if (len(playerList) == 0) :
                newPlayer = dto_player()
                newPlayer.playername = "SimC-Profile"
                playerList.append(newPlayer)
                
            curplayer = playerList[len(playerList)-1]
            parseSimCLine (curplayer, data)
            return;         
            
        self.resetStatus();
            

    def resetStatus(self) :
        self.status = eStatus.SEARCH_DIV_PLAYER_SECTION
        self.divCounter = 0
        
        
#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------
#                            random Functions

def dprint(*data) :
    if (__debug == True) :
        print(*data)
    return

def getfiles(dirpath):
    a = [s for s in os.listdir(dirpath)
         if os.path.isfile(os.path.join(dirpath, s))]
    a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)) * -1)
    return a

def parseInputTxtFile(player, input_txt_file) :
    with open(input_txt_file, 'r') as filehandle :
        for line in filehandle.readlines() :
            parseSimCLine(player, line.strip())
    return

def parseSimCLine(player, line) :
    if (line.find("#") == 0  or line.find("action") == 0) :
        return   
    if (line.find(",") != -1) :
        player.addItem(line)
    else :
        player.addConfig(line)                                   
    #print(data)
    return;       
#----------------------------------------------------------------------------------
###################################################################################
#----------------------------------------------------------------------------------
#                               MAIN Func


## find last simc file
folder = ".\\results\\"
files = getfiles(folder) 
croppedfiles = []
for file in files :
    if ".html" in file :
        croppedfiles.append(file)        
print (croppedfiles)


## Read HTML Simc
print ("Parsing HTML SimC output")
datafilehandle = io.open(folder + croppedfiles[0], mode="r", encoding="utf-8")
data = datafilehandle.read()
parser = SimCHTMLParser()
parser.feed(data)

## Read Input.txt
print ("Parsing input.txt")
currentEquippedPlayer = dto_player();
currentEquippedPlayer.playername = "current Equip"
parseInputTxtFile(currentEquippedPlayer, "input.txt");
# dbg things
dprint(currentEquippedPlayer.playername)
for key in currentEquippedPlayer.items.keys() :
    dprint(key , currentEquippedPlayer.items[key].attribute)                
dprint(currentEquippedPlayer.config)

## Sort list
playerList.sort();


## compare
for player in playerList :
    currentEquippedPlayer.compare(player)




