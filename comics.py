import typing
import datetime
import json
import base64

def log(info: str):
	f = open("log.txt", "a")
	f.write(datetime.datetime.now().isoformat())
	f.write(" - ")
	f.write(info)
	f.write("\n")
	f.close()

T = typing.TypeVar('T')
R = typing.TypeVar('R')
class Optional(typing.Generic[T]):
	def __init__(self, value: T | None = None):
		self._value = value
	def set(self, value: T | None = None):
		self._value = value
	def ifPresent(self, callback: typing.Callable[[ T ], typing.Any]):
		if self._value != None:
			callback(self._value)
	def runWith(self, valueCallback: typing.Callable[[ T ], R], absentValue: R) -> R:
		if self._value == None:
			return absentValue
		else:
			return valueCallback(self._value)
	def get(self, substitute: T) -> T:
		if self._value == None:
			return substitute
		else:
			return self._value
	def transform(self, callback: typing.Callable[[ T ], R]) -> "Optional[R]":
		if self._value == None:
			return Optional()
		else:
			return Optional(callback(self._value))

class Comic:
	def __init__(self, title: Optional[str], date: Optional[datetime.date], comicname: Optional[str], number: Optional[int], author: Optional[str], images: list[bytes], alt: Optional[str], description: Optional[str]):
		self.title: Optional[str] = title
		self.date: Optional[datetime.date] = date
		self.comicname: Optional[str] = comicname
		self.number: Optional[int] = number
		self.author: Optional[str] = author
		self.images: list[bytes] = images
		self.alt: Optional[str] = alt
		self.description: Optional[str] = description
	def save(self):
		data: dict[str, None | str | int | list[str] | dict[str, int]] = {
			"title": self.title.runWith(lambda x: x, None),
			"date": self.date.runWith(lambda x: {
				"year": x.year,
				"month": x.month,
				"day": x.day
			}, None),
			"comicname": self.comicname.runWith(lambda x: x, None),
			"number": self.number.runWith(lambda x: x, None),
			"author": self.author.runWith(lambda x: x, None),
			"images": [base64.b64encode(x).decode("UTF-8") for x in self.images],
			"alt": self.alt.runWith(lambda x: x, None),
			"description": self.description.runWith(lambda x: x, None)
		}
		return json.dumps(data, indent='\t')
	@staticmethod
	def load(raw: str):
		data = json.loads(raw)
		return Comic(
			Optional(data["title"]),
			Optional() if data["date"] == None else Optional(datetime.date(data["date"]["year"], data["date"]["month"], data["date"]["day"])),
			Optional(data["comicname"]),
			Optional(data["number"]),
			Optional(data["author"]),
			[base64.b64decode(x.encode("UTF-8")) for x in data["images"]],
			Optional(data["alt"]),
			Optional(data["description"])
		)
	@staticmethod
	def create(title: str | None = None, date: datetime.date | None = None, comicname: str | None = None, number: int | None = None, author: str | None = None, images: list[bytes] = [], alt: str | None = None, description: str | None = None):
		return Comic(Optional(title), Optional(date), Optional(comicname), Optional(number), Optional(author), images, Optional(alt), Optional(description))
