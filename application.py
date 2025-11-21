VERSION = "2.3.0 PROD RELEASE"


import os
import json
import datetime

import requests
from textual.css.query import NoMatches

from api import OddApiNew
from textual.app import App, ComposeResult
from textual.containers import VerticalGroup, HorizontalGroup, VerticalScroll, Grid, Center, Right
from textual.widgets import Header, Label, Rule, LoadingIndicator, TabbedContent, TabPane, Select, Button, Collapsible, \
    Input, Markdown
from textual.screen import Screen, ModalScreen
from textual.widget import Widget
from asset import stringText, cssText
from textual import work, log
from dataclasses import dataclass, asdict
from textual.reactive import reactive
import pandas as pd
from api.FixtureScrape import create_map
import textual.theme

# modes: 1 (1x2), 2 (underover), 3 (golnogol)

scraper = None#

betTypes = ["1x2", "Under/Over", "Entrambi Segnano"]

mapNames = None

associate = {
                            "1": 0,
                            "x": 1,
                            "2": 2,
                            "Under": 0,
                            "Over": 1,
                            "Si": 0,
                            "No": 1
                        }

import unicodedata
import re

def sanitize_id(s: str) -> str:
    # Converti in forma decomposed (NFKD) e rimuovi caratteri non ASCII
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode()
    # Sostituisci tutto ciò che non è lettera, numero o underscore con underscore
    s = re.sub(r"[^a-zA-Z0-9_-]", "_", s)
    return s


from datetime import datetime, timedelta

multcache = 0


