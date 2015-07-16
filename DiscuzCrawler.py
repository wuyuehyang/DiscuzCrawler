import urllib.request
import gzip
import re
import http.cookiejar
import hashlib
import os
import time

class postParser:
	postContentList, authorList = [], []

	def feed(self, pageData):
		self.postContentList = []
		self.authorList = []
		postContentWithTDTagsPattern = re.compile(r'<td class="t_msgfont" id="postmessage_\d+">(?:.|[\r\n])*?</td>|<div class="locked">(?:.|[\r\n])*?</div>')
		postContentTDTagsPattern = re.compile(r'<td class="t_msgfont" id="postmessage_\d+">|</td>|<img[^>]*>|<div class="locked">|</div>')
		postContentListWithTDTags = postContentWithTDTagsPattern.findall(pageData)
		self.postContentList = postContentTDTagsPattern.sub('', repr(postContentListWithTDTags))

		authorWithTDTagsPattern = re.compile(r'<td class="postauthor" rowspan=(?:.|[\r\n])*?>(?:.|[\r\n])*?>(?:.|[\r\n])*?>(?:.|[\r\n])*?</a>')
		authorTDTagsPattern = re.compile(r'<td class="postauthor" rowspan=(?:.|[\r\n])*?>(?:.|[\r\n])*?>(?:.|[\r\n])*?>|</a>')
		authorListWithTDTags = authorWithTDTagsPattern.findall(pageData)
		self.authorList = authorTDTagsPattern.sub('', repr(authorListWithTDTags))

		titleWithTagsPattern = re.compile(r'<title>.+</title>')
		titleTagPattern = re.compile(r'<title>|</title>')
		titleWithTags = titleWithTagsPattern.findall(pageData)
		self.title = titleTagPattern.sub('', titleWithTags[0])
	def getPostContentList(self):
		postContentList = eval(self.postContentList)
		postContentList.reverse()
		return postContentList
	def getAuthorList(self):
		self.authorList = eval(self.authorList)
		return self.authorList
	def getTitle(self):
		return self.title
	def clean(self):
		self.postContentList = []
		self.authorList = []

def getPagingListFromSearchResult(pageData):
	pagingListWithTagsPattern = re.compile(r'<a href="search.php\?searchid=[^>]+page=\d')
	pagingListWithTags = pagingListWithTagsPattern.findall(pageData)
	pagingListTagsPattern = re.compile(r'<a href="|amp;')
	pagingList = pagingListTagsPattern.sub('', repr(pagingListWithTags))	
	pagingList = list(set(eval(pagingList)))
	return pagingList

def getPostHRefListFromSearchResult(pageData):
	postHRefWithTagsPattern = re.compile(r'viewthread.php\?tid=[0-9]+&amp')
	postHRefListWithTags = postHRefWithTagsPattern.findall(pageData)
	postHRefTagsPattern = re.compile(r'&amp')
	postHRefList = postHRefTagsPattern.sub('', repr(postHRefListWithTags))
	postHRefList = list(set(eval(postHRefList)))
	return postHRefList

def getPageData(op):
	pageData = op.read()
	try:
		pageData = gzip.decompress(pageData)
	except:
		print('unable to decompress')
	try:
		pageData = pageData.decode('gbk')
		return pageData
	except:
		print('error decoding page with gbk.')
		file = open(os.getcwd() + '//error.html', 'ab')
		file.write(pageData)
		file.close()
		return 'error'

def getformhash(pageData): 
	formhash = re.compile('name="formhash" value="(.*)"', flags=0)
	strlist = formhash.findall(pageData)
	return strlist[0]

def getOpener(head):
	cj = http.cookiejar.CookieJar()
	pro = urllib.request.HTTPCookieProcessor(cj)
	opener = urllib.request.build_opener(pro)
	header = []
	for key, value in head.items():
		elem = (key, value)
		header.append(elem)
	opener.addheaders = header
	return opener

def generateMD5(input):
	output = hashlib.md5(input.encode('utf-8')).hexdigest()
	print(output)
	return output

