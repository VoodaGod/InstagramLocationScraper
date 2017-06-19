import os
import sys

'''gets average postcount of all locations in a city at all hours & writes them to a file'''

ERROR_INDICATOR = -9999

def main():
	averageList = [0 for x in range(24)]
	root = sys.argv[1]
	for __, subDirs, __ in os.walk(root): #get subDirs
		for subDir in subDirs:
			if(not subDir.endswith("_Postcounts")): #for each dir ending in "_Postcounts"
				continue
			print(subDir)
			subRoot = os.path.join(root, subDir)
			for __, __, subFiles in os.walk(subRoot): #get subFiles
				for i in range(24): #reset timeList
					averageList[i] = 0
				for subFile in subFiles:
					if(not subFile.endswith("Postcounts.txt")): #for each file ending in "_Postcounts.txt"
						continue
					lines = getLinesInFile(os.path.join(subRoot, subFile))
					for i in range(24): #for each hour
						counts = []
						for line in lines: #look for all lines matching hour
							if(str(i).zfill(2) + ":00:00") in line:
								count = int(line.split("\t")[1])
								if(count != ERROR_INDICATOR):
									counts.append(count) #add count at hour in current line to counts
						#remove outliers & add average
						counts.remove(min(counts))
						counts.remove(max(counts))
						averageList[i] += sum(counts) / len(counts)
			#write to file
			avgCountFile = open(subRoot.replace("Postcounts", "AvgCounts.txt"), "w")
			lines = []
			for i in range(24):
				lines.append(str(i).zfill(2) + ":00:00\t" + str(round(averageList[i], 2)) + "\n")
			avgCountFile.writelines(lines)
			avgCountFile.close()



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