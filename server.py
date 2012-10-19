#Author: Mike Jacobi
#Virtual Mafia Game
#Instructors: Roya Ensafi, Jed Crandall
#Cybersecurity, Spring 2012
#server.py is the automated moderator for Mafia

import traceback
import datetime
import sys
import os
import time
import random
import signal
import communication as c
from threading import Thread

i={}
inputVars=open('mafia.config','r').read().split('\n')
for var in inputVars:
	var=var.strip('\n').split('=')
	key=var[0]
	try:#if a line doesn't have an = sign
		value=var[1]
	except:
		continue
	i[key]=value
logFile=''

#time parameters
timeTillStart=int(i['timeTillStart'])
wolftalktime=int(i['wolfTalkTime'])
wolfvotetime=int(i['wolfVoteTime'])
townvotetime=int(i['townVoteTime'])
towntalktime=int(i['townTalkTime'])
witchvotetime=int(i['witchVoteTime'])
deathspeechtime=int(i['deathSpeechTime'])

test=int(i['test'])
numWolves=int(i['numWolves'])

#group people by roles
all={}
wolves={}
townspeople={}
witch={}

potions=[int(i['kill']),int(i['heal'])]#[kill,heal]

round=1

def removePlayer(player,giveSpeech):
    global all, wolves, witch
    isTownsperson=1
   
    newAll={}
    for p in all.keys():
        if player!=p:
            newAll[p]=all[p]
    newWolves={}
    for p in wolves.keys():
        if player!=p:
            newWolves[p]=wolves[p]
        else:
            #c.broadcast('%s was a wolf!'%player,all)
	    c.log('%s-wolf killed.'%p,1,0,1)
            isTownsperson=0
    if player in witch.keys():
        #c.broadcast(player+' was the witch!',all)
	c.log('%s-witch killed'%player,1,0,1)
        witch={}
        isTownsperson=0
    if isTownsperson:
	pass
        #c.broadcast(player+' was a townsperson.',all)
	c.log('%s-townsperson killed'%player,1,0,1)
    if giveSpeech:
        c.broadcast('These are %ss last words.'%player, all)
	c.send("Share your parting words.", all[player][1])
	c.setLogChat(1)
        c.spawnDeathSpeech(player,deathspeechtime)
	c.setLogChat(0)
    else:
	c.broadcast('%s was eliminated by the moderator.'%player,all)

    c.send('close',all[player][1])
    all=newAll
    wolves=newWolves
    if len(wolves)==1:
	wolftalktime=0

def quitGame(Signal, frame):
    global all
    c.broadcast('close',all)
    c.log('\nGAME FORCE QUIT BY MODERATOR',1,1,1)
    os.chmod(moderatorLogName,0744)
    if not test:
    	os.system('echo "Game is over." | wall'%msg)
    #sys.exit()
    os.kill(os.getpid(),signal.SIGKILL)

signal.signal(signal.SIGINT, quitGame)

def assign():
    global all, wolves, witch
    #balance the game accordingly
    numPlayers = len(all.keys())

    config=['W']
    for i in range(numWolves):
	config.append('w')
    for i in range(numPlayers-numWolves-1):
	config.append('t')

    #randomize roles
    random.shuffle(config)

    #assign roles and inform players
    for i in range(len(all.keys())):
	player=all.keys()[i]

        if config[i]=='w':
            wolves[player]=all[player]
            role='wolf'
        elif config[i]=='W':
            witch[player]=all[player]
            townspeople[player]=all[player]
            role='witch'
        else:
            townspeople[player]=all[player]
            role='townsperson'
	try:
       	    c.send('~~~~~ YOU ARE A %s ~~~~~'%role, all[player][1])
	except Exception, p:
	    c.log('ASSIGNERROR:%s'%p,1,0,1)

 
