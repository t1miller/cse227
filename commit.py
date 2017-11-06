import json
import collections
import datetime


class Commit:

    def __init__(self,jsonData):
        self.author = jsonData['commit']['author']['name']
        self.msg = jsonData['commit']['message']
        self.sha = jsonData['commit']['tree']['sha']
        self.date = jsonData['commit']['author']['date'].split('T')[0]
        self.hour,self.minute,_ = jsonData['commit']['author']['date'].split('T')[1].replace('Z','').split(':')
        self.files = [ChangedFile(f) for f in jsonData['files']]  
        print self.__str__()

    def __str__(self):
        fileStr = ''
        for f in self.files:
            fileStr += ''#f.__str__()+'\n' ignore files in __str__
        return 'Author: %s\nMessage: %s\nSHA: %s\nDate: %s\nHour: %s\nMinute: %s\n%s' % (self.author,self.msg,self.sha,self.date,self.hour,self.minute,fileStr)

    '''
    Feature extraction from commit messsage using Bag of Words aproach. 
    All words with non alphanumeric characters are ignored.
    '''
    def featureMsg(self):
        bagOfWords = collections.defaultdict(int)
        for word in self.msg.lower():
            if word.isalnum():
                bagOfWords[word] += 1
        return bagOfWords
    
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
        hour[self.hour] = 1
        return hour


class ChangedFile:

    def __init__(self,jsonFile):
        self.filename = jsonFile['filename']
        self.numLinesAdded = jsonFile['additions']
        self.numLinesDeleted = jsonFile['deletions']
        self.numLinesChanged = jsonFile['changes']
        self.rawURL = jsonFile['raw_url']

    def __str__(self):
        return 'Filename: %s\nLines Added: %s\nLines Deleted: %s\nLines Changed: %s\nRaw URL: %s' % (self.filename,self.numLinesAdded,self.numLinesDeleted,self.numLinesChanged,self.rawURL)
    
    '''
    TODO handle camelCase and acronyms 
    '''
    def featureFilename(self):
        bagOfWords = collections.defaultdict(int)
        for term in self.filename.split('/'):
            if '-' in term:
                for subTerms in term.split('-'):
                    bagOfWords[subTerms] += 1
            else:
                bagOfWords[term] += 1
        print bagOfWords
    
    def featureNumLinesChanged(self):
        return self.numLinesChanged
    
    def featureNumLinesAdded(self):
        return self.numLinesAdded
    
    def featureNumLinesDeleted(self):
        return self.numLinesDeleted














