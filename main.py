import commitExtractor as ce
from commit import Commit
from commit import BOWHelper
from collections import defaultdict
from collections import OrderedDict
import operator



commits = ce.getCommits()
bowhelper = BOWHelper()

corpusAdd,corpusRemove = bowhelper.buildCommitCorpus(commits)
bowAdded,bowRemoved = bowhelper.bowCommit(corpusAdd,corpusRemove,commits[0])

corpusFilename = bowhelper.buildFileNameCorpus(commits)
bowFilename = bowhelper.bowFilename(corpusFilename,commits[0])



