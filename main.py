from http.server import BaseHTTPRequestHandler, HTTPServer
import typing
import comics
import os
from urllib.parse import unquote
import base64
import datetime

hostName = "0.0.0.0"
serverPort = 7963

def read_file(filename: str) -> str:
	f = open(filename, "r")
	t = f.read()
	f.close()
	return t

def write_file(filename: str, content: str):
	f = open(filename, "w")
	f.write(content)
	f.close()

class HttpResponse(typing.TypedDict):
	status: int
	headers: dict[str, str]
	content: bytes

def findComic(name: str, number: int) -> comics.Optional[str]:
	for filename in os.listdir("comics"):
		comic = comics.Comic.load(read_file("comics/" + filename))
		valid = comic.comicname.runWith(lambda x: x == name, False) and comic.number.runWith(lambda x: x == number, False)
		if valid: return comics.Optional(filename)
	return comics.Optional()

def findComicsFromComicName(name: str) -> dict[str, comics.Comic]:
	v: dict[str, comics.Comic] = {}
	for filename in os.listdir("comics"):
		comic = comics.Comic.load(read_file("comics/" + filename))
		valid = comic.comicname.runWith(lambda x: x == name, False)
		if valid:
			v[filename.replace(".json", "")] = comic
	return v

def findNextAndPrev(comic: comics.Comic) -> tuple[comics.Optional[str], comics.Optional[str]]:
	name = comic.comicname.get("$NONEXISTENT")
	number = comic.number.get(-100000)
	if name == "$NONEXISTENT" or number == -100000: return (comics.Optional(), comics.Optional())
	return (
		findComic(name, number + 1),
		findComic(name, number - 1)
	)

def findComicNamesWithAuthor(name: str) -> list[str]:
	v: list[str] = []
	def ta(x: str):
		s = x.replace(".json", "")
		if s not in v:
			v.append(s)
	for filename in os.listdir("comics"):
		comic = comics.Comic.load(read_file("comics/" + filename))
		valid = comic.author.runWith(lambda x: x == name, False)
		if valid:
			comic.comicname.runWith(ta, None)
	return v

def findAllComicNames() -> list[str]:
	v: list[str] = []
	for filename in os.listdir("comics"):
		comic = comics.Comic.load(read_file("comics/" + filename))
		valid = comic.comicname.runWith(lambda x: x not in v, False)
		if valid:
			comic.comicname.runWith(lambda x: v.append(x), None)
	return v

def findAllAuthors() -> list[str]:
	v: list[str] = []
	for filename in os.listdir("comics"):
		comic = comics.Comic.load(read_file("comics/" + filename))
		valid = comic.author.runWith(lambda x: x not in v, False)
		if valid:
			comic.author.runWith(lambda x: v.append(x), None)
	return v

