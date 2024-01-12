import requests
import re
import comics

number = 1
name = "kris-kapplesauce"

def loadLeft(info: dict[str, str | int]):
	global number
	global name
	number = info["number"]
	name = info["name"]
comics.get_left("explosm").ifPresent(loadLeft)

previous = [name]

while True:
	data = requests.get("https://explosm.net/comics/" + name).text
	matches = re.findall(r'<a href="/comics/([a-z\-0-9]+)#comic">', data)
	next = matches[1]
	desc: str | None = None
	img_matches = re.findall(r'href="(https://files.explosm.net/comics/[A-Za-z/0-9\-_\(\) !,\.]+\.(?:jpg|png|gif|PNG|JPG))[\?=a-zA-Z0-9]*?"/>', data)
	if len(img_matches) == 0:
		comics.log(f"error getting images at {number}:{name} - context is: >" + repr(re.findall(r'href="https://files.explosm.net/comics/.{50}', data)) + "<")
		desc = f"Source: <a href=\"https://explosm.net/comics/{name}\">https://explosm.net/comics/{name}</a>"
	img_data = []
	try:
		d = requests.get(img_matches[0]).content
		type = img_matches[0].split(".")[-1].lower().encode("UTF-8")
		img_data = [type + b"." + d]
	except: pass
	vname = re.sub(r"^(kris|dave|rob|matt) (comic)?", "", name.replace("-", " "))
	# find author
	author: str | None = name.replace("-", " ").split(" ")[0]
	if author not in ["kris", "dave", "rob", "matt"]:
		author = None
	if author != None:
		author += "-explosm"
	# assemble comic object
	comic = comics.Comic.create(title=vname, comicname="Cyanide & Happiness", description=desc, number=number, author=author, images=img_data)
	# save
	f = open(f"comics/explosm{number}.json", "w")
	f.write(comic.save())
	f.close()
	print(f"done {number} {repr(name)}")
	number += 1
	name = next + ""
	if name in previous: exit()
	previous = [*previous[-5:], name]
	comics.set_left("explosm", {
		"number": number,
		"name": name
	})
