import commitExtractor as ce
from commit import Commit
from commit import BOWHelper
from collections import defaultdict
from collections import OrderedDict
import operator
from sklearn import svm
from sklearn.neighbors import NearestNeighbors
import numpy as np
import os
import json
import sys
import random

reload(sys)
sys.setdefaultencoding('utf-8')



def parseCommits(buggyHash,path):
    commits = []
    i = 0
    for filename in os.listdir(path):
        data = json.load(open(path+filename))
        sha = data['sha'][1:8]#only first 7 char of hash
        author = data['commit']['author']['name']
        msg = data['commit']['message']
        date = data['commit']['author']['date'].split('T')[0].replace("\"","")
        hour,minute,_,_ = data['commit']['author']['date'].split('T')[1].replace('Z','').split(':')
        diff = data['diff']
        isBuggy = buggyHash[sha]
        commits.append(Commit(author,msg,sha,date,hour,minute,diff,isBuggy))
        if i % 1000 == 0:
            print 'parsed ',i,' commits'
        if i == 1000:
            return commits
        i += 1

def parseBugs(path):
    buggyHash = defaultdict(int)
    for filename in os.listdir(path):
        data = json.load(open(path+filename))
        for h in data['blames']:
            buggyHash[h[:7]] = 1
    return buggyHash


'''
def buggiestInterval(commits,intervalLength=1000):
    bestInterval = []
    bestBugCount = float('-inf')
    for i in range(len(commits)/intervalLength):
        interval = commits[i*1000:i*1000+1000]
        buggyCount = sum([c.isBuggy for c in interval])
        print 'buggyCount:',buggyCount,', commits[',i*1000,':',i*1000+1000,']'
        if buggyCount > bestBugCount:
            bestBugCount = buggyCount
            bestInterval = interval
    return bestInterval
'''

print 'parsing commits'
buggyHash = parseBugs('./data/bug_data/')
commits = parseCommits(buggyHash,'./data/commit_data/')
#commits = buggiestInterval(commits)


bowhelper = BOWHelper()
#build corpi
corpusAdd,corpusRemove,corpusCurrent = bowhelper.buildCommitSourceCorpus(commits)
corpusFilename = bowhelper.buildFileNameCorpus(commits)
corpusMsg = bowhelper.buildCommitMsgCorpus(commits)
corpusAuthor = bowhelper.buildAuthorCorpus(commits)


for corp in corpusCurrent:
    print corp

def featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,corpusAuthor,commit):
    f = []
    f.append(1)
    f += commit.featureHour()
    f += commit.featureDate()
    f.append(commit.changes)
    f.append(len(commit.filenames))
    f += bowhelper.bowAuthor(corpusAuthor,commit)
    f += bowhelper.bowFilename(corpusFilename,commit)
    f += bowhelper.bowCommitMsg(corpusMsg,commit)
    bowAdded,bowRemoved,bowCurrent = bowhelper.bowCommitSource(corpusAdd,corpusRemove,corpusCurrent,commit)
    f += bowAdded
    f += bowRemoved
    f += bowCurrent
    return f

#print featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,corpusAuthor,commits[0])

print 'builing feature vectors'
x = []
for i,c in enumerate(commits):
    x.append(featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,corpusAuthor,c))
    if i % 100 == 0:
        print 'completed ',i,' features'

x_train = x[:len(x)/2]
x_test = x[len(x)/2:]
print 'builing labels'
y = [int(c.isBuggy) for c in commits]
y_train = y[:len(y)/2]
y_test = y[len(y)/2:]

def accuracy(p,y):
    tp,tn,fp,fn = 0.0,0.0,0.0,0.0
    for i in range(len(y)):
        if p[i] == 1 and y[i] == 1:
            tp += 1
        elif p[i] == 1 and y[i] == 0:
            fp += 1
        elif p[i] == 0 and y[i] == 0:
            tn += 1 
        elif p[i] == 0 and y[i] == 1:
            fn += 1
    #metrics used by the 'Clean or Buggy?' paper
    buggyPrecision = tp/(tp + fp)
    buggyRecall = tp/(tp + fn) 
    cleanPrecison = tn/(tn + fn)
    cleanRecall = tn/(tn + fp)
    buggyF1 = 2*buggyPrecision*buggyRecall/(buggyPrecision + buggyRecall)
    cleanF1 = 2*cleanPrecison*cleanRecall/(cleanPrecison + cleanRecall)
    acc = (tp+tn)/(tp+tn+fp+fn)
    return tp,tn,fp,fn,acc,buggyRecall,buggyPrecision,buggyF1,cleanRecall,cleanPrecison,cleanF1


clf = svm.LinearSVC(C=.1,class_weight='balanced') # Linear SVM is faster
clf.fit(x_train, y_train)
predictions = [int(x) for x in clf.predict(x_test)]
tp,tn,fp,fn,acc,buggyRecall,buggyPrecision,buggyF1,cleanRecall,cleanPrecison,cleanF1 = accuracy(predictions,y_test)
print 'accuracy:',acc
print 'buggy F1:',buggyF1,'buggy recall:',buggyRecall,'buggy precision:',buggyPrecision
print 'clean F1:',cleanF1,'clean recall:',cleanRecall,'clean precision:',cleanPrecison
print 'tp:',tp,'tn:',tn,'fp:',fp,'fn:',fn

'''
bestAcc = 0
bestCLF = None
for c in 0.01, 0.1, 1, 10, 100:
    clf = svm.LinearSVC(C = c) # Linear SVM is faster
    clf.fit(x_train, y_train)
    predictions = [int(x) for x in clf.predict(x_test)]
    tp,tn,fp,fn,acc,buggyRecall,buggyPrecision,buggyF1,cleanRecall,cleanPrecison,cleanF1 = accuracy(predictions,y_test)
    print 'accuracy:',acc
    print 'buggy F1:',buggyF1,'buggy recall:',buggyRecall,'buggy precision:',buggyPrecision
    print 'clean F1:',cleanF1,'clean recall:',cleanRecall,'clean precision:',cleanPrecison
    print 'tp:',tp,'tn:',tn,'fp:',fp,'fn:',fn
    if acc > bestAcc:
        bestAcc = acc
        bestCLF = clf
    print("C = " + str(c) + ": validation accuracy = " + str(acc))
'''