def standardTurn():
    global all, witch, potions
    wolfkill=0
    witchkill=0
    
    try:
        c.broadcast("Night falls and the town sleeps.  Everyone close your eyes",all)
	c.log('Night',0,1,0)
        #time.sleep(1)


        #**************WEREWOLVES************************
        c.broadcast("Werewolves, open your eyes.", c.complement(wolves,all))

        c.broadcast('Werewolves, %s, you must choose a victim.  You have %d seconds to discuss.'%(str(wolves.keys()),wolftalktime) ,wolves)
	#c.broadcast('Werewolves, '+str(wolves.keys())+', you must choose a victim.  You have '+str(wolftalktime)+' seconds to discuss.' ,wolves)
	c.log('Werewolves debate',0,1,0)
        c.allow(wolves)
        c.sleep(wolftalktime)

	c.broadcast("Werewolves, vote.", c.complement(wolves,all))
	
		
        c.broadcast('Werewolves, you must vote on a victim to eat.  You have %d seconds to vote.  Valid votes are %s.'%(wolfvotetime, str(sorted(all.keys()))),wolves)
	#c.broadcast('Werewolves, you must vote on a victim to eat.  You have '+str(wolfvotetime)+' seconds to vote.  Valid votes are '+str(sorted(all.keys())),wolves)
	c.log('Werewolves vote',0,1,0)
        wolfvote,voteType=c.poll(wolves,wolfvotetime, all.keys(), 'wolf', all, i['wolfUnanimous'],i['wolfSilentVote'])
	c.broadcast('Werewolves, go to sleep.',c.complement(wolves,all))
	if voteType==1:
	    c.broadcast('Vote not unanimous, nobody eaten.', wolves)
	    c.log('Werewolves not unanimous',0,1,0)
        #elif len(wolfvote)!=1:
	elif voteType==2:
            c.broadcast('Tie', wolves)
	    c.log('Werewolves vote tie',0,1,0)
        elif voteType==0:
            msg="Werewolves, you selected to eat %s"%str(wolfvote[0])
            wolfkill=1
            c.broadcast(msg,wolves)
	    c.log('Werewolves selected %s'%str(wolfvote[0]),0,1,0)

        #**********END WEREWOLVES************************


        #**************WITCH************************
        #construct the witch's options
        if len(witch)>0 and (potions[0] or potions[1]):
            c.broadcast('Witch, open your eyes.',c.complement(witch,all))
	    c.log('Witch vote',0,1,0)
	    witchPlayer=witch[witch.keys()[0]]

            if wolfkill:
                validKills=[]
                for p in all:
                    if p!=wolfvote[0]:
                        validKills.append(p)
		validKills=sorted(validKills)
                if potions[0] and potions[1]:
                    witchmoves=validKills+['Heal','Pass']
                elif potions[0]:
                    witchmoves=validKills+['Pass']
                else:
                    witchmoves=['Heal','Pass']
                c.send('Witch, wake up.  The wolves killed %s.  Valid votes are %s.'%(str(wolfvote),str(witchmoves)),witchPlayer[1])
		#c.send('Witch, wake up.  The wolves killed '+str(wolfvote)+'.  Valid votes are '+str(witchmoves),witchPlayer[1])
            else:
                if potions[0]:
                    witchmoves=all.keys()+['Pass']
                else:
                    witchmoves=['Pass']
		c.send('Witch, the wolves didnt feed tonight.  Valid votes are %s'%str(witchmoves),witchPlayer[1])

            #witch voting
            witchVote,voteType=c.poll(witch,witchvotetime,witchmoves,'witch',all,0,0)

            if witchVote==[] or witchVote[0]=='Pass' or voteType!=0:
		c.log('Witch passed',1,1,1)
		c.broadcast('Witch, close your eyes',all)
            elif witchVote[0]=='Heal':
		c.send('The Witch healed you!',all[wolfvote[0]][1])
		c.log('The Witch healed %s!'%wolfvote[0],0,0,1)
                wolfkill=0
                potions[1]-=1
                c.broadcast('The witch used a health potion! %d heal[s] remaining.'%potions[1],all)
		#c.broadcast('The witch used a health potion! '+str(potions[1])+' heal[s] remaining.',all)
            else:
                witchkill=1
                potions[0]-=1
	        c.broadcast('Witch, close your eyes',all)
        #**************END WITCH************************
        #**************START TOWN***********************
        if wolfkill:
            c.broadcast('The werewolves ate %s!'%wolfvote[0],all)
	    c.log('Werewolves killed %s'%wolfvote[0],0,1,0)
            removePlayer(wolfvote[0],1)
            if len(wolves)==0 or len(all)==len(wolves):
                return 1
        if witchkill:
            c.broadcast('The Witch poisoned %s!  %d poison[s] remaining.'%(witchVote[0],potions[0]),all)
            #c.broadcast('The Witch poisoned '+witchVote[0]+'!  '+ str(potions[0])+' poison[s] remaining.',all)
	    c.log('Witch poisoned %s'%witchVote[0],0,1,0)
            removePlayer(witchVote[0],1)
            if len(all)-len(wolves)==0 or len(wolves)==0:
                return 1

        c.allow(all)
	c.setLogChat(1)
        c.broadcast('It is day.  Everyone, open your eyes.  You will have %d seconds to discuss who the werewolves are.'%towntalktime,all)
        #c.broadcast('It is day.  Everyone, open your eyes.  You will have '+str(towntalktime)+' seconds to discuss who the werewolves are.',all)
	c.log('Day-townspeople debate',0,1,0)
        c.sleep(towntalktime)
        c.allow({})

	c.log('Townspeople vote',0,1,0)
        c.broadcast('Townspeople, you have %d seconds to cast your votes on who to hang. Valid votes are %s'%(townvotetime,str(sorted(all.keys()))), all)
	#c.broadcast('Townspeople, you have '+str(townvotetime)+' seconds to cast your votes on who to hang. Valid votes are '+str(sorted(all.keys())), all)
        killedPlayer,voteType = c.poll(all, townvotetime, all.keys(), 'town', all,i['townUnanimous'],i['townSilentVote'])
        #if len(killedPlayer)!=1:
	if voteType==2:
            msg = 'The vote resulted in a tie between players %s, so nobody dies today.'%killedPlayer
            c.broadcast(msg, all)
	    c.log('Townspeople vote tie',0,1,0)
        elif voteType==1:
		c.broadcast('The vote was not unanimous',all)
		c.log('Townspeople vote not unanimous',0,1,0)
	else:
            c.broadcast('The town voted to hang %s!'%killedPlayer[0],all)
	    c.log('Townspeople killed %s'%str(killedPlayer[0]),0,1,0)
            removePlayer(killedPlayer[0],1)
	c.setLogChat(0)
        #******************END TOWN*******************
        return 1
    except Exception, error:
	print traceback.print_exc()
        c.log('STANDARDTURNERROR:%s'%str(error),1,0,1)
        return 0

