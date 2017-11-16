import json
import collections
import datetime
import whatthepatch 
import string
from collections import defaultdict
from collections import OrderedDict
from copy import deepcopy
import re

#utility method
def mergeDicts(x,y):
    z = defaultdict(int)
    for k,v in x.iteritems():
        z[k] += v
    for k,v in y.iteritems():
        z[k] += v
    return z

class Commit:

    def __init__(self,jsonData):
        self.author = jsonData['commit']['author']['name']
        self.msg = jsonData['commit']['message']
        self.sha = jsonData['commit']['tree']['sha']
        self.date = jsonData['commit']['author']['date'].split('T')[0]
        self.hour,self.minute,_ = jsonData['commit']['author']['date'].split('T')[1].replace('Z','').split(':')
        self.files = [ChangedFile(f) for f in jsonData['files']] 

    def __str__(self):
        fileCount = len(self.files)
        return ('Author: %s\nMessage: %s\nSHA: %s\nDate: %s\nHour: %s\nMinute: %s\n#Files Changed:%s' % (self.author,self.msg,self.sha,self.date,self.hour,self.minute,fileCount)).encode('utf8')

    '''
    Feature extraction from commit messsage using Bag of Words aproach. 
    All words with non alphanumeric characters are ignored.
    '''
    def featureMsg(self):
        bow = collections.defaultdict(int)
        for word in self.msg.lower():
            if word.isalnum():
                bow[word] += 1
        return bow
    
    '''
    Represent the day of the week as a binary vector 
    (i.e. [0,1,0,0,0,0,0] = tuesday)
    '''
    def featureDate(self):
        dayOfWeek = [0]*7
        year,month,day = self.date.split('-')
        dayOfWeekIndex = datetime.date(int(year),int(month),int(day)).weekday()
        dayOfWeek[dayOfWeekIndex] = 1
        return dayOfWeek
    
    '''
    Represent the hour as a binary vector
    '''
    def featureHour(self):
        hour = [0]*24
        hour[int(self.hour)] = 1
        return hour

    def getFiles(self):
        return self.files

class ChangedFile:


    def __init__(self,jsonFile):
        self.filename = jsonFile['filename']
        self.numLinesAdded = jsonFile['additions']
        self.numLinesDeleted = jsonFile['deletions']
        self.numLinesChanged = jsonFile['changes']
        self.rawURL = jsonFile['raw_url']
        self.patch = self.getPatch(jsonFile)
        #self.featureSourceCode()
        #print json.dumps(jsonFile, indent=4, sort_keys=True)


    def __str__(self):
        return ('Filename: %s\nLines Added: %s\nLines Deleted: %s\nLines Changed: %s\nRaw URL: %s' % (self.filename,self.numLinesAdded,self.numLinesDeleted,self.numLinesChanged,self.rawURL)).encode('utf8')
    
    def getPatch(self,jsonFile):
        try:
            patch = jsonFile['patch']
        except:
            patch = None
        return patch

    '''
    Create BOW+ features from the source code 
    '''
    def featureSourceCode(self):
        if self.patch == None:
            return

        bowAdded = collections.defaultdict(int)
        bowRemoved = collections.defaultdict(int)

        diff = [x for x in whatthepatch.parse_patch(self.patch)]
        sourceLines = diff[0][2].split('\n')
        for line in sourceLines:
            line = line.lower()
            if len(line) > 1 :
                if line[0] == '+':
                    bowAdded = mergeDicts(self.parsePatchHelper(line[1:]),bowAdded)
                elif line[0] == '-':
                    bowRemoved = mergeDicts(self.parsePatchHelper(line[1:]),bowRemoved)
        #print list(reversed(sorted(bowAdded,key=bowAdded.__getitem__)))
        return bowAdded,bowRemoved

    def parsePatchHelper(self,line):
        operators = ['==','!=','++','--','&&','||','*=','/=','+=','-=','<','>','?']
        bowPlus = collections.defaultdict(int)

        for operator in operators:
            if line.count(operator) > 0:
                bowPlus[operator] = line.count(operator)
        strippedString = ''
        for character in line:
            if character not in string.punctuation:
                strippedString += character
            else:
                strippedString += ' '
        for word in strippedString.split():
            bowPlus[word] += 1
        return bowPlus

    '''
    BOW++ on filename
    TODO handle camelCase and acronyms 
    '''
    def featureFilename(self):
        bow = collections.defaultdict(int)
        test = defaultdict(int)
        for term in re.findall('[A-Z][^A-Z]*', self.filename):
            for t in re.split(r'[-|_|/\s]\s*', term):
                bow[t] += 1
        return bow

    def featureNumLinesChanged(self):
        return self.numLinesChanged
    
    def featureNumLinesAdded(self):
        return self.numLinesAdded
    
    def featureNumLinesDeleted(self):
        return self.numLinesDeleted

#TODO Bug class
class Bug:    
    def __init__(self):
        return
        #Feature length of time that bug was in code
        #Feature buggy line source BOW+ 

class BOWHelper:
    
    def __init__(self):
        return

    def bowCommit(self,corpusAdd,corpusRemove,commit):
        #merge all bow for individual files changed in a commit
        addedMerged = defaultdict(int)
        removedMerged = defaultdict(int)
        for f in commit.getFiles():
            fileBow = f.featureSourceCode()
            if fileBow:
                added,removed = fileBow
                addedMerged = mergeDicts(addedMerged,added)
                removedMerged = mergeDicts(removedMerged,added)
        
        bowAdded = defaultdict(int)
        bowRemoved = defaultdict(int)
        for word in corpusAdd:
            bowAdded[word] += addedMerged[word]
        for word in corpusRemove:
            bowRemoved[word] += removedMerged[word]

        return sorted(bowAdded.items()),sorted(bowRemoved.items())

    def bowFilename(self,corpus,commit):
        bowMerged = defaultdict(int)
        for f in commit.getFiles():
            if f.featureFilename():
                bowMerged = mergeDicts(bowMerged,f.featureFilename())

        bow = defaultdict(int)
        for word in corpus:
            bow[word] += bowMerged[word]

        return sorted(bow.items())

    def buildFileNameCorpus(self,commits):
        corpus = set()
        for c in commits:
            for f in c.getFiles():
                if f.featureFilename():
                    for k,v in f.featureFilename().iteritems():
                        corpus.add(k)
        return corpus 

    def buildCommitCorpus(self,commits):
        corpusAdd = set()
        corpusRemove = set()
        for c in commits:
            for f in c.getFiles():
                bow = f.featureSourceCode()
                if bow:
                    bowAdded,bowRemoved = bow
                    for k,v in bowAdded.iteritems():
                        corpusAdd.add(k)
                    for k,v in bowRemoved.iteritems():
                        corpusRemove.add(k)
        return corpusAdd,corpusRemove



