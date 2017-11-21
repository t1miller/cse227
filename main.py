import commitExtractor as ce
from commit import Commit
from commit import BOWHelper
from collections import defaultdict
from collections import OrderedDict
import operator
from sklearn.neighbors import NearestNeighbors
import numpy as np




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
    f.append(1)
    f += commit.featureHour()
    f += commit.featureDate()
    changed,added,deleted = commit.getNumLinesChangedAllFiles()
    f.append(changed)
    f.append(added)
    f.append(deleted)
    f.append(len(commit.getFiles()))
    f += [wordCountTuple[1] for wordCountTuple in bowhelper.bowFilename(corpusFilename,commit)]
    f += [ wordCountTuple[1] for wordCountTuple in bowhelper.bowCommitMsg(corpusMsg,commit)] 
    bowAdded,bowRemoved = bowhelper.bowCommitSource(corpusAdd,corpusRemove,commit)
    f += [wordCountTuple[1] for wordCountTuple in bowAdded ]
    f += [wordCountTuple[1] for wordCountTuple in bowRemoved ]
    return f




x = featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,commits[1])
print x
''' K NearestNeighbors
x_train = [featureBuilder(corpusMsg,corpusFilename,corpusAdd,corpusRemove,c) for c in commits]
x_train_np = np.array(x_train)
nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(x_train)
distances, indices = nbrs.kneighbors(x_train)
for k in indices[:,1]:
    print commits[k]
'''