def date_formatString(date_str):
    """
    Converte una data in formato YYYY-MM-DD in:
    - "OGGI" se la data è oggi
    - "DOMANI" se la data è domani
    - "19 Novembre 2025" altrimenti
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

    oggi = datetime.today().date()
    domani = oggi + timedelta(days=1)

    if date_obj.date() == oggi:
        return f"{date_obj.day} {mesi[date_obj.month - 1]} {date_obj.year} | OGGI"
    elif date_obj.date() == domani:
        return f"{date_obj.day} {mesi[date_obj.month - 1]} {date_obj.year} | DOMANI"
    else:
        delta = date_obj.date() - oggi
        return f"{date_obj.day} {mesi[date_obj.month - 1]} {date_obj.year} TRA {delta.days} GIORNI"


leaguesDict = {"gamesItalia": ["Serie A", "Serie B"],
               "gamesUefa": ["Champions League", "Europa League", "Conference League"],
               "gamesInghilterra": ["Premier League"],
               "gamesGermania": ["Bundesliga"],
               "gamesSpagna": ["La Liga"],
               "gamesFrancia": ["Ligue 1"],
               "gamesInternazionale": ["World Cup Qualifiers"]}




databaseGame = {}

class WarningDialogDefault(ModalScreen):
    def __init__(self, warningMessage: str):
        self.warningMessage = warningMessage
        super().__init__()
    def compose(self):
        yield Grid(
            Label(self.warningMessage),
            Button("OK", variant="warning")
        )
    def on_button_pressed(self, event: Button.Pressed):
        self.app.pop_screen()

class SplashScreen(Screen):
    def compose(self):
        with VerticalGroup():
            yield Label(stringText, id="labelTitoletto")
            yield Rule(line_style="thick")
            yield LoadingIndicator()

class GameObject(Widget):
    def __init__(self, gameObject, id=None, typebet = 1, prepress=None):
        super().__init__(id=sanitize_id(id))
        self.game = gameObject
        self.rendermode = typebet
        self.prepress = prepress
    def compose(self):
        match self.rendermode:
            case 1:
                with HorizontalGroup():
                    with VerticalGroup(id="groupGameDetail"):
                        yield Label(f"{self.game.home} - {self.game.away}")
                        yield Label(f"{date_formatString(self.game.date)}", id="labelData")
                    with HorizontalGroup(id="oddGroup"):
                        index = 0
                        btts = []
                        for i in (["1", "x", "2"] if len(self.game.odds) == 3 else ["1", "2"]):
                            with VerticalGroup(id=f"odd{i}"):
                                yield Label(i.upper(), id="labelUnit")
                                yield Rule(line_style="solid", id="ruleUnit")
                                btts.append(Button(str(self.game.odds[index]), "primary", name=f"{self.game.home.replace("/", "")}/{self.game.away.replace("/", "")}/{i}"))
                                yield btts[index]
                            index += 1
                        if self.prepress is not None:
                            btts[self.prepress].variant = "success"
            case 2:
                with HorizontalGroup():
                    with VerticalGroup(id="groupGameDetail"):

                        yield Label(f"{self.game.home} - {self.game.away}")
                        yield Label(f"{date_formatString(self.game.date)}", id="labelData")
                    with HorizontalGroup(id="oddGroup"):
                        index = 0
                        btts = []
                        for i in ["Over", "Under"]:
                            with VerticalGroup(id=f"odd{i}"):
                                yield Label(i.upper(), id="labelUnit")
                                yield Rule(line_style="solid", id="ruleUnit")
                                btts.append(Button(str(self.game.odds[index]), "primary",
                                                   name=f"{self.game.home.replace("/", "")}/{self.game.away.replace("/", "")}/{i}"))
                                yield btts[index]
                            index += 1
                        if self.prepress is not None:
                            btts[self.prepress].variant = "success"
            case 3:
                with HorizontalGroup():
                    with VerticalGroup(id="groupGameDetail"):

                        yield Label(f"{self.game.home} - {self.game.away}")
                        yield Label(f"{date_formatString(self.game.date)}", id="labelData")
                    with HorizontalGroup(id="oddGroup"):
                        index = 0
                        btts = []
                        for i in ["Si", "No"]:
                            with VerticalGroup(id=f"odd{i}"):
                                yield Label(i.upper(), id="labelUnit")
                                yield Rule(line_style="solid", id="ruleUnit")
                                btts.append(Button(str(self.game.odds[index]), "primary",
                                                   name=f"{self.game.home.replace("/", "")}/{self.game.away.replace("/", "")}/{i}"))
                                yield btts[index]
                            index += 1
                        if self.prepress is not None:
                            btts[self.prepress].variant = "success"

                    
    def placeHolder(self):
        pass
    def on_button_pressed(self, event: Button.Pressed):
        button = event.button
        data = button.name.split("/")

        self.screen.add_bet(self.game, data[2], button.name, self.rendermode)

class TicketObject(Widget):
    def __init__(self, betObject, index,  id = None):
        super().__init__(id=id)
        self.value = float(betObject[0])
        self.bet = betObject[1]
        self.index = index
        self.multodds = None
        
    def compose(self):
        with Collapsible(title=f"Scheda numero {self.index}"):

            print(self.bet)
            scommesseVinte = []
            self.multodds = 1
            for id, selected in self.bet.items():
                game = selected[0]
                score = None
                for _, i in databaseGame[game.league].iterrows():

                    if game.home == i["Home Team"] and game.away == i["Away Team"]:
                        home_score = i["Home Score"]
                        away_score = i["Away Score"]

                        home_score = None if pd.isna(home_score) else home_score
                        away_score = None if pd.isna(away_score) else away_score
                        if home_score != None and away_score != None:
                            score = [int(home_score), int(away_score)]
                print(score)
                gameString = "Nessun Risultato" if not score else "Risultato Disponibile"

                oddSelected = selected[1]

                scoreString = "Risultato non presente" if score == None else f"{score[0]}-{score[1]}"
                
                wonBet = None
                if score is not None:
                    match oddSelected:
                        case "1":
                            if score[0] > score[1]:
                                wonBet = True
                            else: wonBet = False
                        case "x":
                            if score[0] == score[1]:
                                wonBet = True 
                            else: wonBet = False
                        case "2":
                            if score[0] < score[1]:
                                wonBet = True 
                            else: wonBet = False
                        case "Under":
                            if score[0]+score[1] < 2.5:
                                wonBet = True 
                            else: wonBet = False
                        case "Over":
                            if score[0]+score[1] > 2.5:
                                wonBet = True 
                            else: wonBet = False
                        case "Si":
                            if score[0] >= 1 and score[1] >= 1:
                                wonBet = True
                            else: wonBet = False
                        case "No":
                            if score[0] == 0 or score[1] == 0:
                                wonBet = True
                            else: wonBet = False

                match wonBet:
                    case True:
                        emoji = "🟢"
                    case False:
                        emoji = "🔴"
                    case _:
                        emoji = "🟡"
                scommesseVinte.append(wonBet)
                self.multodds *= float(game.odds[associate[oddSelected]])
                with Collapsible(title=f"{game.home} - {game.away} || {date_formatString(game.date)} || {gameString} || {emoji}"):
                    yield Label(f"Selezionata: {oddSelected}\nQuotazione: {game.odds[associate[oddSelected]]}\nRisultato: {scoreString}")
            with HorizontalGroup(id="internalGroupCash"):
                disableButton = not all(scommesseVinte)
                lostBet = False
                if False in scommesseVinte:
                    lostBet = True

                if not disableButton and not lostBet:
                    statoScommessa = "Vinta"
                elif not lostBet:
                    statoScommessa = "In corso"
                else:
                    statoScommessa = "Persa"
                yield Label(f"Valore scheda €{self.value}\nGuadagno potenziale €{round(self.value * self.multodds, 2)}\nStato: {statoScommessa}", id="labelValue")
                if not lostBet:
                    yield Button("Cash out", "success", id="cashOutButton", disabled=disableButton)
                else: yield Button("Elimina Scommessa", "error", id="removeBetButton")
    def on_button_pressed(self, event: Button.Pressed):
        contentId = event.button.id
        print(contentId)
        if contentId == "cashOutButton":
            TELEGRAM_TOKEN = "8261199286:AAGDEycUALaw1UTCK0Wpe9m73M_kRunJZ84"
            username = None
            canTelegram = True
            try:
                with open("telegram.user", "r", encoding="utf-8") as f:
                    username = f.read()
            except FileNotFoundError:
                canTelegram = False
            if not username:
                canTelegram = False
            print(canTelegram)
            print(username)

            print("cash")
            cash = round(self.value * self.multodds, 2)

            self.app.screen.balance += cash
            if canTelegram:
                url1 = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
                send1 = requests.get(url1)
                print(send1.content)
                cnts = json.loads(send1.content)
                chatid = None
                for event in cnts["result"]:
                    print(event)
                    if event["message"]["chat"]["first_name"] == username:
                        chatid = event["message"]["chat"]["id"]
                if chatid != None:
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    params = {"chat_id": chatid, "text": f"EFFETTUATO CASHOUT SU ACCOUNT PER IL VALORE DI:\n>>| {cash} € |<<"}
                    send = requests.get(url, params=params)
                    print(send.status_code)
            try:
                os.remove(f"bets/{self.index}.bet")
            except FileNotFoundError:
                pass
            self.remove()
        elif contentId == "removeBetButton":
            print("elimina")
            try:
                os.remove(f"bets/{self.index}.bet")
            except FileNotFoundError:
                pass
            self.remove()





class MainAppScreen(Screen):
    balance = reactive(0)
    moneyloaded = False
    betpay = reactive("?")
    def __init__(self):
        super().__init__(id="MainAppScreen")
        self.odd_cache = {}
        self.rejectIndex = 0
        self.current_bet = {}
        self.old_nation = "Italia"
        self.old_bet = "1x2"

    def compose(self):


        yield Header(True)
        yield Center(Label("Soldi: ???", id="balanceLab"))
        with TabbedContent(id = "tabNation"):

            nominazioni = [item.replace("games", "") for item in leaguesDict.keys()]

            for nom in nominazioni:
                with TabPane(nom):
                    selectLeague = Select.from_values(leaguesDict["games"+nom], prompt="Lega selezionata",
                                                      allow_blank=False, id="select"+nom)
                    selectOdd = Select.from_values(betTypes, prompt="Tipo scommessa", allow_blank=False, id="bet"+nom)
                    with HorizontalGroup():
                        yield selectLeague
                        yield selectOdd
                    yield VerticalScroll(id="games"+nom)



            with TabPane("Scheda"):
                yield Label("La tua scheda", id="titleScheda")
                with VerticalScroll(id="ticketGroup"):
                    for game, selectedBet in self.current_bet:
                        with Collapsible(title=f"{game.home} - {game.away} || {game.date}"):
                                yield Label(f"Selezionata: {selectedBet}\nQuotazione: {game[selectedBet]}")
                with HorizontalGroup(id="GroupBuy"):
                    yield Label("Costo €")
                    yield Input(placeholder="Soldi", type="number", id="soldiInput")
                    yield Button("Compra la scommessa", variant="success", id="buyButton")
                    yield Label(f"Guadagno Potenziale: {self.betpay} €", id="payoutLabel")

            with TabPane("Risultati"):
                yield Label("Schede Acquistate", id="titleResult")
                with HorizontalGroup():
                    yield Center(Button("Ricarica schede", "primary", id="reloadBet"))
                    yield Center(Button("Ricarica risultati", "primary", id="reloadDb"))
                yield VerticalScroll(id="resultTicketGroup")
            with TabPane("Impostazioni"):
                with VerticalGroup(id="mainSetting"):
                    with HorizontalGroup(id="settingGroup"):
                        yield Label("Username Telegram (PROMEMORIA)")
                        username = ""
                        try:
                            with open("telegram.user", "r", encoding="utf-8") as f:
                                username = f.read()
                        except FileNotFoundError:
                            username = ""

                        yield Input(placeholder="Username", id="telegram", value=username)
                    with HorizontalGroup(id="settingGroup2"):
                        yield Label("Tema Applicazione")
                        themesRaw = textual.theme.BUILTIN_THEMES
                        themesAvailable = []
                        for i in themesRaw.keys():
                            themesAvailable.append((i.title(), i))

                        yield Select(themesAvailable, allow_blank=False, value="textual-dark", id="themeSelect")
                with HorizontalGroup(id="groupAbout"):
                    yield Label(VERSION, id = "versionLabel")
                    with Right():
                        yield Button("Informazioni", id="openModalAbout")
        self.call_later(self.clear_cache)
        self.call_after_refresh(self.load_money)
        self.call_after_refresh(self.reload_db)
    def load_money(self):
        if os.path.exists("data/balance.enc"):
            with open("data/balance.enc", "r", encoding="utf-8") as f:
                tempbalance = json.loads(f.read())
        else:
            tempbalance = 50
            with open("data/balance.enc", "w", encoding="utf-8") as f:
                f.write(json.dumps(tempbalance))
        self.moneyloaded = True
        self.balance = tempbalance
        
    def watch_balance(self, newmoney):
        if self.moneyloaded:
            self.query_one("#balanceLab").update(f"Soldi: {newmoney}")
            print("Saving ",newmoney)
            with open("data/balance.enc", "w", encoding="utf-8") as f:
                    f.write(json.dumps(newmoney))
    def watch_betpay(self, newbetpay):
        try:
            self.query_one("#payoutLabel").update(f"Guadagno Potenziale: {newbetpay} €")
        except NoMatches:
            print("Payout not loaded still")
            pass

    async def reload_bets(self):
        bets = []
        if not os.path.exists("bets"):
            return
        for i in os.listdir("bets"):
            if i[(len(i)-3):] != "bet":
                continue
            print(f"loading {i}")
            bet = []
            with open("bets/"+i, "r", encoding="utf-8") as f:
                singlebet = json.loads(f.read())
                money = singlebet[0]
                bet.append(money)
                
                temp = {}
                for id, value in singlebet[1].items():
                    value[0] = OddApiNew.Game(**value[0])
                    temp[id] = [value[0], value[1]]
                bet.append(temp)
            bets.append(bet)
        group = self.query_one("#resultTicketGroup")
        await group.remove_children()
        print(bets)
        inde = 0
        for betObject in bets:
            print(f"betCaricata{bets.index(betObject)}")
            group.mount(TicketObject(betObject, inde, id=f"betCaricata{inde}"))
            inde += 1
    def reload_ticket(self):
        print(self.current_bet)
        group = self.query_one("#ticketGroup")
        group.remove_children()
        print(self.current_bet)
        for gamelul, selectedBet in self.current_bet.items():
                        print(selectedBet)
                        game = selectedBet[0]
                        group.mount(Collapsible(Label(f"Selezionata: {selectedBet[1]}\nQuotazione: {game.odds[associate[selectedBet[1]]]}"), title=f"{game.home} - {game.away} || {game.date}"))
    def clear_cache(self):
        self.odd_cache = {}
    async def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        nation = event.tab.label_text
        if nation == "Risultati":
            await self.reload_bets()
            return
        elif nation == "Scheda":
            self.reload_ticket()
            return
        elif nation == "Impostazioni":
            return
        else:
            print("Tab Activated ", nation, "--", self.old_nation)
            if nation == self.old_nation:
                return
            else:
                self.old_nation = nation
            containerName = "games"+nation
            league = leaguesDict[containerName][0]
            self.update_games(league, containerName)

    async def on_select_changed(self, event: Select.Changed):

        if event.select.id == "themeSelect":
            self.app.theme = event.value
            self.app.refresh()
            return

        if "bet" in event.select.id:
            betType = event.value
            if betType == self.old_bet:
                return
            else:
                self.old_bet = betType
            id = event.select.id
            nation = id.removeprefix("bet")
            select = "select"+nation
            bettype = event.select.parent.query_one("#bet"+nation).value
            league = event.select.parent.query_one("#"+select).value
            for key,value in leaguesDict.items():
                if league in value:
                    container = key
            print(league, container)
            betsel = None
            match betType:
                case "1x2":
                    betsel = 1
                case "Under/Over":
                    betsel = 2
                case "Entrambi Segnano":
                    betsel = 3
            self.query_one(f"#{container}").set_loading(True)
            self.update_games(league, container, betsel)
            self.query_one(f"#{container}").set_loading(False)
                    


        else:
            league = event.value
            print(league, self.rejectIndex)
            if league != "Serie A" and self.rejectIndex < len(leaguesDict)-1:
                print("Rejecting ", league)
                self.rejectIndex += 1
                return
            print("Getting ", league)
            
            for key,value in leaguesDict.items():
                if league in value:
                    container = key
            print(league, container)
            self.query_one(f"#{container}").set_loading(True)
            self.update_games(league, container)
            self.query_one(f"#{container}").set_loading(False)
    @work()
    async def update_games(self, league, containerName, typesel = 1):
        print("Doing ",typesel)
        
        self.query_one(f"#{containerName}").set_loading(True)
        keyleague = None
        match typesel:
            case 1:
                keyleague = league
            case 2:
                keyleague = league + "uo"
            case 3:
                keyleague = league + "gn"
        if keyleague in self.odd_cache.keys():
            odds = self.odd_cache[keyleague]
        else:
            match typesel:
                case 1:
                    odds = scraper.get_request(league)
                    self.odd_cache[league] = odds
                case 2:
                    odds = scraper.get_other_bet(league)
                    self.odd_cache[league + "uo"] = odds
                case 3:
                    odds = scraper.get_golng(league)
                    self.odd_cache[league + "gn"] = odds

        await self.query_one(f"#{containerName}").remove_children()
        print(odds)
        print(self.current_bet)
        if odds == []:
            self.query_one(f"#{containerName}").mount(Label("Nessuna Partita disponibile,  appena disponibili appariranno qui"))
        else:
            for gameData in odds:

                match typesel:
                    case 1:
                        odder = None
                        print(self.current_bet)
                        if f"{gameData.home}{gameData.away}{gameData.date}" in self.current_bet:
                            odder = ["1", "x", "2"].index(
                                self.current_bet[f"{gameData.home}{gameData.away}{gameData.date}"][1])
                        print(odder)
                        self.query_one(f"#{containerName}").mount(
                            GameObject(gameData, id=f"{sanitize_id(gameData.home)}_{sanitize_id(gameData.away)}",
                                       prepress=odder))
                    case 2:
                        odder = None
                        print(self.current_bet)
                        if f"{gameData.home}{gameData.away}{gameData.date}uo" in self.current_bet:
                            odder = ["Under", "Over"].index(self.current_bet[
                                                                f"{gameData.home}{gameData.away}{gameData.date}uo"][
                                                                1])
                        print(odder)
                        self.query_one(f"#{containerName}").mount(
                            GameObject(gameData, id=f"{sanitize_id(gameData.home)}_{sanitize_id(gameData.away)}_uo",
                            typebet=2, prepress=odder))
                    case 3:
                        odder = None
                        print(self.current_bet)
                        if f"{gameData.home}{gameData.away}{gameData.date}gn" in self.current_bet:
                            odder = ["Si", "No"].index(self.current_bet[
                                                                f"{gameData.home}{gameData.away}{gameData.date}gn"][
                                                                1])
                        print(odder)
                        self.query_one(f"#{containerName}").mount(
                            GameObject(gameData, id=f"{sanitize_id(gameData.home)}_{sanitize_id(gameData.away)}_gn",
                                       typebet=3, prepress=odder))


        self.query_one(f"#{containerName}").set_loading(False)
    def add_bet(self, game, odd, buttonid, typesel = 1):
        print(self.current_bet)
        afterkey = ""
        match typesel:
            case 1:
                afterkey = ""
            case 2:
                afterkey = "uo"
            case 3:
                afterkey = "gn"

        if f"{game.home}{game.away}{game.date}{afterkey}" in self.current_bet.keys():
            if self.current_bet[f"{game.home}{game.away}{game.date}"][1] != odd:
                self.current_bet[f"{game.home}{game.away}{game.date}{afterkey}"] = [game, odd]
                for button in self.query_one(f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}" if afterkey == "" else f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}_{afterkey}").query("Button"):
                    button.variant = "primary"
                self.query_one(f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}" if afterkey == "" else f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}_{afterkey}").query_one(f"#odd{odd}").query_one("Button").variant = "success"
            else:
                self.current_bet.pop(f"{game.home}{game.away}{game.date}{afterkey}")
                for button in self.query_one(f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}" if afterkey == "" else f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}_{afterkey}").query("Button"):
                    button.variant = "primary"
        else:
            self.current_bet[f"{game.home}{game.away}{game.date}{afterkey}"] = [game, odd]
            self.query_one(f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}" if afterkey == "" else f"#{sanitize_id(game.home)}_{sanitize_id(game.away)}_{afterkey}").query_one(f"#odd{odd}").query_one("Button").variant = "success"

    async def on_input_changed(self, event: Input.Changed):
        selected = event.input
        if selected.id ==  "soldiInput":
            if selected.value and selected.value != 0:
                totalmult = 1
                for bet in self.current_bet.values():
                    oddsel = bet[0].odds[associate[bet[1]]]
                    totalmult *= oddsel
                self.betpay = round(float(float(selected.value) * totalmult),2)
                print(self.betpay)
            else:
                self.betpay = "?"
        if selected.id == "telegram":
            with open("telegram.user", "w", encoding="utf-8") as f:
                f.write(selected.value)


    async def on_button_pressed(self, event: Button.Pressed):
        button = event.button
        print(button.id)
        if button.id == "buyButton":
            moneyValue = round(float(self.query_one("#soldiInput").value), 2)
            if moneyValue == 0 or moneyValue is None:
                self.app.push_screen(WarningDialogDefault("Inserisci un valore di soldi con cui piazzare la scommessa, diverso da 0!"))
                return
            self.saveBet(moneyValue)
        elif button.id == "reloadBet":
            await self.reload_bets()
        elif button.id == "reloadDb":
            print("reloading")
            button.parent.parent.parent.query_one("#resultTicketGroup").set_loading(True)
            self.call_after_refresh(self.reload_db, True)
        elif button.id == "openModalAbout":
            await self.app.push_screen(AboutModal())
    def removeLoading(self):
        self.query_one("#resultTicketGroup").set_loading(False)
    @work(thread=True)
    def reload_db(self, override = False):
        print(f"Override {override}!!!")
        for id, values in leaguesDict.items():
            for i in values:
                value = scraper.cache_db(i, override)
                print("Creating DB")
                print(value)
                databaseGame[i] = value
        self.reload_bets()
        self.app.call_from_thread(self.removeLoading)



    def saveBet(self, money):
        index = 0
        if len(self.current_bet) == 0:
            self.app.push_screen(WarningDialogDefault("Non puoi piazzare una scommessa vuota!"))
            return
        if money > self.balance:
            self.app.push_screen(WarningDialogDefault("Soldi insufficienti per piazzare la scommessa!"))
            return
        else:
            self.balance -= money
        if os.path.exists("bets"):
            for file in os.listdir("bets"):
                if "memo" in file: continue
                num = int(file.removesuffix(".bet"))
                if num >= index:
                    index = num + 1
        else:
            os.mkdir("bets")
            index = 0
        stringToWrite = ""
        with open(f"bets/{index}.bet", "w", encoding="utf-8") as f:
            bettowrite = {}
            for id, value in self.current_bet.items():
                print(value[0])
                game = asdict(value[0])
                odd = value[1]
                bettowrite[id] = [game, odd]
                stringToWrite += f"| {date_formatString(game["date"])} |\n\t{game["home"]}-{game["away"]} || {odd} | {game["odds"][associate[odd]]}\n\n"
                
            bet = [money, bettowrite]
            content = json.dumps(bet, indent=4)
            f.write(content)
        stringToWrite += f"Spesa: {money} € >> Potenziale: {self.betpay} €"
        with open(f"bets/memoBet{index}.txt", "w", encoding="utf-8") as f:
            f.write(stringToWrite)

        TELEGRAM_TOKEN = "8261199286:AAGDEycUALaw1UTCK0Wpe9m73M_kRunJZ84"
        username = None
        canTelegram = True
        try:
            with open("telegram.user", "r", encoding="utf-8") as f:
                username = f.read()
        except FileNotFoundError:
            canTelegram = False
        if not username:
            canTelegram = False
        print(canTelegram)
        print(username)
        if canTelegram:
            url1 = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            send1 = requests.get(url1)
            print(send1.content)
            cnts = json.loads(send1.content)
            chatid = None
            for event in cnts["result"]:
                print(event)
                if event["message"]["chat"]["first_name"] == username:
                    chatid = event["message"]["chat"]["id"]
            if chatid != None:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                params = {"chat_id": chatid, "text": f"CREATA SCOMMESSA IN DATA ODIERNA\n{stringToWrite}"}
                send = requests.get(url, params=params)
                print(send.status_code)

        self.current_bet = {}
        self.reload_ticket()
        

class AboutModal(Screen):
    text = """## NeoBetSim
    Applicazione creata da: Giuseppe Leonardi Rovetto
    
    Ho iniziato a sviluppare questa app perchè volevo un applicazione che avesse:
    - Simulazione realistica di scommesse
    - Quote reali
    
    Se trovi bug o hai una domanda contattami su [Github](https://github.com/leonardig08/BetSim)
    
    MIT License

    Copyright (c) 2025 Giuseppe Leonardi
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE."""
    def compose(self) -> ComposeResult:
        yield Markdown(self.text)
        yield Button("OK" ,id="exitPage")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "exitPage":
            self.dismiss()



class BetSim(App):
    CSS_PATH = "main.tcss"
    
    def compose(self):

        yield Header(show_clock=True)
        self.push_screen(SplashScreen())
        self.odd_data = None
        self.dataLoaded = False
        
        self.call_later(self.load_data)

    def on_mount(self):
        self.title = """| ⚽ NeoBetSim 2026 ⚽ |"""
        self.sub_title = "Scommesse Simulate Nel Terminale"
    
    def load_main_screen(self):
        if self.dataLoaded:
            self.pop_screen()
            self.push_screen(MainAppScreen())

    @work(thread=True)
    def load_data(self):
        global scraper
        create_map()
        scraper = OddApiNew.BetAPI()
        for id, values in leaguesDict.items():
            for i in values:
                databaseGame[i] = scraper.cache_db(i)
        with open("api/map.json", "r", encoding="utf-8") as f:
            global mapNames
            mapNames = json.loads(f.read())

        print(mapNames)
        self.dataLoaded = True
        self.call_from_thread(self.load_main_screen)
        
    
            

        
if __name__ == "__main__":
    app = BetSim()
    app.run()


