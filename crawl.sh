driverPath='./chromedriver.exe'
driverProfilePathPrefix='./Scraper'
folder='./data/24hCrawl1/'
suffix='_Top5.txt'
threads=6
max=2000
curday='2017-06-13'
nextday='2017-06-14'
nextnextday='2017-06-15'
start=0

for i in {0..47};
do
	let hours=$start+$i
	if (( $hours > 47 )); then
		day=$nextnextday
	elif (( $hours > 23 )); then
		day=$nextday
	else
		day=$curday
	fi
	let hours=$hours%24
	cmd="python LocationCrawler.py -fromDir $folder $suffix -t 1 -max $max -d "$day"T"$hours":00:00 -threads $threads -drv $driverPath -drvProfile $driverProfilePathPrefix"
	echo $cmd
	$cmd
done