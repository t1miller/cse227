import commitExtractor as ce
from commit import Commit
from commit import BOWHelper
from collections import defaultdict
from collections import OrderedDict
import operator



commits = ce.getCommits()
bowhelper = BOWHelper()

#build source code add/remove corpus
corpusAdd,corpusRemove = bowhelper.buildCommitSourceCorpus(commits)

#build filename corpus
corpusFilename = bowhelper.buildFileNameCorpus(commits)

#build commit msg corpus
corpusMsg = bowhelper.buildCommitMsgCorpus(commits)

def featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,commit):
    f = []
    f += commit.featureHour()
    f += commit.featureDate()
    f += [ wordCountTuple[1] for wordCountTuple in bowhelper.bowCommitMsg(corpusMsg,commit)] 
    totalLinesChanged,totalLinesAdded,totalLinesDeleted = 0,0,0
    for cFile in commit.getFiles():
        totalLinesChanged += cFile.featureNumLinesChanged()
        totalLinesAdded += cFile.featureNumLinesAdded()
        totalLinesDeleted += cFile.featureNumLinesDeleted()
    f.append(totalLinesChanged)
    f.append(totalLinesAdded)
    f.append(totalLinesDeleted)
    f.append(len(commit.getFiles()))
    f += [wordCountTuple[1] for wordCountTuple in bowhelper.bowFilename(corpusFilename,commit) ]
    bowAdded,bowRemoved = bowhelper.bowCommitSource(corpusAdd,corpusRemove,commit)
    f += [wordCountTuple[1] for wordCountTuple in bowAdded ]
    f += [wordCountTuple[1] for wordCountTuple in bowRemoved ]
    return f


print featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,commits[0])
