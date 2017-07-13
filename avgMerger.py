import os
import sys


def main():
	root = sys.argv[1]
	merged = []
	for i in range(25):
		merged.append("")
	for __, __, subFiles in os.walk(root):
		for subFile in subFiles:
			if (not subFile.endswith("AvgCountsTimeZoned.txt")):
				continue
			merged[0] += "\t" + subFile.replace("_AvgCountsTimeZoned.txt", "")
			lines = getLinesInFile(os.path.join(root, subFile))
			for i in range(1, 25):
				 merged[i] += "\t" + lines[i-1].split("\t")[1]
		break
	for i in range(25):
		merged[i] += "\n"
	file = open(os.path.join(root, "merged.txt"), "w")
	file.writelines(merged)
	file.close()


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