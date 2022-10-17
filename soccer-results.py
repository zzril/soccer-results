#! /usr/bin/env python3

# --------

"""
MIT License

Copyright (c) 2022 zzril

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# --------

import argparse
import requests
import sys

# --------

url = "https://www.openligadb.de/api/getmatchdata/bl1"
headers = {'Accept': 'application/json'}

maxMinuteDigits = 2

# --------

# general functions for performing the api request and querying its returned object:

def getAllMatches():
	try:
		response = requests.get(url, headers=headers)
		return response.json()
	except requests.exceptions.RequestException as e:
		sys.exit("Network error.")

def getTeamNames(match):
	return tuple(match.get(teamNumber).get('TeamName') for teamNumber in ('Team1', 'Team2'))

def getScore(match):
	resultsList = match.get('MatchResults')
	if len(resultsList) == 0:
		return (0, 0)
	currentMatchResult = resultsList[0]
	return tuple(currentMatchResult.get(teamNumber) for teamNumber in ('PointsTeam1', 'PointsTeam2'))

def getGoalsList(match):
	return match.get('Goals')

def getNewScore(goal):
	return tuple(goal.get(side) for side in ('ScoreTeam1', 'ScoreTeam2'))

def getGoalsTuple(match):

	goalsList = getGoalsList(match)

	(homeGoals, awayGoals) = ([], [])
	(currentHomeScore, currentAwayScore) = (0, 0)

	for goal in goalsList:
		(newHomeScore, newAwayScore) = getNewScore(goal)
		# if home goal:
		if newHomeScore == currentHomeScore + 1 and newAwayScore == currentAwayScore:
			homeGoals.append(goal)
			# append None to the other list, for nicer formatting:
			awayGoals.append(None)
			currentHomeScore += 1
		# if away goal:
		elif newHomeScore == currentHomeScore and newAwayScore == currentAwayScore + 1:
			awayGoals.append(goal)
			# append None to the other list, for nicer formatting:
			homeGoals.append(None)
			currentAwayScore += 1
		# goals not ordered correctly:
		else:
			return None

	return (homeGoals, awayGoals)

def getMinute(goal):
	return goal.get('MatchMinute')

def getGoalGetter(goal):
	return goal.get('GoalGetterName')

def isPenalty(goal):
	return goal.get('IsPenalty') is True

def isOwnGoal(goal):
	return goal.get('IsOwnGoal') is True

def hasFinished(match):
	return match.get('MatchIsFinished')

def hasBegun(match):
	return len(match.get('MatchResults')) > 0

# methods for filtering out games by specific teams:

def hasTeam(match, teamNameSubstring):
	teamNames = [teamName.casefold() for teamName in getTeamNames(match)]
	return any(teamNameSubstring.casefold() in teamName for teamName in teamNames)

def getMatchesByTeamName(teamNameSubstring, allMatches=None):
	if allMatches is None:
		allMatches = getAllMatches()
	if teamNameSubstring is None:
		return allMatches
	else:
		return [match for match in allMatches if hasTeam(match, teamNameSubstring)]

# string manipulating / printing functions:

def getRunningStateGerman(match):
	return "beendet" if hasFinished(match) else ("läuft" if hasBegun(match) else "noch nicht gestartet")

def teamNamesToString(teamNames):
	return f"{teamNames[0]} - {teamNames[1]}"

def scoreToString(score):
	if score is None:
		return None
	return f"{score[0]} : {score[1]}"

def goalToString(goal):
	if goal is None:
		return ""
	minute = str(getMinute(goal)).rjust(maxMinuteDigits)
	playerName = getGoalGetter(goal)
	goalString = f"{minute}' {playerName}"
	if isPenalty(goal):
		goalString += " (P)"
	if isOwnGoal(goal):
		goalString += " (OG)"
	return goalString

def printGoals(goalsTuple, newline=False):

	if goalsTuple is None:
		return 0

	(homeGoals, awayGoals) = tuple([goalToString(goal) for goal in teamsGoalList] for teamsGoalList in goalsTuple)

	numGoals = len(homeGoals)
	if len(awayGoals) != numGoals or numGoals == 0:
		return 0

	minWidth = 15
	spaceBetween = 5

	(maxHomeColumnWidth, maxAwayColumnWidth) = tuple((max(minWidth, max([len(goalString) for goalString in teamsGoalList]) + spaceBetween)) for teamsGoalList in (homeGoals, awayGoals))

	for i in range(numGoals):
		print(homeGoals[i].ljust(maxHomeColumnWidth) + awayGoals[i].ljust(maxAwayColumnWidth))

	if newline:
		print()
	return numGoals

def printSeparator():
	print("---", end='\n\n')

def printHeadline():
	headline = "Aktuelle Bundesliga-Spielstände:"
	headlineLength = len(headline)
	underline = "=" * headlineLength
	print(f"\n{headline}\n{underline}\n")

# --------

def updateAll(teamNameSubstring=None):
	allMatches = getAllMatches()
	if teamNameSubstring is None:
		printHeadline()
	else:
		allMatches = getMatchesByTeamName(teamNameSubstring, allMatches)
	firstIteration = True
	for match in allMatches:
		if firstIteration:
			firstIteration = False
		else:
			printSeparator()
		print(teamNamesToString(getTeamNames(match)), end='\n\n')
		print(scoreToString(getScore(match)), end='\n\n')
		printGoals(getGoalsTuple(match), newline=True)
		print(f"({getRunningStateGerman(match)})", end='\n\n')

# --------

def parseArgs():
	generalDescription = "Print all scores from the current day of play in the German soccer Bundesliga to stdout."
	teamDescription = "show only games from teams with names containing TEAM"
	parser = argparse.ArgumentParser(description=generalDescription)
	parser.add_argument('--team', help=teamDescription)
	return vars(parser.parse_args())

# --------

def main():

	arguments = parseArgs()
	if 'team' in arguments:
		updateAll(arguments['team'])
	else:
		updateAll()

# --------

if __name__ == "__main__":
	main()

# --------


