import commitExtractor as ce
from commit import Commit
from commit import BOWHelper
from collections import defaultdict
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


def loadCommits(path):
    data = []
    for i,filename in enumerate(sorted(os.listdir(path))):
        data.append(json.load(open(path+filename)))
        if i % 10000 == 0:
            print 'loaded ',i,' commits'
    return data


def parseCommitData(buggyHashes,data):
    commits = []
    for i,d in enumerate(data):
        sha = d['sha'][1:8]#only first 7 char of hash
        author = d['commit']['author']['name']
        msg = d['commit']['message']
        date = d['commit']['author']['date'].split('T')[0].replace("\"","")
        hour,minute,_,_ = d['commit']['author']['date'].split('T')[1].replace('Z','').split(':')
        diff = d['diff']
        isBuggy = buggyHashes[sha]
        commits.append(Commit(author,msg,sha,date,hour,minute,diff,isBuggy))
        if i % 1000 == 0:
            print 'parsed ',i,' commits'
    return commits

def parseBugs(path):
    buggyHash = defaultdict(int)
    for filename in os.listdir(path):
        data = json.load(open(path+filename))
        for h in data['blames']:
            buggyHash[h[:7]] = 1
    return buggyHash


buggyHashes = parseBugs('./data/bug_data/')
commitData = loadCommits('./data/commit_data/')
SAMPLE_SIZE = 3000
random.seed(23)
commitDataSample = random.sample(commitData,SAMPLE_SIZE)
commits = parseCommitData(buggyHashes,commitDataSample)

#build corpi
bowhelper = BOWHelper()
corpusAdd,corpusRemove,corpusCurrent = bowhelper.buildCommitSourceCorpus(commits)
corpusFilename = bowhelper.buildFileNameCorpus(commits)
corpusMsg = bowhelper.buildCommitMsgCorpus(commits)
corpusAuthor = bowhelper.buildAuthorCorpus(commits)


def feature(corpusMsg,corpusFilename,corpusAdd,corpusRemove,corpusAuthor,commit):
    f = []
    f.append(1)
    f += commit.featureHour()
    f += commit.featureDate()
    f.append(commit.numLinesChanged) 
    f.append(len(commit.filenames))
    f += bowhelper.featureAuthor(corpusAuthor,commit)
    f += bowhelper.featureFilename(corpusFilename,commit)
    f += bowhelper.featureCommitMsg(corpusMsg,commit)
    bowAdded,bowRemoved,bowCurrent = bowhelper.featureCommitSource(corpusAdd,corpusRemove,corpusCurrent,commit)
    f += bowAdded
    f += bowRemoved
    f += bowCurrent
    return f

#print feature(corpusMsg,corpusFilename,corpusAdd,corpusRemove,corpusAuthor,commits[0])

print 'building feature vectors'
x = []
for i,c in enumerate(commits):
    x.append(feature(corpusMsg,corpusFilename,corpusAdd,corpusRemove,corpusAuthor,c))
    if i % 100 == 0:
        print 'completed ',i,' features'


x_train = x[:len(x)/3]
x_test = x[len(x)/3:2*len(x)/3]
x_valid = x[2*len(x)/3:]
print 'building labels'
y = [int(c.isBuggy) for c in commits]
y_train = y[:len(y)/3]
y_test = y[len(x)/3:2*len(x)/3]
y_valid = y[2*len(y)/3:]


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

#Test set 
predictions = [int(x) for x in clf.predict(x_test)]
tp,tn,fp,fn,acc,buggyRecall,buggyPrecision,buggyF1,cleanRecall,cleanPrecison,cleanF1 = accuracy(predictions,y_test)
print 'test set'
print 'accuracy:',acc
print 'buggy F1:',buggyF1,'buggy recall:',buggyRecall,'buggy precision:',buggyPrecision
print 'clean F1:',cleanF1,'clean recall:',cleanRecall,'clean precision:',cleanPrecison
print 'tp:',tp,'tn:',tn,'fp:',fp,'fn:',fn

#Validation set
predictions = [int(x) for x in clf.predict(x_valid)]
tp,tn,fp,fn,acc,buggyRecall,buggyPrecision,buggyF1,cleanRecall,cleanPrecison,cleanF1 = accuracy(predictions,y_valid)
print 'valid set'
print 'accuracy:',acc
print 'buggy F1:',buggyF1,'buggy recall:',buggyRecall,'buggy precision:',buggyPrecision
print 'clean F1:',cleanF1,'clean recall:',cleanRecall,'clean precision:',cleanPrecison
print 'tp:',tp,'tn:',tn,'fp:',fp,'fn:',fn



''' This is for tuning SVM params 
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