url = '' #like 'http://www.??.com/forum/'
host = ''  #like 'www.??.com'
username = ''
password = ''
SearchName = ''

header = {
	'Host': host,
	'Connection': 'keep-alive',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.61 Safari/537.36',
	'HTTPS': '1',
	'Referer': url,
	'Accept-Encoding': 'gzip, deflate, sdch',
	'Accept-Language': 'en-US,en;q=0.8',
}
mainOpener = getOpener(header)
print('mainOpener initialized with parameters')

print('now logging in')
urlLogin = url + 'logging.php?action=login'
pageData = getPageData(mainOpener.open(urlLogin))
formhash = (getformhash(pageData))

urlLoginSubmit = urlLogin + '&loginsubmit=yes&inajax=1'
loginHeader = {
	'formhash': formhash,
	'referer': url,
	'loginfield': 'username',
	'username': username,
	'password': generateMD5(password),
	'questionid': '0',
	'answer': '',
	'loginsubmit': 'true',
	'cookietime': '2592000'
}
loginHeaderEncoded = urllib.parse.urlencode(loginHeader).encode()
pageData = getPageData(mainOpener.open(urlLoginSubmit, loginHeaderEncoded))
print('logged in successfully')

print('now searching for the first page of result')
SearchName = SearchName.encode('gbk')
urlSearch = url + "search.php?srchtxt="
searchHeader = {
	'searchtype': 'title',
	'searchsubmit': 'true',
	'st': 'on',
	'srchuname': SearchName,
	'srchfilter': 'all',
	'srchfrom': '0',
	'before': '',
	'orderby': 'dateline',
	'ascdesc': 'desc',
	'srchfid%5B0%5D': 'all'
}
searchHeaderEncoded = urllib.parse.urlencode(searchHeader).encode()
pageData = getPageData(mainOpener.open(urlSearch, searchHeaderEncoded))
print('first page of search result was transported successfully')

pageList = getPagingListFromSearchResult(pageData)
pageListVisited = []
postHRefList = []

print('Now start paging looping')
while 1:
	print('%d pages in pageList' % len(pageList))
	if len(pageList) == 0:
		print('Paging Looping stopped')
		break
	pageTemp = pageList.pop()
	print('Poped pageTemp: %s' % pageTemp)
	pageListVisited.append(pageTemp)
	urlTemp = url + pageTemp
	time.sleep(3)
	pageData = getPageData(mainOpener.open(urlTemp))
	pagingInf = getPagingListFromSearchResult(pageData)
	for item in pagingInf:
		if not (item in pageList or item in pageListVisited):
			pageList.append(item)
			print("%s item is appended to pageList" % item)
	postHRefList = postHRefList + getPostHRefListFromSearchResult(pageData)
	
postHRefList = list(set(postHRefList))
postHRefList.sort()
postParser = postParser()
fileOutput = open(os.getcwd() + '//output.html', 'w', encoding = 'utf-8')
fileOutput.write('<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n<style type="text/css">\nh1{font-size:18px;}\nh2{font-size:14px;}\n</style>\n</head>\n<body>\n')

while 1:
	print('%d posts in postHRefList' % len(postHRefList))
	if len(postHRefList) == 0:
		print('post looping stopped')
		break
	postHRefTemp = postHRefList.pop()
	print('now dealing with post:' + postHRefTemp)
	pageData = getPageData(mainOpener.open(url + postHRefTemp))
	if pageData == 'error':
		print('error handling page:' + postHRefTemp)
		continue
	postParser.feed(pageData)
	postContentList = postParser.getPostContentList()
	authorList = postParser.getAuthorList()
	fileOutput.write('<h1>')
	fileOutput.write(postParser.getTitle())
	fileOutput.write('</h1>\n<br />')

	for author in authorList:
		fileOutput.write('\n<h2>')
		fileOutput.write(author)
		fileOutput.write('：</h2>\n<p>')
		fileOutput.write(postContentList.pop())
		fileOutput.write('\n</p></hr>\n')
	fileOutput.write('<hr />')
	time.sleep(5)

fileOutput.write('\n</body>\n</html>')
fileOutput.close()
