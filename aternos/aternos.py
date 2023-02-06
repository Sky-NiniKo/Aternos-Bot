import json
import logging
import random
import re
import string
import time
import urllib.parse
import _thread
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Any

import cloudscraper
import websocket as websocket_client
from js2py import eval_js6
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

domain = "aternos.org"
base_url = f"https://{domain}"
login = {'user': 'Demare_maintenant',
         'password': 'f854a68c1d1506d8bf5b2edc0ad114db'
         }


def random_string(length: int) -> str:
    # return Array(length + 1).join(f'{Math.random().toString(36)}00000000000000000'.slice(2, 18)).slice(0, length)
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def enum2condition(enum: Enum):
    return lambda message: message.get(enum.type.value) == enum.value


class AvailableStreams(Enum):
    type = "stream"
    CONSOLE = "console"
    STATS = "stats"
    TPS = "tick"
    MEMORY = "heap"


class AvailableTypes(Enum):
    type = "type"
    STATUS = "status"
    TPS = "tick"
    MEMORY = "heap"


class HasAjaxToken:
    def __init__(self, cookie_prefix: str, ajax_token: str = None):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.cookie_prefix = cookie_prefix
        if ajax_token:
            self.ajax_token = ajax_token
        else:
            logging.warning("Don't forget to set ajax_token as soon as possible with set_ajax_token.")

    def set_ajax_token(self, ajax_token: str) -> None:
        """
        To be use when you need self.scraper to get ajax_token and so you cannot set ajax_token in the __init__
        Use carefully tough
        :param ajax_token: string
        """
        self.ajax_token = ajax_token
        logging.warning("You can safely ignore the line above because you have properly set ajax_token.")

    def generate_ajax_token(self, url: str) -> str:
        key = random_string(16)
        value = random_string(16)
        # document.cookie = COOKIE_PREFIX + "_SEC_" + key + "=" + value + ";path=" + url;
        self.scraper.cookies[f"{self.cookie_prefix}_SEC_{key}"] = value
        self.scraper.cookies["path"] = url
        return f"{key}:{value}"

    def build_url(self, path: str, data: dict = None, ajax_token: str = None) -> str:
        if data is None:
            data = {}
        if ajax_token is None:
            ajax_token = self.ajax_token
        data["SEC"] = self.generate_ajax_token(f"{base_url}/{path}")
        data["TOKEN"] = ajax_token
        return f"{base_url}/{path}?{urllib.parse.urlencode(data)}"


class AternosServer(HasAjaxToken):
    websocket: websocket_client.WebSocketApp = None

    def __init__(self, identifier: str, cookies: RequestsCookieJar, ajax_token: str, name: str = None):
        super().__init__(cookie_prefix="ATERNOS", ajax_token=ajax_token)
        self.id = identifier
        self.scraper.cookies.update(cookies)
        self.get_server_cookie()
        self.name = name or self.get_name()
        self.condition2subscribers: dict[Any, list] = {}
        self.open_steams: dict[AvailableStreams, bool] = {stream: False for stream in AvailableStreams}
        self.subscribe(self._set_info, enum2condition(AvailableTypes.STATUS))
        self.subscribe(self._set_tps, enum2condition(AvailableStreams.TPS))
        self.connect_websocket()

    def connect_websocket(self) -> websocket_client.WebSocketApp:
        cookie = ';'.join(
            [
                f'{name}={value}'
                for (name, value) in self.scraper.cookies.get_dict(domain).items()
            ]
        )

        # websocket_client.enableTrace(True)
        self.websocket = websocket_client.WebSocketApp(
            f"wss://{domain}/hermes/",
            cookie=cookie,
            header=self.scraper.headers,
            on_open=self.keep_alive,
            on_message=self.on_message,
            on_error=logging.error
        )

        _thread.start_new_thread(self.websocket.run_forever, ())
        return self.websocket

    @staticmethod
    def keep_alive(websocket):
        def run():
            while True:
                time.sleep(49)
                websocket.send('{type:"❤"}')

        _thread.start_new_thread(run, ())

    def on_message(self, _websocket, message):
        message: dict = json.loads(message)

        for condition, functions_to_call in self.condition2subscribers.items():
            if condition(message):
                for function in functions_to_call:
                    function(message)

    def get_server_cookie(self):
        # Real code
        """url = self.build_url("panel/ajax/friends/access.php")
        response = self.scraper.post(url=url, data={"id": self.id})
        if response.json().get("success") is not True or not response.ok:
            raise NotImplementedError
        return response.cookies"""

        # But its do just that
        self.scraper.cookies.set('ATERNOS_SERVER', self.id, domain=domain)
        return {'ATERNOS_SERVER': self.id}

    def start(self) -> None:
        response = self.scraper.get(
            self.build_url("panel/ajax/start.php", {"headstart": 0, "access-credits": 0})
        ).json()
        if response["success"] is False:
            match response["error"]:
                case "file":
                    logging.warning("Server side error!")
                case "eula":
                    logging.warning("EULA not accepted")
                case "wrongversion":
                    logging.warning("Server software not good")
                case "currently":
                    logging.info("Server currently starting...")
                case "already":
                    logging.info("Server already started")
                case _:
                    raise NotImplemented

    def stop(self) -> None:
        response = self.scraper.get(self.build_url("panel/ajax/stop.php"))
        if not response.ok or response.json()["success"] is False:
            raise NotImplemented

    def restart(self) -> None:
        pass

    def open_stream(self, stream: AvailableStreams):
        if not self.open_steams[stream]:
            self.open_steams[stream] = True
            self.websocket.send(f'{{"stream":"{stream.value}","type":"start"}}')

    def close_stream(self, stream: AvailableStreams):
        if self.open_steams[stream]:
            self.open_steams[stream] = False
            self.websocket.send(f'{{"stream":"{stream.value}","type":"stop"}}')

    # for compatibility reason
    def _set_info(self, message: dict) -> None:
        self.info: dict = json.loads(message["message"])

        self.info["motd"] = re.sub(r"\\[a-zA-Z0-9]{5}", lambda match: chr(int(match.group(0)[2:], 16)),
                                   self.info['motd'])  # convert unicode : "Pr\\u00E9parez vous" -> "Préparez vous"

        self.info["players"] = {"current": self.info["players"], "max": self.info["slots"]}
        del self.info["slots"]

        if self.info.get("maxram"):
            self.info["ram"] = {"used": self.info["ram"], "max": self.info["maxram"]}
        else:
            self.info["ram"] = {"used": self.info["ram"]}

        if self.info.get("countdown"):
            self.info["countdown"] = datetime.now() + timedelta(seconds=self.info["countdown"])

        # here because _set_info is only run when this is a 'type: "status"' message
        match self.info.get("status"):
            case 1:
                for stream in (AvailableStreams.TPS, AvailableStreams.MEMORY):
                    self.open_stream(stream)
                self.close_stream(AvailableStreams.CONSOLE)
            case 2:
                self.open_stream(AvailableStreams.CONSOLE)
            case 3 | 4:
                for stream in (AvailableStreams.TPS, AvailableStreams.MEMORY):
                    self.close_stream(stream)

    # for compatibility reason
    def get_info(self) -> dict:
        return self.info or {}

    def _set_tps(self, message: dict) -> None:
        self.mspt: int = message["data"]["averageTickTime"]

    def get_tps(self) -> dict | None:
        return (
            {"tps": max(1 / (self.mspt / 1000), 20), "mspt": self.mspt}
            if self.open_steams[AvailableStreams.TPS]
            else None
        )

    def subscribe(self, function, condition=lambda _: True) -> None:
        """
        Subscribe a function to a stream of messages sends by Aternos
        :param function: The function that you want to run when a message is received
        :param condition: Function that the message and return true if the message should be transmitted
        :return: None
        """
        if condition not in self.condition2subscribers:
            self.condition2subscribers[condition] = []
        self.condition2subscribers[condition].append(function)

    def get_countdown(self) -> int | None:
        return (
            (self.info["countdown"] - datetime.now()).seconds
            if self.info.get("countdown")
            else None
        )

    def get_name(self) -> str:
        raise NotImplemented

    def __str__(self):
        return f"#{self.id}: {self.name}"


