import requests
import comics
import json
import datetime

# im: list[comics.Comic] = []
i = 0
while True:
	i += 1
	if i == 404:
		comic = comics.Comic.create(title="404", date=datetime.date(2008, 4, 1), comicname="xkcd", number=404, author="Randall Munroe")
	else:
		data = json.loads(requests.get(f"https://xkcd.com/{i}/info.0.json").text)
		title = data["title"]
		date = datetime.date(int(data["year"]), int(data["month"]), int(data["day"]))
		img = b"png." + requests.get(data["img"]).content
		alt = data["alt"]
		comic = comics.Comic.create(title=title, date=date, comicname="xkcd", number=i, author="Randall Munroe", images=[img], alt=alt)
	# im.append(comic)
	f = open(f"comics/xkcd{i}.json", "w")
	f.write(comic.save())
	f.close()
	print(f"done {i}")
