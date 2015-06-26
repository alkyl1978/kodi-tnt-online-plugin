import sys
import xbmcgui
import xbmcplugin
import CommonFunctions
import re
import urllib2
import urllib
import urlparse

common = CommonFunctions
common.plugin = 'TNT-Online.ru-0.5'

addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')

def debugMsg(msg):
	print('Debug - ' + msg)

def getPage(url):
	request = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0',})
	response = urllib2.urlopen(request)
	result = response.read()

	return result

def build_url(query):
	return base_url + '?' + urllib.urlencode(query)


mode = args.get('mode', None)

if mode is None:
	result = getPage('http://tnt-online.ru/programs.htm')
	program_div = common.parseDOM(result, "div", attrs = { 'id': 'all-videos' })
	show_link_elements = common.parseDOM(program_div[0], "b")

	for link_element in show_link_elements:
		show_url = common.parseDOM(link_element, "a", ret = 'href')
		show_title = common.parseDOM(link_element, "a")

		#Skip those we know is not working
		skipped_links = ['http://dom2.tnt-online.ru/', 'http://zkd.tnt-online.ru/', 'http://otkritii-pokaz.tnt-online.ru/', 'http://sladkaya-jizn.tnt-online.ru/', 'http://dom2.ru/', 'http://tnt-comedy.tnt-online.ru/', 'http://tnt-online.ru/kino/']
		if show_url[0] in skipped_links:
			continue

		url = build_url({'mode': 'show', 'url': show_url[-1]})
		li = xbmcgui.ListItem(show_title[0].encode('utf-8'), iconImage='DefaultFolder.png')
		#li = xbmcgui.ListItem(show_title[-1].encode('utf-8'), iconImage='DefaultFolder.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		

	xbmcplugin.endOfDirectory(addon_handle)
	
	
elif mode[0] == 'show':
	show_url = args.get('url', None)[0]
	show_page = args.get('page', 0)
	show_base_url = args.get('show_base_url', None)

	debugMsg('show: Fetching page {0}'.format(show_url))
	debugMsg('You are on page: ' + str(show_page))
	debugMsg('Base url: ' + str(show_base_url))

	if show_page == 0:
		#Fix for when Lazy russian programmers have missed the whole URL!
		#i.e /Dva-s-polovinoy-povara
		if show_url.startswith('/'):
			show_url = 'http://tnt-online.ru' + show_url

		result = getPage(show_url)
		show_base_url = show_url

		all_videos_div = common.parseDOM(result, "ul", attrs = { 'class': 'nav1' })

		if all_videos_div is None:
			debugMsg('show: Could not find ln1 div!')

		if 'series.html' in all_videos_div[0]:
			all_videos_link = 'series.html'
		elif 'seasons.html' in all_videos_div[0]:
			all_videos_link = 'seasons.html'
		else:
			all_videos_link = 'video.html'

		show_url = show_url + all_videos_link
		show_page = 1
	else:
		show_page = show_page[0]
		show_base_url = show_base_url[0]

	result = getPage(show_url + '?page=' + str(show_page) + '&mode=new&period=all')
	footer_nav = common.parseDOM(result, "div", attrs = {'id': 'main-block'})
	if 'btnprev' in footer_nav[0]:
		url = build_url({'mode': 'show', 'url': show_url, 'page': int(show_page) - 1, 'show_base_url': show_base_url})
		li = xbmcgui.ListItem('Previous...', iconImage='DefaultFolder.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	
	video_link_elements = common.parseDOM(result, "h4")

	for link_element in video_link_elements:
		episode_url = common.parseDOM(link_element, "a", ret = 'href')
		episode_title = common.parseDOM(link_element, "a")
		episode_url[-1] = episode_url[-1].lstrip('/')

		url = build_url({'mode': 'episode', 'url': show_base_url + episode_url[-1], 'title': episode_title})
		li = xbmcgui.ListItem(episode_title[-1].encode('utf-8'), iconImage='DefaultFolder.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	#if next_page_href is not None:
	if 'btnnext' in footer_nav[0]:
		url = build_url({'mode': 'show', 'url': show_url, 'page': int(show_page) + 1, 'show_base_url': show_base_url})
		li = xbmcgui.ListItem('Next...', iconImage='DefaultFolder.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		

	xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'episode':
	episode_url = args.get('url', None)[0]
	episode_title = args.get('title', None)[0]

	episode_page = getPage(episode_url)
	video_id_matches = re.search('val1=([0-9]+)', episode_page)
	video_id = video_id_matches.group(1)

	video_urls_page = 'http://out.pladform.ru/getVideo?pl=33413&social=none&dl=tnt-online.ru&videoid=' + video_id

	result = getPage(video_urls_page)
	print(video_urls_page)

	cdata_video_urls = common.parseDOM(result, "src")
	for quality_container in cdata_video_urls:
		video_urls = re.search('(http.*)]]', quality_container)
		url = video_urls.group(1) + '|User-Agent=Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0'
		quality = re.search('([0-9]+p)', url)

		li = xbmcgui.ListItem(quality.group(1), iconImage='DefaultVideo.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

	xbmcplugin.endOfDirectory(addon_handle)
