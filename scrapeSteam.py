from flask import Flask, jsonify, json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class Release():
    id = None
    name = None
    type = None
    info = ""
    followers = 0
    followers_change = 0
    trend_svg = None
    price = 0.0
    applogo = None

class App():
    uri = "mongodb+srv://prath:ffWubpPWNQZrlVZr@bbwfi.m1wu7rg.mongodb.net/"
    releases = set()
    releases_json = []

    def scrape(self):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        driver.get("https://steamdb.info/upcoming/?nosmall")
        bs = BeautifulSoup(driver.page_source, "html.parser")

        selector = "#main > div.container"

        container = bs.select_one(selector)

        for release_selection in container.select("tbody > tr"):
            release = Release()

            ## get data attributes data-appid, data-type, data-name
            release.id = int(release_selection.get("data-appid"))

            for i, element in enumerate(release_selection.find_all('td')):
                try:
                    if i == 1:
                        applogo = element.find("img").get("src")
                        if applogo is None or applogo == "/static/img/applogo.svg":
                            release.applogo = "https://steamdb.info/static/img/applogo.svg"
                        elif applogo is not None:
                            release.applogo = applogo
                    elif i == 2:
                        release.name = element.find("a").get_text()
                        release.info = element.find("i").get_text()
                        release.type = element.find("i").get_text().split(",")[0].strip()
                    elif i == 3:
                        release.followers = int(element.get_text().replace(",", ""))
                    elif i == 4:
                        # statistics
                        release.trend_svg = str(element.find("svg"))
                    elif i == 5:
                        # statistics change
                        release.followers_change = element.get_text().replace(",", "")
                    elif i == 6:
                        release.price = float(element.get_text().split("€")[0].strip().replace(",", "."))
                except Exception:
                    pass
            if release.id is not None:
                self.releases.add(release)

        driver.close()
        self.export()

    def export(self):
        releases_json = []
        for release in self.releases:
            release_dict = {
                "id": release.id,
                "name": release.name,
                "type": release.type,
                "info": release.info,
                "followers": release.followers,
                "followers_change": release.followers_change,
                "trend_svg": release.trend_svg,
                "price": release.price,
                "applogo": release.applogo
            }
            releases_json.append(release_dict)

        with open("releases.json", "w") as file:
            json.dump(releases_json, file)

class FlaskServer():
    def serve(self):
        app = Flask(__name__)

        @app.route('/releases', methods=['GET'])
        def get_releases():
            with open("releases.json", "r") as file:
                releases = json.load(file)
            return jsonify(releases)
        app.run(host="0.0.0.0", port=5100)
    
    
def main():
    app = App()
    app.scrape()
    server = FlaskServer()
    server.serve()

main()
