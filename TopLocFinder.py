import os
import sys


def main():
	locDict = {}
	numTop = int(sys.argv[2])
	for root, subDirs, __ in os.walk(sys.argv[1]):
		for subDir in subDirs:
			if(not subDir.endswith("_Postcounts")):
				continue
			print(subDir)
			for subRoot, __, subFiles in os.walk(os.path.join(root, subDir)):
				for subFile in subFiles:
					for line in getLinesInFile(os.path.join(subRoot, subFile)):
						count = line.split("\t")[-1]
						locDict[subFile.replace("Postcounts.txt", "")] =  count
				break
			sortedLocs = sorted(locDict.items(), key=lambda x: int(x[1]), reverse=True)
			topFile = open((os.path.join(root, subDir).replace("_Postcounts", "_Top") + str(numTop) + ".txt"), "w")
			topLocs = []
			for i in range(min(len(sortedLocs), numTop)):
				topLocs.append(sortedLocs[i][0].replace("_", "/") + "\n")
			topFile.writelines(topLocs)
			locDict.clear()
		break


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