def get(path: str) -> HttpResponse:
	if path == "/":
		return {
			"status": 200,
			"headers": {
				"Content-Type": "text/html; charset=utf-8"
			},
			"content": read_file("index.html").
				replace("{{comics}}", "\n\t".join([f"<p><a href='/comic/{n}'>{n}</a></p>" for n in findAllComicNames()])).
				replace("{{authors}}", "\n\t".join([f"<p><a href='/author/{n}'>{n}</a></p>" for n in findAllAuthors()])).
				encode("UTF-8")
		}
	elif path.startswith("/page/"):
		if os.path.isfile("comics/" + path[6:] + ".json"):
			comic = comics.Comic.load(read_file("comics/" + path[6:] + ".json"))
			nextC, prevC = findNextAndPrev(comic)
			return {
				"status": 200,
				"headers": {
					"Content-Type": "text/html; charset=utf-8"
				},
				"content": read_file("view.html").
					replace("{{comicname}}", comic.comicname.get("???")).
					replace("{{number}}", comic.number.transform(lambda x: str(x)).get("?")).
					replace("{{author}}", comic.author.get("???")).
					replace("{{title}}", comic.title.get(comic.comicname.get("???") + " #" + comic.number.transform(lambda x: str(x)).get("?"))).
					replace("{{images}}", "\n\t".join([f"<p><img src='data:image/{x.split(b'.')[0].decode('UTF-8')};base64,{base64.b64encode(b'.'.join(x.split(b'.')[1:])).decode('UTF-8')}'></p>" for x in comic.images])).
					replace("{{next}}", nextC.get("").replace(".json", "")).
					replace("{{prev}}", prevC.get("").replace(".json", "")).
					replace("{{alt}}", comic.alt.get("<i>Not provided</i>")).
					replace("{{desc}}", comic.description.get("<i>Not provided</i>")).
					encode("UTF-8")
			}
		else: # 404 page
			return {
				"status": 404,
				"headers": {
					"Content-Type": "text/plain"
				},
				"content": b"Page Not Found"
			}
	elif path.startswith("/comic/"):
		listname = unquote(path[7:])
		pages = findComicsFromComicName(listname)
		filenames = [*pages.keys()]
		filenames.sort(key=lambda x: pages[x].number.get(1000000))
		return {
			"status": 200,
			"headers": {
				"Content-Type": "text/html; charset=utf-8"
			},
			"content": read_file("list.html").
				replace("{{name}}", listname).
				replace("{{items}}", "\n\t".join([f"<p><a href='/page/{x}'>#{pages[x].number.transform(lambda x: str(x)).get('?')}{pages[x].title.transform(lambda x: ' - '+x).get('')}</a></p>" for x in filenames])).
				encode("UTF-8")
		}
	elif path.startswith("/author/"):
		listname = unquote(path[8:])
		pages = findComicNamesWithAuthor(listname)
		return {
			"status": 200,
			"headers": {
				"Content-Type": "text/html; charset=utf-8"
			},
			"content": read_file("author.html").
				replace("{{name}}", listname).
				replace("{{comics}}", "\n\t".join([f"<p><a href='/comic/{x}'>{x}</a></p>" for x in pages])).
				encode("UTF-8")
			# TODO: Additional pages by this author
		}
	else: # 404 page
		return {
			"status": 404,
			"headers": {
				"Content-Type": "text/plain"
			},
			"content": b"404 Not Found"
		}

def post(path: str, body: bytes) -> HttpResponse:
	if False:
		bodydata = body.decode("UTF-8").split("\n")
	else:
		return {
			"status": 404,
			"headers": {
				"Content-Type": "text/plain"
			},
			"content": b"404 Not Found"
		}

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		global running
		started = datetime.datetime.now()
		print("started")
		res = get(self.path)
		self.send_response(res["status"])
		for h in res["headers"]:
			self.send_header(h, res["headers"][h])
		self.end_headers()
		c = res["content"]
		self.wfile.write(c)
		ended = datetime.datetime.now()
		dur = (ended - started).total_seconds()
		print(f"ended; took {dur}s")
	def do_POST(self):
		res = post(self.path, self.rfile.read(int(self.headers["Content-Length"])))
		self.send_response(res["status"])
		for h in res["headers"]:
			self.send_header(h, res["headers"][h])
		self.end_headers()
		c = res["content"]
		self.wfile.write(c)
	def log_message(self, format: str, *args) -> None:
		return;
		if 400 <= int(args[1]) < 500:
			# Errored request!
			print(u"\u001b[31m", end="")
		print(args[0].split(" ")[0], "request to", args[0].split(" ")[1], "(status code:", args[1] + ")")
		print(u"\u001b[0m", end="")
		# don't output requests

if __name__ == "__main__":
	running = True
	webServer = HTTPServer((hostName, serverPort), MyServer)
	webServer.timeout = 1
	print("Server started http://%s:%s" % (hostName, serverPort))
	while running:
		try:
			webServer.handle_request()
		except KeyboardInterrupt:
			running = False
	webServer.server_close()
	print("Server stopped")
