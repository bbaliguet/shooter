# PYTHON 3
# follow links on target website
import urllib.request, random, re, threading, time, sys, http.client

# INIT
target = sys.argv[1]
print("SHOOTING " + target)
nextUrls = set([target])
doneUrls = set([])
pathHistory = {}
pathHistory[target] = ""

# uncomment to turn HTTP debugging on
# http.client.HTTPConnection.debuglevel = 1

# install a cookie processor to automatically request with previoulsy set cookies
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
urllib.request.install_opener(opener)

lock = threading.Lock()
threads = 0
fileName =  re.sub("[^\w]", "_", target)
if len(fileName)>30:
	fileName = fileName[0:30]
logName = time.strftime("logs/" + fileName + "_%d%b%Y_%Hh%M.csv", time.gmtime())
print("log in " + logName)



def write(code, duration, url):
	logs = open(logName,"a")
	history = "" if code == "200" else pathHistory[url]
	logs.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(str(len(doneUrls)), str(len(nextUrls)), str(threads), code, duration, url, history))
	logs.close()

def extractor(content, url):
	pattern = re.compile("href=['\"][^'\"]+['\"]", re.IGNORECASE)	
	matches = pattern.findall(content)

	queryString = url.find("?")
	base = url
	baseSlash = url
	if queryString != -1:
		base = url[0:queryString]
	lastSlash = url.rfind("/")
	if lastSlash != -1:
		baseSlash = url[0:lastSlash + 1]

	for match in matches:
		pathMatch=match[6:len(match)-1]
		if pathMatch[0:4] != 'http' and pathMatch[0:2] != "//" and pathMatch[0] != "#":
			if pathMatch[0] == "?":
				newUrl = base + pathMatch
			elif pathMatch[0] == "/":
				newUrl = target + pathMatch
			else:
				newUrl = baseSlash + pathMatch
			if not newUrl in doneUrls:
				nextUrls.add(newUrl)
				#save path
				pathHistory[newUrl] = "{} > {}".format(pathHistory[url], newUrl)

def shoot():
	global threads
	startTime = time.time()
	
	lock.acquire()
	threads += 1
	url = nextUrls.pop()
	print(">>" + url)
	doneUrls.add(url)
	lock.release()
	
	req = urllib.request.Request(url)
	target = None
	try:
		target = urllib.request.urlopen(req)
	except urllib.error.HTTPError as e:
		lock.acquire()
		write(str(e.code), 0, url)
		threads -= 1
		lock.release()

	# no error : search for links
	if target != None:
		content = str(target.read())
		target.close()
		duration = round(time.time() - startTime, 3)
		
		lock.acquire()
		extractor(content, url)
		threads -= 1
		write("200", str(duration), url)
		lock.release()

#shoot every 0.2s
def shooter():
	if len(nextUrls) > 0 or threads > 0:	
		if len(nextUrls) > 0:
			threading.Thread(None, shoot).start()
		threading.Timer(0.2,shooter).start()

# start !
shooter()