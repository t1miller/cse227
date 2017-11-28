import json
import collections
import datetime
import whatthepatch 
import string
from collections import defaultdict
from collections import OrderedDict
from copy import deepcopy
import re
from unidiff import PatchSet

#utility method
def mergeDicts(x,y):
    z = defaultdict(int)
    for k,v in x.iteritems():
        z[k] = v
    for k,v in y.iteritems():
        z[k] = v
    return z

class Commit:

    def __init__(self,author,msg,sha,date,hour,minute,diff,isBuggy):
        self.author = author
        self.msg = msg
        self.sha = sha
        self.date = date
        self.hour = hour
        self.minute = minute
        self.isBuggy = isBuggy
        self.filenames,self.sourceAdded,self.sourceRemoved,self.sourceCurrent,self.changes = self.parseDiff(diff)

    def __str__(self):
        return ('Author: %s\nMessage: %s\nSHA: %s\nDate: %s\nHour:%s\n \
                Minute: %s\n#Files Changed:%s\nisBuggy:%s\nChanges:%s\n'
                % (self.author,self.msg,self.sha,self.date,self.hour,self.minute,len(self.filenames),
                self.isBuggy,self.changes)).encode('utf8')

    def bowSourceCode(self,lines):
        bow = defaultdict(int)
        for line in lines:
            bow = mergeDicts(self.parsePatchHelper(line),bow)
        return bow

    def parseDiff(self,diff):
        filenames = []
        sourceAdded = set()
        sourceRemoved = set()
        sourceCurrent = set()
        changes = 0
        diff = json.loads(diff).split('\n')[1:]
        patchSet = PatchSet(diff,encoding='utf-8')
        for patch in patchSet:
            changes += patch.removed + patch.added  
            filenames.append(patch.path)
            for hunk in patch:
                for line in hunk.source:
                    if line[0] == '-':
                        sourceRemoved.add(line[1:].lower())
                for line in hunk.target:
                    if line[0] == '+':
                        sourceAdded.add(line[1:].lower())
                    sourceCurrent.add(line)
        added = self.bowSourceCode(sourceAdded)
        removed = self.bowSourceCode(sourceRemoved)
        current = self.bowSourceCode(sourceCurrent)
        return filenames,added,removed,current,changes

    '''
    Feature extraction from commit messsage using Bag of Words aproach. 
    All words with non alphanumeric characters are ignored.
    '''
    def featureMsg(self):
        bow = collections.defaultdict(int)
        for word in self.msg.lower().split():
            if word.isalnum():
                bow[word] = 1
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

    def featureFilenames(self):
        bow = collections.defaultdict(int)
        for filename in self.filenames:
            for term in re.split(r'[-/._]+',filename):
                bow[term.lower()] = 1
        return bow

    def parsePatchHelper(self,line):
        operators = ['==','!=','++','--','&&','||','*=','/=','+=','-=','<','>','?','[]','//']
        bowPlus = collections.defaultdict(int)
        for operator in operators:
            if line.count(operator) > 0:
                bowPlus[operator] = 1
        strippedString = ''
        for character in line:
            if character not in string.punctuation:
                strippedString += character
            else:
                strippedString += ' '
        for word in strippedString.split():
            bowPlus[word] = 1
        return bowPlus

class BOWHelper:
    
    def __init__(self):
        return

    def bowAuthor(self,authorCorpus,commit):
        f = []
        index = 0
        for word in authorCorpus:
            if word == commit.author:
                f.append(1)
                f += [0]*(len(authorCorpus)-index)
                break
            f.append(0)
            index += 1
        return f

    def bowCommitSource(self,corpusAdd,corpusRemove,corpusCurrent,commit):
        matched = 0
        add = []
        rem = []
        cur = []
        for word in corpusAdd:
            if commit.sourceAdded[word]:
                add.append(1)
                matched += 1
                if len(commit.sourceAdded) == matched:
                    add += [0]*(len(corpusAdd)-matched)
                    break
            else:
                add.append(0)
        matched = 0
        for word in corpusRemove:
            if commit.sourceRemoved[word]:
                rem.append(1)
                matched += 1
                if len(commit.sourceRemoved) == matched:
                    rem += [0]*(len(corpusRemove)-matched)
                    break
            else:
                rem.append(0)

        matched = 0
        for word in corpusCurrent:
            if commit.sourceCurrent[word]:
                cur.append(1)
                matched += 1
                if len(commit.sourceCurrent) == matched:
                    cur += [0]*(len(corpusCurrent)-matched)
                    break
            else:
                rem.append(0)
        return add,rem,cur#sorted(bowAdded.items()),sorted(bowRemoved.items()),sorted(bowCurrent.items())

    def bowFilename(self,corpus,commit):
        bowfiles = commit.featureFilenames()
        f = []
        matched = 0
        for word in corpus:
            if bowfiles[word]:
                f.append(1)
                matched += 1
                if len(bowfiles) == matched:
                    f += [0]*(len(corpus)-matched)
                    break
            else:
                f.append(0)
        return f

    def bowCommitMsg(self,corpus,commit):
        bowMsg = commit.featureMsg()
        f = []
        matched = 0
        for word in corpus:
            if bowMsg[word]:
                f.append(1)
                matched += 1
                if len(bowMsg) == matched:
                    f += [0]*(len(corpus)-matched)
                    break
            else:
                f.append(0)
        return f

    def buildFileNameCorpus(self,commits):
        corpus = set()
        bowMerged = defaultdict(int)
        for c in commits:
            bowMerged = mergeDicts(bowMerged,c.featureFilenames())
            for k,v in c.featureFilenames().iteritems():
                corpus.add(k)
        return sorted(corpus) 

    def buildCommitSourceCorpus(self,commits):
        corpusAdd = set()
        corpusRemove = set()
        corpusCurrent = set()
        for c in commits:
            for k,v in c.sourceAdded.iteritems():
                corpusAdd.add(k)
            for k,v in c.sourceRemoved.iteritems():
                corpusRemove.add(k)
            for k,v in c.sourceCurrent.iteritems():
                corpusCurrent.add(k)
        return sorted(corpusAdd),sorted(corpusRemove),sorted(corpusCurrent)

    def buildCommitMsgCorpus(self,commits):
        corpus = set()
        for c in commits:
            for k,v in c.featureMsg().iteritems():
                corpus.add(k)
        return sorted(corpus)

    def buildAuthorCorpus(self,commits):
        corpus = set()
        for c in commits:
            corpus.add(c.author)
        return sorted(corpus)



