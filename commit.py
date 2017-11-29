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
from nltk.stem.porter import PorterStemmer


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
        self.filenames,self.sourceAdded,self.sourceRemoved,self.sourceCurrent,self.numLinesChanged = self.parseDiff(diff)

    def __str__(self):
        return ('Author: %s\nMessage: %s\nSHA: %s\nDate: %s\nHour:%s\n \
                Minute: %s\n#Files Changed:%s\nisBuggy:%s\nChanges:%s\n'
                % (self.author,self.msg,self.sha,self.date,self.hour,self.minute,len(self.filenames),
                self.isBuggy,self.changes)).encode('utf8')

    def bowSourceCode(self,lines):
        bow = defaultdict(int)
        for line in lines:
            for term in self.parsePatchHelper(line):
                bow[term] = 1
        return bow 

    def parseDiff(self,diff):
        filenames = []
        sourceAdded = set()
        sourceRemoved = set()
        sourceCurrent = set()
        numLinesChanged = 0
        diff = json.loads(diff).split('\n')[1:]
        patchSet = PatchSet(diff,encoding='utf-8')
        for patch in patchSet:
            filenames.append(patch.path)
            for hunk in patch:
                for line in hunk.source:
                    if line[0] == '-':
                        sourceRemoved.add(line[1:])
                        numLinesChanged += 1
                for line in hunk.target:
                    if line[0] == '+':
                        sourceAdded.add(line[1:])
                        numLinesChanged += 1
                    sourceCurrent.add(line)
        added = self.bowSourceCode(sourceAdded)
        removed = self.bowSourceCode(sourceRemoved)
        current = self.bowSourceCode(sourceCurrent)
        return filenames,added,removed,current,numLinesChanged

    '''
    Feature extraction from commit messsage using Bag of Words aproach. 
    All words with non alphanumeric characters are ignored.
    '''
    def bowMSG(self):
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

    def bowFilenames(self):
        bow = collections.defaultdict(int)
        for filename in self.filenames:
            for term in re.split(r'[-/._]+',filename):
                for hump in self.camelCase(term):
                    bow[hump.lower()] = 1
        return bow

    def parsePatchHelper(self,line):
        operators = ['==','!=','++','--','&&','||','*=','/=','+=','-=','<','>','?','[]','//']
        wordDict = collections.defaultdict(int)
        for operator in operators:
            if line.find(operator) != -1:
                wordDict[operator] = 1

        stripped = ''
        for character in line:
            if character not in string.punctuation:
                stripped += character
            else:
                stripped += ' '

        for word in stripped.split():
            wordDict[word.lower()] = 1
        return wordDict

    def camelCase(self,line):
        words = set()
        word = ''
        i = 0
        while(i < len(line)):
            if line[i].isupper() and i != 0:
                words.add(word)
                word = ''
                while(i < len(line) and line[i].isupper()): #find acronyms
                    word += line[i]
                    i += 1
            else:
                word += line[i]
                i += 1
        words.add(word)
        return words

class BOWHelper:
    
    def __init__(self):
        return

    def featureAuthor(self,authorCorpus,commit):
        f = [word == commit.author for word in authorCorpus] 
        return f

    def featureCommitSource(self,corpusAdd,corpusRemove,corpusCurrent,commit):
        add = [commit.sourceAdded[word] for word in corpusAdd]
        rem = [commit.sourceRemoved[word] for word in corpusRemove]
        curr = [commit.sourceCurrent[word] for word in corpusCurrent]
        return add,rem,curr

    def featureFilename(self,corpus,commit):
        bowfiles = commit.bowFilenames()
        f = [bowfiles[word] for word in corpus]
        return f

    def featureCommitMsg(self,corpus,commit):
        bowMsg = commit.bowMSG()
        f = [bowMsg[word] for word in corpus]
        return f

    def buildFileNameCorpus(self,commits):
        corpus = set()
        for c in commits:
            for k,v in c.bowFilenames().iteritems():
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
            for k,v in c.bowMSG().iteritems():
                corpus.add(k)
        return sorted(corpus)

    def buildAuthorCorpus(self,commits):
        corpus = set()
        for c in commits:
            corpus.add(c.author)
        return sorted(corpus)



