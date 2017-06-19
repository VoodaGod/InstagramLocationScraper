import os
import sys
from collections import deque

'''gets time offset from utc from file in argv[1] (<city>\t<offset) and takes "<city>AvgCounts.txt" files in dir argv[2], adjusts them by offset & writes them to "<city>AvgCountsTimeZoned.txt"'''

def main():
	timeZoneDict = {}
	lines = getLinesInFile(sys.argv[1]) #file with "<citiy>\t<offset"
	for line in lines:
		split = line.split("\t")
		timeZoneDict[split[0]] = int(float(split[1]))

	root = sys.argv[2] #directory with "<city>AvgCounts.txt" files
	for __, __, rootFiles in os.walk(root):
		for file in rootFiles:
			if(not file.endswith("AvgCounts.txt")):
				continue
			print(file)
			city = file.replace("AvgCounts.txt", "")
			timeZoneOffset = timeZoneDict[city]
			lines = getLinesInFile(os.path.join(root, file))
			for i in range(24):
				lines[i] = lines[i].split("\t")[1] #get counts, sorted by UTC
			counts = deque(lines)
			counts.rotate(timeZoneOffset) #rotate by offset
			#write to file
			fixedFile = open(os.path.join(root, (city + "AvgCountsTimeZoned.txt")), "w")
			for i in range(24):
				fixedFile.write(str(i).zfill(2) + ":00:00\t" + counts[i] + "\n")
			fixedFile.close()



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