class AternosAccount(HasAjaxToken):
    servers: List[AternosServer] = []

    def __init__(self, user: str = None, password: str = None, login_data: dict = None):
        if (user is None or password is None) and login_data is None:
            raise ValueError("Provide login data!")
        super().__init__(cookie_prefix="ATERNOS")
        self.set_ajax_token(self.get_ajax_token())
        self.login_data = login_data or {'user': user, 'password': password}
        self.get_session_cookie()
        self.get_servers()

    def get_ajax_token(self) -> str:
        login_page = self.scraper.get(f"{base_url}/go")
        if not login_page.ok:
            raise ConnectionError("Login page not accessible")
        soup = BeautifulSoup(login_page.content, "html.parser")
        obfuscated_javascript = soup.find("script", dict(type="text/javascript")).text
        # ...{AJAX_TOKEN=condition?if_true:if_false;}...
        condition, if_true, if_false = re.findall(r"\{([^?]+)?([^:]+):([^;}]+);", obfuscated_javascript)[0]
        if_true, if_false = eval_js6(if_true[1:]), eval_js6(if_false)
        is_true = True
        for part in re.findall(r"(&&|\|\||!)", condition):
            match part:  # Thing between parts are always True
                case "!":
                    is_true = not is_true
                case "||":
                    is_true = True
                case _:
                    pass
        return if_true if is_true else if_false

    def get_session_cookie(self) -> RequestsCookieJar:
        url = self.build_url("panel/ajax/account/login.php")
        response = self.scraper.post(url=url, data=self.login_data)
        if response.json().get("success") is not True or not response.ok:
            raise NotImplementedError
        return response.cookies

    def get_servers(self):
        servers_page = self.scraper.get(f"{base_url}/servers")
        if not servers_page.ok:
            raise ConnectionError("Cannot access /servers")
        soup = BeautifulSoup(servers_page.content, "html.parser")
        servers = soup.find("div", class_="servers").findChildren("div", recursive=False)
        for server in servers:
            self.servers.append(AternosServer(
                identifier=server.find("div", class_="server-id").text.strip()[1:],  # .strip() -> '#id'
                cookies=self.scraper.cookies.copy(),
                ajax_token=self.ajax_token,
                name=server.find("div", class_="server-name").text.strip()
            ))


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    account = AternosAccount(login_data=login)
    for one_server in account.servers:
        logging.info(one_server)
        one_server.subscribe(logging.info)
    account.servers[0].start()
    time.sleep(60)
