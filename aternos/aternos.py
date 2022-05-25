import asyncio
import os
import re
import time
import traceback as tb
from typing import Union

from playwright._impl import _api_types as api_types
from playwright.async_api._generated import BrowserContext, Page
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async


def get_full_path(path):
    if path[0] == "/" or path[1] == ":":
        return path
    else:
        return os.path.dirname(os.path.realpath(__file__)) + "/" + path


async def do_stuff_periodically(interval, periodic_function):
    while True:
        await asyncio.gather(
            asyncio.sleep(interval),
            periodic_function(),
        )


class Aternos:
    browser: BrowserContext
    page: Page

    last_info = {}
    updater: asyncio.Task
    update_receivers = []
    get_update_started = False

    alive_keeper: asyncio.Task

    hostname = 'https://aternos.org'
    timeout = {"default": 10000, "start": 1200000, "stop": 60000}
    server_state = {'offline': 'div.statuslabel i.fas.fa-stop-circle',
                    'online': 'div.statuslabel i.fas.fa-play-circle',
                    'waiting': 'div.statuslabel i.fas.fa-clock',
                    'loading starting': 'div.statuslabel i.fas.fa-spinner-third'}

    def __init__(self, user: str, password: str, ublock_origin_path='uBlock0.chromium',
                 user_data_dir='tmp/test-user-data-dir'):
        self.user = user
        self.password = password
        self.ublock_origin_path = get_full_path(ublock_origin_path)
        self.user_data_dir = get_full_path(user_data_dir)

    async def find_server(self, server_id):
        if server_id is None:
            return self.page.locator('.server-body >> nth=0')
        try:
            return self.page.locator(f'[data-id="{server_id}"]')
        except api_types.TimeoutError:
            return None

    async def get_queue(self):
        info = await self.get_info()
        return info['queue']

    async def get_info(self) -> dict:
        info = await self.page.evaluate("lastStatus")

        info['motd'] = re.sub(r"[\\][a-zA-Z0-9]{5}", lambda match: chr(int(match.group(0)[2:], 16)),
                              info['motd'])  # convert unicode : "Pr\\u00E9parez vous" -> "Préparez vous"

        info["players"] = {"current": info["players"], "max": info["slots"]}
        del info["slots"]

        if info.get("maxram"):
            info["ram"] = {"used": info["ram"], "max": info["maxram"]}
        else:
            info["ram"] = {"used": info["ram"]}
        return info

    async def get_countdown(self) -> Union[int, None]:
        if timer := await self.get_text(".queue-time"):
            try:
                minutes, seconds = map(int, timer.split(':'))
                return minutes * 60 + seconds
            except ValueError:
                return

    async def get_tps(self):
        if (tps := await self.get_text(".js-tps")).isdigit():
            return int(tps)

    async def get_text(self, selector) -> str:
        return (await self.page.locator(selector).inner_text()).strip()

    async def wait_for_first(self, timeout, *selectors):
        try:
            elements = [
                asyncio.create_task(
                    self.page.wait_for_selector(
                        selector, timeout=timeout, state="visible"
                    )
                )
                for selector in selectors
            ]

            await asyncio.wait(elements, return_when=asyncio.FIRST_COMPLETED)
            return True
        except asyncio.TimeoutError:
            return False

    async def connect(self, main_loop: asyncio.AbstractEventLoop, server_id=None):
        start_time = time.time()
        info = {}

        try:
            playwright = await async_playwright().start()
            args = [f"--disable-extensions-except={self.ublock_origin_path}",
                    f"--load-extension={self.ublock_origin_path}"]
            self.browser = await playwright.chromium.launch_persistent_context(self.user_data_dir, headless=False,
                                                                               args=args, locale='en-US')
            self.page = await self.browser.new_page()
            await stealth_async(self.page)

            await self.page.goto(self.hostname + '/go')
            await self.page.type('#user', self.user)
            await self.page.type('#password', self.password)
            await self.page.click('#login')

            try:
                await self.page.wait_for_selector('.page-servers', timeout=self.timeout['default'])
            except api_types.TimeoutError:
                error = await self.get_text('.login-error')
                if error:
                    raise Exception(error)

            server = await self.find_server(server_id)
            if not server:
                raise Exception(f'Server {server_id} not found')

            await server.click()
            await self.page.wait_for_load_state("networkidle")

            choices = await self.page.query_selector('#accept-choices')
            if choices:
                await choices.click()

            await self.page.wait_for_selector('.btn.btn-white')
            await self.page.click('.btn.btn-white')
            await self.page.wait_for_selector('div.btn.btn-white i.far.fa-sad-tear', state='hidden',
                                              timeout=self.timeout['default'])

            self.alive_keeper = main_loop.create_task(self.keepalive())

            info = await self.get_info()
        except Exception as e:
            info['error'] = ''.join(tb.format_exception(None, e, e.__traceback__))
        finally:
            info['elapsed'] = time.time() - start_time
            return info

    async def keepalive(self):
        while True:
            await self.page.wait_for_selector(".btn.btn-white.MNjhsfJlwYUcNrLaBpLTqTVRnYiNhmbueuINeAGLX",
                                              timeout=0, state='visible')
            await self.page.click(".btn.btn-white.MNjhsfJlwYUcNrLaBpLTqTVRnYiNhmbueuINeAGLX")
            await self.page.wait_for_selector('div.btn.btn-white i.far.fa-sad-tear', state='hidden', timeout=0)

    async def get_update(self):
        new_info = await self.get_info()
        if self.last_info != new_info:
            self.last_info = new_info

            receivers = [
                asyncio.create_task(receiver(new_info))
                for receiver in self.update_receivers
            ]

            await asyncio.wait(receivers, return_when=asyncio.ALL_COMPLETED)

    def on_update(self, func, main_loop: asyncio.AbstractEventLoop):
        self.update_receivers.append(func)
        if not self.get_update_started:
            self.updater = main_loop.create_task(do_stuff_periodically(1, self.get_update))
            self.get_update_started = True

    async def start(self, wait=True):
        try:
            if not await self.page.query_selector('#start'):
                return {"no effect": "the start button can not be found"}

            await self.page.click('#start')
            await self.page.wait_for_timeout(1000)

            confirm_start = '.alert-buttons.btn-group a.btn.btn-green'
            try:
                await self.page.wait_for_selector(confirm_start, timeout=500)
                await self.page.click(confirm_start)
            except api_types.TimeoutError:
                pass

            if 'server' not in self.page.url:
                await self.page.goto('https://aternos.org/server')

            await self.wait_for_first(self.timeout['start'], self.server_state["online"], self.server_state["waiting"])

            if wait and (info := await self.get_info())['queue']:
                await self.page.wait_for_selector('#confirm', timeout=info['queue']["minutes"] * 60000, state="visible")
                await self.page.click('#confirm')

            return await self.get_info()
        except Exception as e:
            return {'error': ''.join(tb.format_exception(None, e, e.__traceback__))}

    async def close(self):
        self.updater.cancel()
        self.alive_keeper.cancel()
        await self.browser.close()


if __name__ == '__main__':
    from pprint import pprint
    from dotenv import load_dotenv

    load_dotenv(dotenv_path="../.env")
    user = os.getenv("ATERNOS_USER")
    password = os.getenv("ATERNOS_PASSWORD")

    API = Aternos(user=user, password=password)


    async def main():
        pprint(await API.connect(asyncio.get_event_loop()))
        await API.page.screenshot(path='url.png')
        await API.close()


    asyncio.run(main())
