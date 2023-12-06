import urllib.request
import urllib.error
import http.cookiejar as cookielib
from functools import total_ordering
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os
from dotenv import load_dotenv



DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3"
}


class MyRequest(urllib.request.Request):
    def __init__(self, url, data=None, headers=DEFAULT_REQUEST_HEADERS, origin_req_host=None, unverifiable=False):
        super().__init__(url, data, headers, origin_req_host, unverifiable)


class MyUrlOpener(object):
    def __init__(self, proxy=None, stringcookie=None):
        self.state = "build"
        self.handler = []
        self.cookiejar = cookielib.CookieJar()
        self.add_handler(urllib.request.HTTPCookieProcessor(self.cookiejar))
        self.proxy = proxy
        if self.proxy:
            if not isinstance(self.proxy, urllib.request.ProxyHandler):
                self.proxy = urllib.request.ProxyHandler(proxy)
            self.add_handler(self.proxy)
        self.__urlo = urllib.request.build_opener(*self.handler)
        self.open = self.__urlo.open
        self.state = "run"

    def clear_cookies(self):
        self.cookiejar.clear()

    def add_handler(self, h):
        assert self.state == "build"
        self.handler.append(h)


@total_ordering
class SteamApp:
    id = None
    name = None
    type = None

    def __lt__(self, other):
        return self.id - other.id

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

class App():

    # Load environment variables from .env file
    load_dotenv()

    # Get the MongoDB username and password from environment variables
    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")

    # Construct the MongoDB URI with the username and password
    uri = f"mongodb+srv://{username}:{password}@bbwfi.m1wu7rg.mongodb.net/"

    def __init__(self):
        self.client = MongoClient(self.uri)  
        self.db = self.client['steam']  
        self.collection = self.db['games']  
        self.steamapps = set()

    def __call__(self, *args, **kwargs):
        self.steamapps.clear()
        url = MyUrlOpener()
        for page in range(1, 1000):
            try:
                soup = BeautifulSoup(urlo.open(MyRequest("http://steamdb.info/apps/page{}/".format(page))).read())
                table = soup.find('table', id='table-apps')

                for app in table.find_all('tr'):
                    steamapp = SteamApp()
                    for i, element in enumerate(app.find_all('td')):
                        try:
                            if i == 0:
                                steamapp.id = int(next(element.stripped_strings))
                            elif i == 1:
                                steamapp.type = next(element.stripped_strings)
                            elif i == 2:
                                steamapp.name = next(element.stripped_strings)
                        except Exception:
                            pass
                    if steamapp.id is not None:
                        self.steamapps.add(steamapp)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print('stopping')
                    break
        for app in self.steamapps:
            d = app.__dict__.copy()
            del d['id']
            self.collection.update({'_id': app.id}, {"$set": d}, upsert=True)


def main():
    app = App()
    app()


if __name__ == '__main__':
    main()



