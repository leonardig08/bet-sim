from bs4 import BeautifulSoup
import json
import re
import requests
import pandas as pd
from rapidfuzz import process, fuzz
from pprint import pprint
import os



leagues = ["Serie A", "Serie B", "Champions League",
           "Europa League", "Conference League", "Premier League",
           "Bundesliga", "La Liga", "Ligue 1", "World Cup Qualifiers"]


def fuzzy_match(name, choices, threshold=2):

    if name == "Northern Ireland":
        return "N.Ireland"

    match, score, _ = process.extractOne(name, choices, scorer=fuzz.token_set_ratio)
    #print(f"SCELTO {match} corrispondente a {name} con affidabilità {score}%")
    if name == "Parma Calcio":
        print(f"SCELTO {match} corrispondente a {name} con affidabilità {score}%")
        print(f"SCELTE DISPONIBILI:\n{choices}")

    if score >= threshold:
        return match
    return None


def fuzzy_league_match(league_name, jsondata, key_hint=None, threshold=50):
    if key_hint:
        # 1. Trova tutte le leghe con lo stesso name
        print(league_name.lower())
        candidates = [comp for comp in jsondata if comp["name"].lower() == league_name.lower()]
        candidatesalt = [comp for comp in jsondata if league_name.lower() in comp["name"].lower()  ]
        if not candidates:
            candidates = candidatesalt
        print(candidates)
        print(key_hint)



        # 2. Se esiste un hint nel key, filtriamo
        if key_hint:
            candidates = [comp for comp in candidates if key_hint.lower() in comp["key"].lower()]

        print([candidate["key"] for candidate in candidates])

        # 3. Se rimane una sola candidata, la prendiamo
        if len(candidates) == 1:
            return candidates[0]["key"]

        # 4. Se ci sono ancora più candidate, usiamo fuzzy match sul name completo
        if candidates:

            all_names = [comp["name"] + " " + comp["key"] for comp in candidates]
            match_name, score, idx = process.extractOne(league_name, all_names, scorer=fuzz.token_set_ratio)
            if score >= threshold:
                return candidates[idx]

        # Nessuna corrispondenza affidabile

        return None
    else:
        allcomps = [comp["name"] for comp in jsondata]
        return fuzzy_match(league_name, allcomps)



def saveMap(league):
    if type(league) == str:
        idmap = None
        with open("api/idmap.json", "r", encoding="utf-8") as f:
            idmap = json.loads(f.read())
        if idmap:
            url = f"https://www.thesportsdb.com/season/{idmap[league]}/2025-2026?csv=1&all=1"

            response = requests.get(url)
            print(response.status_code)
            if response.status_code == 200:
                htmlfile = response.text
                soup = BeautifulSoup(htmlfile, "lxml")
                datacsv = soup.find(name="textarea",attrs={
                    "id": "myInput"
                })
                with open("api/testleague.csv", "w", encoding="utf-8") as f:
                    f.write(datacsv.get_text())
                csvdata = pd.read_csv("api/testleague.csv")
                with open("mega.json","r",encoding="utf-8") as f:
                    jsondata = json.loads(f.read())

                jsondata = jsondata["competitions"]
                compselect = None


                with open("api/keyhints.json","r",encoding="utf-8") as f:
                    hints = json.loads(f.read())
                if league in hints.keys():
                    keyhint = hints[league]
                else:
                    keyhint = None

                matched = fuzzy_league_match(league, jsondata, keyhint)
                print(league, keyhint)
                print(matched)

                for comp in jsondata:
                    if comp["name"] == matched:
                        compselect = comp["events"]
                    if comp["key"] == matched:
                        compselect = comp["events"]
                if not compselect:
                    print("ERROR ",compselect)
                    return

                teamstotal = {}
                for game in compselect:
                    teamstotal.setdefault(game["home"]["name"])
                    teamstotal.setdefault(game["away"]["name"])
                teambet = set(teamstotal)
                dbteams = set(csvdata["Home Team"].tolist() + csvdata["Away Team"].tolist())
                associate = {}
                if league == "Premier League":
                    pprint(teambet)
                    pprint(dbteams)
                for i in teambet:
                    match = fuzzy_match(i, dbteams)
                    if match:
                        associate[i] = match
                return associate
        else:
            print("NO ID")

def getCsv(league): # cartella dello script
    idmap_path =  "api/idmap.json"

    if not os.path.exists(idmap_path):
        print(f"File idmap.json non trovato: {idmap_path}")
        return None

    with open(idmap_path, "r", encoding="utf-8") as f:
        idmap = json.load(f)

    if league not in idmap:
        print(f"League '{league}' non trovata in idmap.json")
        return None

    print("ID MAP TROVATA")
    url = f"https://www.thesportsdb.com/season/{idmap[league]}/2025-2026?csv=1&all=1"
    response = requests.get(url)
    print("HTTP status:", response.status_code)

    if response.status_code != 200:
        print("Errore nella richiesta")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    datacsv = soup.find("textarea", id="myInput")
    if datacsv is None:
        print("Textarea con CSV non trovata nella pagina")
        return None

    cache_dir = "api/cache"
    os.makedirs(cache_dir, exist_ok=True)

    cache_file = f"api/cache/{league}cache.csv"

    print(cache_file)
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(datacsv.get_text())

    return pd.read_csv(cache_file)

def create_map():
    from api.OddApiNew import BetAPI
    bet = BetAPI()

    bet.get_fixture()
    totalassociate = {}
    for l in leagues:
        fix = saveMap(l)
        # pprint(fix)
        totalassociate[l] = fix

    with open(f"api/map.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(totalassociate, indent=4))
