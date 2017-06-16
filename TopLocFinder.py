import os
import sys

''' Script to find top N locations from files in folders, both ending with "_Postcounts", in DIR
	Usage: TopLocFinder.py DIR N   eg. TopLocFinder.py ./data/ 10'''

def main():
	locDict = {}
	numTop = int(sys.argv[2])
	root = sys.argv[1]
	for __, subDirs, __ in os.walk(root): #get subDirs
		for subDir in subDirs:
			if(not subDir.endswith("_Postcounts")): #for each dir ending in "_Postcounts"
				continue
			print(subDir)
			subRoot = os.path.join(root, subDir)
			for __, __, subFiles in os.walk(subRoot): #get subFiles
				for subFile in subFiles:
					if(not subFile.endswith("Postcounts.txt")): #for each file ending in "_Postcounts.txt"
						continue
					count = 0
					for line in getLinesInFile(os.path.join(subRoot, subFile)): #add number of posts in each timestamp
						count += int(line.split("\t")[-1])
					locDict[subFile.replace("Postcounts.txt", "")] =  count #store location & sum of postcounts
			sortedLocs = sorted(locDict.items(), key=lambda x: x[1], reverse=True) #sort by postcount, descending
			topFile = open((subRoot.replace("_Postcounts", "_Top") + str(numTop) + ".txt"), "w")
			topLocs = []
			for i in range(min(len(sortedLocs), numTop)): #write top locations to file "CITY_TopN.txt"
				topLocs.append(sortedLocs[i][0].replace("_", "/") + "\n")
			topFile.writelines(topLocs)
			topFile.close()
			locDict.clear()


def getLinesInFile(filePath):
	lines = []
	try:
		file = open(filePath, "r")
	except FileNotFoundError:
		print("File not found")
		return lines
	else:
		lines.append(file.readline().strip('\n'))
		while(lines[-1] != ""):
			lines.append(file.readline().strip('\n'))
		lines.pop()
		file.close()
	return lines


main()