def listenerThread():
    global round,all
    while 1:
        i=raw_input().strip('\n')
	if i=='':
	    pass
        elif i=='help':
	    os.system('cat moderatorHelp.txt')
        elif i=='status':
	    print 'round %d'%round
            print 'all: %s'%str(all.keys())
            print 'wolves: %s'%str(wolves.keys())

            wStatus=': '
            wStatus+='%d poisons, '%potions[0]
            wStatus+='%d heals '%potions[1]
            print 'witch: %s%s'%(str(witch.keys()),wStatus)
        elif i[0:4]=='kill':
            player=i.split(' ')[1]
            c.broadcast('Moderator removed %s'%player,all)
	    c.log('Moderator removed %s'%player,0,1,0)
            removePlayer(player,0)
	elif i=='skip':
	    c.skip()
	    #c.broadcast('Moderator skipped current section.',all)
	    c.log('Moderator skipped current section.',0,1,0)
	else:
	    c.broadcast('moderator-%s'%i,all)
	    #c.log('moderator-'+i,0)

publicLogName=''
moderatorLogName=''
listenThread=None
chatThread=None

def main():
    global all,round,publicLogName,moderatorLogName

    if test:
	publicLogName='log/dummy.log'
	moderatorLogName='log/dummy-m.log'
	next=9999
    else:
    	nextround=open('log/nextround','r')
    	next=int(nextround.readline().strip('\n'))
    	nextround.close()
    	nextround=open('log/nextround','w')
   	nextround.write(str(next+1))
   	nextround.close()
	msg='Game %d starts in %d seconds.'%(next,timeTillStart)
    	#msg='Game '+str(next)+' starts in '+str(timeTillStart)+' seconds.'
	os.system('echo "%s" | wall'%msg)
    	publicLogName='log/%d.log'%next
        moderatorLogName='log/%dm.log'%next

    #pass the necessary input variables into the communication script
    c.setVars(i['readVulnerability'],i['imposterMode'],publicLogName,moderatorLogName)

    if i['moderatorLogMode']==1:
	os.system('touch '+moderatorLogName)
	os.system('chmod 700 '+moderatorLogName)
    else:
    	os.system('cp log/template '+moderatorLogName)

    c.log('GAME: '+str(next),1,1,1)

    listenThread=Thread(target=listenerThread,args=[])
    listenThread.start()
    c.log('\nmoderator listener thread started',1,0,1)

    all=c.handleConnections(timeTillStart,int(i['randomizeNames']))

    #ot=Thread(target=c.obscure,args=[])
    #ot.start()
    #c.log('obscurity thread started',1,0,1)

    #assign each connection a role
    assign()
    c.log('roles assigned',1,0,1)

    chatThread=Thread(target=c.groupChat,args=[all,])
    chatThread.start()
    c.log('group chat thread started',1,0,1)

    c.log('\nBegin.',1,1,1)
    c.broadcast('There are '+str(len(wolves))+' wolves, and '+str(len(all)-len(wolves))+' townspeople.',all)
    c.allow({})

    #the main part of the game
    while len(wolves)!=0 and len(wolves)<len(all):
	    c.log('\n\n',1,1,1)
	    c.broadcast('*'*50,all)
	    c.broadcast('*'*21+'ROUND '+str(round)+'*'*22,all)
	    c.broadcast('*'*15+str(len(all))+' players remain.'+'*'*18,all)
	    c.broadcast('*'*50,all)
	    c.log('Round '+str(round),0,1,0)
	    c.log('Townspeople: '+str(all.keys()),1,1,1)
	    c.log('Werewolves: '+str(wolves.keys()),1,0,1)
	    c.log('Witch: '+str(witch.keys()),1,0,1)
	    round+=1
            standardTurn()


    #end game
    if len(wolves)==0:
        c.log('\nTownspeople win!',0,1,0)
        c.broadcast('Townspeople win!',all)
    elif len(wolves)==len(all):
        c.log('\nWerewolves win!',0,1,0)
        c.broadcast('Werewolves win!',all)
    c.broadcast('win',all)

    c.log('End',1,1,1)
    if not test: os.chmod('log/%sm.log'%str(next),0744)#os.system('chmod 744 log/'+str(next)+'m.log')
    #logFile.close()
    if not test:
        os.system('echo "Game %s is over." | wall'%str(next))
    #os.system('killall -s 9 cat 2> /dev/null')
    #os.system('killall -s 9 sh 2> /dev/null')
    os.kill(os.getpid(),signal.SIGKILL)
    #listenThread._Thread__stop()
    #chatThread._Thread__stop()
    #sys.exit()

if __name__=='__main__':
    main()
