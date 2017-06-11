driverPath='./chromedriver.exe'
driverProfilePathPrefix='./Scraper'
folder='./data/24hCrawl1/'
suffix='_Top1.txt'
threads=6
max=2000
curday='2017-06-11'
nextday='2017-06-12'
nextnextday='2017-06-13'
start=23

for i in {0..47};
do
	let hours=$start+$i
	echo $hours
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