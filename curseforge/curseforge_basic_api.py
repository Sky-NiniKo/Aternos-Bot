import time

import requests
from markdownify import markdownify


class CurseForgeAPI:
    endpoint = 'https://api.curseforge.com'
    mod_id = None
    last_version = None
    cooldown: dict = {'last_file': {'args': (), 'last_result': dict(), 'when_run': 0.0}}

    def __init__(self, api_key: str) -> None:
        self.headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }

        r = requests.get(f'{self.endpoint}/v1/games', headers=self.headers)
        if r.ok:
            pass
        elif r.status_code == 403:
            raise ValueError("API key is not valid")
        elif r.status_code == 500:
            raise ConnectionError("Curseforge servers have internal errors")
        else:
            raise ConnectionError(f"Connection to the Curseforge API fail. Error code: {r.status_code}")

    def track_mod(self, mod_id):
        self.mod_id = mod_id

    def get_game_id(self, name: str) -> int:
        r = requests.get(f'{self.endpoint}/v1/games', headers=self.headers)
        for game in r.json()['data']:
            if game['slug'] == name.lower().replace(' ', '-'):
                return game['id']

    def get_mod_id(self, name: str, game: int = None) -> int:
        game = '' if game is None else f"&gameId={game}"
        r = requests.get(f'{self.endpoint}/v1/mods/search?searchFilter={name}{game}', headers=self.headers)
        data = r.json()['data']
        if len(data) != 1:
            raise FileNotFoundError("The name is too vague use the argument game or precise the name.")
        return data[0]['id']

    def get_last_file(self, mod: int = None) -> dict:
        if mod is None:
            if self.mod_id is not None:
                mod = self.mod_id
            else:
                raise ValueError("The argument mod must be specified")

        if self.cooldown['last_file']['args'] == (mod,) and self.cooldown['last_file']['when_run'] + 5 > time.time():
            return self.cooldown['last_file']['last_result']

        data = requests.get(f'{self.endpoint}/v1/mods/{mod}', headers=self.headers).json()['data']['latestFiles'][-1]
        self.cooldown['last_file'] = {'args': (mod,), 'last_result': data, 'when_run': time.time()}
        if self.mod_id is not None:
            self.last_version = data['displayName']
        return data

    def get_files(self, mod: int = None) -> list:
        if mod is None:
            if self.mod_id is not None:
                mod = self.mod_id
            else:
                raise ValueError("The argument mod must be specified")
        r = requests.get(f'{self.endpoint}/v1/mods/{mod}/files', headers=self.headers)
        return r.json()['data']

    def get_file_changelog(self, file: int, mod: int = None) -> str:
        if mod is None:
            if self.mod_id is not None:
                mod = self.mod_id
            else:
                raise ValueError("The argument mod must be specified")
        r = requests.get(f'{self.endpoint}/v1/mods/{mod}/files/{file}/changelog', headers=self.headers)
        return markdownify(r.json()['data'])

    def is_a_new_version(self):
        if self.mod_id is None:
            raise ValueError("The argument mod must be specified")

        return self.last_version != self.get_last_file()['displayName']


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv(dotenv_path="../.env")
    API_KEY = os.getenv("CURSEFORGE_API_KEY")

    API = CurseForgeAPI(API_KEY)
    minecraft = API.get_game_id("minecraft")
    ATM7 = API.get_mod_id("ATM7", game=minecraft)
    changelog = API.get_file_changelog(ATM7, API.get_last_file(ATM7)['id'])
    print(changelog)

