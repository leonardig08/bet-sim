import os

import requests
import json
from bs4 import BeautifulSoup
from api.FixtureScrape import getCsv
import pandas as pd

from dataclasses import dataclass, asdict
@dataclass
class Game:
    date : str
    home : str
    away : str
    odds : list
    league: str
    def __post_init__(self):
        for odd in self.odds:
                float(odd)




leagueMap = {
    "Serie A": "soccer-italy-serie-a",
    "Champions League": "soccer-international-clubs-uefa-champions-league",
    "Europa League": "soccer-international-clubs-uefa-europa-league",
    "Conference League": "soccer-international-clubs-t6eeb-uefa-europa-conference-league",
    "Premier League": "soccer-england-premier-league",
    "Bundesliga": "soccer-germany-bundesliga",
    "La Liga": "soccer-spain-laliga",
    "Serie B": "soccer-italy-serie-b",
    "Ligue 1": "soccer-france-ligue-1",
    "World Cup Qualifiers": "soccer-international-wc-qualifying-conmebol"
}

class BetAPI:
    def __init__(self):
        self.urlBetBase = "https://sports-api.cloudbet.com/pub/v2/odds/competitions/"
        self.db = None
        self.nameMap = {}
        self.canRequestBets = True
        try:
            with open("api/map.json", "r", encoding="utf-8") as f:
                self.nameMap = json.loads(f.read())
        except FileNotFoundError:
            self.canRequestBets = False
    def cache_db(self, league, override = False):
        if not os.path.exists(f"api/cache/{league}cache.csv") or override:
            print(f"Override Activated POORPPOO {override}")
            os.remove(f"api/cache/{league}cache.csv")
            self.db = getCsv(league)
            return self.db
        else:
            self.db = pd.read_csv(f"api/cache/{league}cache.csv")
            return self.db

    def get_request(self, league):
        if not self.canRequestBets:
            return
        leagueformat = leagueMap[league]
        self.cache_db(league)
        headers = {
            "accept": "application/json",
            "X-API-Key": "eyJhbGciOiJSUzI1NiIsImtpZCI6Img4LThRX1YwZnlUVHRPY2ZXUWFBNnV2bktjcnIyN1YzcURzQ2Z4bE44MGMiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6ImFmZmlsaWF0ZSIsImV4cCI6MjA3ODMzNDc0NCwiaWF0IjoxNzYyOTc0NzQ0LCJqdGkiOiI1ZWIwNGZjNS0xMjhiLTRhNGEtOTMyNS03Nzk3M2IwYjFmOWQiLCJzdWIiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EiLCJ0ZW5hbnQiOiJjbG91ZGJldCIsInV1aWQiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EifQ.leilGTjGj7zcxFC9zmsUAsK0UAezmGw9aZZrdFHtqtmO821nm4jr7HmqBVgtKzUTPEGpj10JPZVAjf-yr-F83iVLHQrclei-V-q56gxww8GPDd2ns8TMtOfU7SmWgiRzAa7e3wbFwurN9OgmIX-wYo6WvvBPPEdHWi2JesIORGyC8JwIW4f3O8pCcnCOvts2cE9sjO_WoocX-rW9a11EtgfgYST_JvmcvcXoA-Wt7BB3wjOXHuleYY2jT1vwjvlNTQFKPcRdzls_z2EhkUE6BJmpqsfGdNfNje7pYp3zqBzW0Q_lFkZuUZ1j3s2d_RCShU5YzMBbvIJiB0ss4SwCtw"
        }
        url = self.urlBetBase + leagueformat + "?markets=soccer.match_odds"
        response = requests.get(url, headers=headers)
        print(response.status_code)

        events = response.json()["events"]
        gamebets = []

        print(f"DB DB \n{self.db}")
        print(f"MAP MAP \n{self.nameMap}")
        if self.nameMap[league] is None:
            return []
        for event in events:
            if event["home"] is None:
                continue
            gameondb = self.db[(self.db["Home Team"] == self.nameMap[league][event["home"]["name"]]) & (self.db["Away Team"] == self.nameMap[league][event["away"]["name"]])]
            if gameondb.empty:
                print("SKIPPING no match")
                continue
            print(f"{self.db["Home Team"]} -- {self.nameMap[league][event["home"]["name"]]}\n{self.db["Away Team"]} -- {self.nameMap[league][event["away"]["name"]]}")
            oddsraw = event["markets"]["soccer.match_odds"]["submarkets"]["period=ft"]["selections"]
            order_1x2 = ["home", "draw", "away"]
            print(oddsraw)
            oddselab = sorted(
                [o for o in oddsraw if o["outcome"].lower() in order_1x2],
                key=lambda x: order_1x2.index(x["outcome"].lower())
            )
            print("ODD")
            print(oddselab)




            gameobj = Game(gameondb["dateEvent"].iloc[0], gameondb["Home Team"].iloc[0], gameondb["Away Team"].iloc[0], [oddo["price"] for oddo in oddselab], league)
            print(gameobj)
            gamebets.append(gameobj)
        return gamebets
    def get_other_bet(self, league):
        if not self.canRequestBets:
            return
        leagueformat = leagueMap[league]
        self.cache_db(league)
        headers = {
            "accept": "application/json",
            "X-API-Key": "eyJhbGciOiJSUzI1NiIsImtpZCI6Img4LThRX1YwZnlUVHRPY2ZXUWFBNnV2bktjcnIyN1YzcURzQ2Z4bE44MGMiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6ImFmZmlsaWF0ZSIsImV4cCI6MjA3ODMzNDc0NCwiaWF0IjoxNzYyOTc0NzQ0LCJqdGkiOiI1ZWIwNGZjNS0xMjhiLTRhNGEtOTMyNS03Nzk3M2IwYjFmOWQiLCJzdWIiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EiLCJ0ZW5hbnQiOiJjbG91ZGJldCIsInV1aWQiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EifQ.leilGTjGj7zcxFC9zmsUAsK0UAezmGw9aZZrdFHtqtmO821nm4jr7HmqBVgtKzUTPEGpj10JPZVAjf-yr-F83iVLHQrclei-V-q56gxww8GPDd2ns8TMtOfU7SmWgiRzAa7e3wbFwurN9OgmIX-wYo6WvvBPPEdHWi2JesIORGyC8JwIW4f3O8pCcnCOvts2cE9sjO_WoocX-rW9a11EtgfgYST_JvmcvcXoA-Wt7BB3wjOXHuleYY2jT1vwjvlNTQFKPcRdzls_z2EhkUE6BJmpqsfGdNfNje7pYp3zqBzW0Q_lFkZuUZ1j3s2d_RCShU5YzMBbvIJiB0ss4SwCtw"
        }
        url = self.urlBetBase + leagueformat + "?markets=soccer.total_goals"
        response = requests.get(url, headers=headers)
        print(response.status_code)

        events = response.json()["events"]

        gamebets = []
        print(f"DB DB \n{self.db}")
        print(f"MAP MAP \n{self.nameMap}")
        if self.nameMap[league] is None:
            return []
        for event in events:

            if event["home"] is None:
                continue
            gameondb = self.db[(self.db["Home Team"] == self.nameMap[league][event["home"]["name"]]) & (
                        self.db["Away Team"] == self.nameMap[league][event["away"]["name"]])]
            if gameondb.empty:
                print(f"SKIPPING no match {event["home"]} -- {event["away"]}")
                continue
            oddsraw = event["markets"]["soccer.total_goals"]["submarkets"]["period=ft"]["selections"]

            oddshalfraw = [odd for odd in oddsraw if odd["params"] == "total=2.5"]

            order_ou = ["over", "under"]

            print(oddshalfraw)

            oddselab = sorted(
                [o for o in oddshalfraw if o["outcome"].lower() in order_ou],
                key=lambda x: order_ou.index(x["outcome"].lower())
            )
            print("ODD")
            print(oddselab)




            if oddselab == []:
                print("NO UNDER OVER")
                continue



            gameobj = Game(gameondb["dateEvent"].iloc[0], gameondb["Home Team"].iloc[0], gameondb["Away Team"].iloc[0],
                           [oddo["price"] for oddo in oddselab], league)
            print(gameobj)
            gamebets.append(gameobj)
        if league == "Serie A":
            print(gamebets)
        return gamebets
    def get_golng(self, league):
        if not self.canRequestBets:
            return
        leagueformat = leagueMap[league]
        self.cache_db(league)
        headers = {
            "accept": "application/json",
            "X-API-Key": "eyJhbGciOiJSUzI1NiIsImtpZCI6Img4LThRX1YwZnlUVHRPY2ZXUWFBNnV2bktjcnIyN1YzcURzQ2Z4bE44MGMiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6ImFmZmlsaWF0ZSIsImV4cCI6MjA3ODMzNDc0NCwiaWF0IjoxNzYyOTc0NzQ0LCJqdGkiOiI1ZWIwNGZjNS0xMjhiLTRhNGEtOTMyNS03Nzk3M2IwYjFmOWQiLCJzdWIiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EiLCJ0ZW5hbnQiOiJjbG91ZGJldCIsInV1aWQiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EifQ.leilGTjGj7zcxFC9zmsUAsK0UAezmGw9aZZrdFHtqtmO821nm4jr7HmqBVgtKzUTPEGpj10JPZVAjf-yr-F83iVLHQrclei-V-q56gxww8GPDd2ns8TMtOfU7SmWgiRzAa7e3wbFwurN9OgmIX-wYo6WvvBPPEdHWi2JesIORGyC8JwIW4f3O8pCcnCOvts2cE9sjO_WoocX-rW9a11EtgfgYST_JvmcvcXoA-Wt7BB3wjOXHuleYY2jT1vwjvlNTQFKPcRdzls_z2EhkUE6BJmpqsfGdNfNje7pYp3zqBzW0Q_lFkZuUZ1j3s2d_RCShU5YzMBbvIJiB0ss4SwCtw"
        }
        url = self.urlBetBase + leagueformat + "?markets=soccer.both_teams_to_score"
        response = requests.get(url, headers=headers)
        print(response.status_code)

        events = response.json()["events"]

        gamebets = []
        print(f"DB DB \n{self.db}")
        print(f"MAP MAP \n{self.nameMap}")
        if self.nameMap[league] is None:
            return []
        for event in events:
            print(event)

            if event["home"] is None:
                continue
            gameondb = self.db[(self.db["Home Team"] == self.nameMap[league][event["home"]["name"]]) & (
                        self.db["Away Team"] == self.nameMap[league][event["away"]["name"]])]
            if gameondb.empty:
                print(f"SKIPPING no match {event["home"]} -- {event["away"]}")
                continue
            if not "soccer.both_teams_to_score" in event["markets"].keys():
                print("NO BOTH TEAMS")
                continue

            oddsraw = event["markets"]["soccer.both_teams_to_score"]["submarkets"]["period=ft"]["selections"]

            order_gng = ["yes", "no"]

            oddselab = sorted(
                [o for o in oddsraw if o["outcome"].lower() in order_gng],
                key=lambda x: order_gng.index(x["outcome"].lower())
            )
            print("ODD")
            print(oddselab)




            if oddselab == []:
                print("NO GNG")
                continue



            gameobj = Game(gameondb["dateEvent"].iloc[0], gameondb["Home Team"].iloc[0], gameondb["Away Team"].iloc[0],
                           [oddo["price"] for oddo in oddselab], league)
            print(gameobj)
            gamebets.append(gameobj)
        return gamebets
    def get_double(self, league):
        if not self.canRequestBets:
            return
        leagueformat = leagueMap[league]
        self.cache_db(league)
        headers = {
            "accept": "application/json",
            "X-API-Key": "eyJhbGciOiJSUzI1NiIsImtpZCI6Img4LThRX1YwZnlUVHRPY2ZXUWFBNnV2bktjcnIyN1YzcURzQ2Z4bE44MGMiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6ImFmZmlsaWF0ZSIsImV4cCI6MjA3ODMzNDc0NCwiaWF0IjoxNzYyOTc0NzQ0LCJqdGkiOiI1ZWIwNGZjNS0xMjhiLTRhNGEtOTMyNS03Nzk3M2IwYjFmOWQiLCJzdWIiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EiLCJ0ZW5hbnQiOiJjbG91ZGJldCIsInV1aWQiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EifQ.leilGTjGj7zcxFC9zmsUAsK0UAezmGw9aZZrdFHtqtmO821nm4jr7HmqBVgtKzUTPEGpj10JPZVAjf-yr-F83iVLHQrclei-V-q56gxww8GPDd2ns8TMtOfU7SmWgiRzAa7e3wbFwurN9OgmIX-wYo6WvvBPPEdHWi2JesIORGyC8JwIW4f3O8pCcnCOvts2cE9sjO_WoocX-rW9a11EtgfgYST_JvmcvcXoA-Wt7BB3wjOXHuleYY2jT1vwjvlNTQFKPcRdzls_z2EhkUE6BJmpqsfGdNfNje7pYp3zqBzW0Q_lFkZuUZ1j3s2d_RCShU5YzMBbvIJiB0ss4SwCtw"
        }
        url = self.urlBetBase + leagueformat + "?markets=soccer.double_chance"
        response = requests.get(url, headers=headers)
        print(response.status_code)

        events = response.json()["events"]
        gamebets = []

        print(f"DB DB \n{self.db}")
        print(f"MAP MAP \n{self.nameMap}")
        if self.nameMap[league] is None:
            return []
        for event in events:
            if event["home"] is None:
                continue
            gameondb = self.db[(self.db["Home Team"] == self.nameMap[league][event["home"]["name"]]) & (self.db["Away Team"] == self.nameMap[league][event["away"]["name"]])]
            if gameondb.empty:
                print("SKIPPING no match")
                continue

            if not "soccer.double_chance" in event["markets"].keys():
                print("NO BOTH TEAMS")
                continue
            print(f"{self.db["Home Team"]} -- {self.nameMap[league][event["home"]["name"]]}\n{self.db["Away Team"]} -- {self.nameMap[league][event["away"]["name"]]}")
            oddsraw = event["markets"]["soccer.double_chance"]["submarkets"]["period=ft"]["selections"]
            order_double = ["home_draw", "home_away", "draw_away"]
            print(oddsraw)
            oddselab = sorted(
                [o for o in oddsraw if o["outcome"].lower() in order_double],
                key=lambda x: order_double.index(x["outcome"].lower())
            )
            print("ODD")
            print(oddselab)




            gameobj = Game(gameondb["dateEvent"].iloc[0], gameondb["Home Team"].iloc[0], gameondb["Away Team"].iloc[0], [oddo["price"] for oddo in oddselab], league)
            print(gameobj)
            gamebets.append(gameobj)
        return gamebets



    def get_fixture(self):
        print("Fix")
        headers = {
            "accept": "application/json",
            "X-API-Key": "eyJhbGciOiJSUzI1NiIsImtpZCI6Img4LThRX1YwZnlUVHRPY2ZXUWFBNnV2bktjcnIyN1YzcURzQ2Z4bE44MGMiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6ImFmZmlsaWF0ZSIsImV4cCI6MjA3ODMzNDc0NCwiaWF0IjoxNzYyOTc0NzQ0LCJqdGkiOiI1ZWIwNGZjNS0xMjhiLTRhNGEtOTMyNS03Nzk3M2IwYjFmOWQiLCJzdWIiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EiLCJ0ZW5hbnQiOiJjbG91ZGJldCIsInV1aWQiOiIxN2U0ZDk4MS1jODA1LTRkZDMtYmVmYi01NzhjNTkwNWMwY2EifQ.leilGTjGj7zcxFC9zmsUAsK0UAezmGw9aZZrdFHtqtmO821nm4jr7HmqBVgtKzUTPEGpj10JPZVAjf-yr-F83iVLHQrclei-V-q56gxww8GPDd2ns8TMtOfU7SmWgiRzAa7e3wbFwurN9OgmIX-wYo6WvvBPPEdHWi2JesIORGyC8JwIW4f3O8pCcnCOvts2cE9sjO_WoocX-rW9a11EtgfgYST_JvmcvcXoA-Wt7BB3wjOXHuleYY2jT1vwjvlNTQFKPcRdzls_z2EhkUE6BJmpqsfGdNfNje7pYp3zqBzW0Q_lFkZuUZ1j3s2d_RCShU5YzMBbvIJiB0ss4SwCtw"
        }
        url = "https://sports-api.cloudbet.com/pub/v2/odds/fixtures?sport=soccer&from=1763022545&to=1765614545&players=false&limit=10000"
        response = requests.get(url, headers=headers)
        print(response.status_code)
        with open("mega.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(response.json(), indent=4))





if __name__ == "__main__":
    api = BetAPI()
    api.get_request("Serie B")

