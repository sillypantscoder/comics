import requests
from pyquery import PyQuery as pq
import datetime
import comics

sess = requests.Session()
sess.headers.update({'user-agent': 'tapas-dl'})

comicName = "Low-quality-comics-with-no-concerning-order-probably"

homePageRequest = sess.get('https://tapas.io/series/' + comicName)
homePage = pq(homePageRequest.text)

print("Querying home page...")

comicName: str = homePage('.center-info__title.center-info__title--small').text() # type: ignore
comicAuthor: str = homePage('div.viewer-section.viewer-section--episode a.name').text() # type: ignore
seriesID = homePage('.subscribe-btn').attr('data-id')

print("Finding episodes...")

episodes = pq(sess.get(f"https://tapas.io/series/{seriesID}/episodes?page=1&sort=OLDEST&max_limit=99999999").json()['data']['body'])
esList: list[int] = []
for episode in episodes('[data-permalink*="/episode/"]'):
	esList.append(int(episode.attrib['data-permalink'][episode.attrib['data-permalink'].rfind('/') + 1:]))

print("Found", len(esList), "episodes")

def processEpisode(pagen: int, pageID: int):
	print("Beginning download of comic #" + str(pagen + 1) + " of " + str(len(esList)))
	pageRequest = sess.get(f'https://tapas.io/episode/{pageID}')
	pageHTML = pq(pageRequest.text)
	date: datetime.date | None = None
	try:
		date_text: str = pageHTML.find('.viewer__header .date')[0].text
		date = datetime.datetime.strptime(date_text, '%b %d, %Y')
	except: pass
	title: str | None = None
	try:
		title = pageHTML.find('.viewer__header .title')[0].text
	except: pass
	comment: str | None = None
	try:
		comment = pageHTML.find('.js-episode-story')[0].text_content().replace("\n", "<br>")
	except: pass
	images: list[bytes] = []
	i = 0
	for img in pageHTML('.content__img'):
		origSrc: str = pq(img).attr('data-src') # type: ignore
		imgno = origSrc[origSrc.rfind('.'):]
		newname = str(pagen + 1) + "-" + str(i + 1) + imgno
		print("Downloading image " + newname)
		imgRequest = sess.get(origSrc)
		images.append(b"jpg." + imgRequest.content)
		i += 1
	print("Finished downloading comic #" + str(pagen + 1))
	# Assemble comic object
	comic = comics.Comic.create(title=title, date=date, comicname=comicName, number=pagen + 1, author="Nightingale", images=images, description=comment)
	f = open(f"comics/lqc{pagen + 1}.json", "w")
	f.write(comic.save())
	f.close()
	# Finish
	print("\n")

for pagen, pageID in enumerate(esList):
	processEpisode(pagen, pageID)
