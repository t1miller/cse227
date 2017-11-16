import requests
import json
from commit import Commit

gitClientID = "077392bc8da10af70548" 
gitClientSecret = "84af78d9b0f9e3ad1936175641dc44e953da8fd5"



def getSavedCommits():
	try:
		with open('commits.txt','r') as infile:
			commits = json.load(infile)
		return commits
	except: 
		print 'Error loading saved file'
		return None

def saveCommits(commits):
	with open('commits.txt', 'w') as outfile:
		json.dump(commits, outfile)

'''
Git API v3 returns 30 commits by default
100 is the max value
https://developer.github.com/v3/
'''
def getCommits(numberOfCommits=100,updateCommitCache=False):
	commits = []
	commitsJSON = getSavedCommits()
	if updateCommitCache or not commitsJSON:
		url = 'https://api.github.com/repos/mozilla/gecko-dev/commits' \
				+"?client_id="+gitClientID \
				+"&client_secret="+gitClientSecret \
				+"&per_page="+str(numberOfCommits)
		response = requests.get(url).json()
		shas = [r['sha'] for r in response]
		commitsJSON = [getDetailedCommit(sha) for sha in shas]
		commits = [Commit(c) for c in commitsJSON]
		saveCommits(commitsJSON)
	else:
		commits = [Commit(c) for c in commitsJSON]
	return commits

def getDetailedCommit(sha):
	return requests.get('https://api.github.com/repos/mozilla/gecko-dev/commits/'+sha+"?client_id="+gitClientID+"&client_secret="+gitClientSecret).json()



