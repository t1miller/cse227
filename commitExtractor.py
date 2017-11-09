import requests
import json
from commit import Commit

gitClientID = "077392bc8da10af70548" 
gitClientSecret = "84af78d9b0f9e3ad1936175641dc44e953da8fd5"

def getListCommits():
	url = 'https://api.github.com/repos/mozilla/gecko-dev/commits' \
			+"?client_id="+gitClientID+"&client_secret="+gitClientSecret
	response = requests.get(url).json()
	shas = []
	for r in response:
		shas.append(r['sha'])
	return shas

def getDetailedCommit(sha):
	return requests.get('https://api.github.com/repos/mozilla/gecko-dev/commits/'+sha+"?client_id="+gitClientID+"&client_secret="+gitClientSecret).json()

def saveCommits(commits):
	with open('commits.txt', 'w') as outfile:
		json.dump(commits, outfile)

def getSavedCommits():
	try:
		with open('commits.txt','r') as infile:
			commits = json.load(infile)
		return commits
	except: 
		print 'Error loading saved file'
		return None


'''
Check to see if we have commits saved on disk
'''
commitsJson = getSavedCommits()
if not commitsJson:
	commitsJson = [getDetailedCommit(sha) for sha in getListCommits()]
	saveCommits(commitsJson)

'''
Convert json to Commit
'''
commits = [ Commit(c) for c in commitsJson]
print commits[0]
#for commitJson in commitsJson:
#	commits.append(Commit(commitJson))

#print json.dumps(commits[1], indent=4, sort_keys=True)
