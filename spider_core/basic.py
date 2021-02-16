# -*- coding: utf-8 -*-

import random
import os
import asyncio
import json
import pyautogui
from pyppeteer import launch


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DRIVER_PATH = os.path.join(BASE_PATH, "env/Chromium.app/Contents/MacOS/Chromium")
PROJECT_PATH = os.path.dirname(BASE_PATH)
COOKIES_PATH = os.path.join(PROJECT_PATH, "data")
USER_DATA_PATH = os.path.join(PROJECT_PATH, "user_data")

if not os.path.exists(DRIVER_PATH):
    raise FileNotFoundError
if not os.path.exists(COOKIES_PATH):
    os.makedirs(COOKIES_PATH)

COOKIES_FILE = os.path.join(COOKIES_PATH, "cookies.json")


class BasePool(object):

    _cache = list()

    def random_get(self):
        return random.choice(self._cache)


class BaseSpider(object):

    _name = ""
    _window_width = None
    _window_height = None

    def __init__(self, is_headless=False, loop=None, driver_path=None, cookies_path=None, user_data_path=None,
                 **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        if driver_path is None:
            driver_path = DRIVER_PATH
        if cookies_path is None:
            cookies_path = COOKIES_FILE
        if user_data_path is None:
            user_data_path = USER_DATA_PATH
        self._user_data_path = user_data_path
        self._driver_path = driver_path
        self._loop = loop
        self._is_headless = is_headless
        self._options = kwargs
        self._cookies_path = cookies_path
        self._window_width, self._window_height = pyautogui.size()
        self._cookies = None
        self._proxy = None

    async def _save_cookie(self, cookies):
        with open(self._cookies_path, 'w', encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)

    async def _load_cookie(self):
        with open(self._cookies_path, encoding="utf-8") as f:
            self._cookies = json.load(f)

    async def _update_cookies(self):
        cookies = await self._page.cookies()
        await self._save_cookie(cookies)
        self._cookies = cookies
        await self._set_cookies()

    async def _set_cookies(self):
        for cookie in self.cookies:
            await self._page.setCookie(cookie)

    @property
    def cookies(self):
        return self._cookies

    @staticmethod
    async def _load_ua(page) -> None:
        """加载user-agent池子"""
        from spider_core.user_agent_pool import user_agent_manager
        await page.setUserAgent(user_agent_manager.random_get())

    @staticmethod
    def _load_ip(args: list) -> list:
        """加载IP代理池子"""
        ip_port = ()
        ip_port = ":".join(ip_port)
        if ip_port:
            proxy = f"--proxy-server=http://{ip_port}"
            args.append(proxy)
        return args

    async def _init_spider(self):
        window_size = ",".join((str(self._window_width), str(self._window_height)))
        args = ['--no-sandbox', '--disable-infobars', f'--window-size={window_size}']
        args = self._load_ip(args)
        browser = await launch(args=args, headless=self._is_headless, userDataDir=self._user_data_path, loop=self._loop,
                               executablePath=self._driver_path, **self._options)
        page = await browser.newPage()
        # 防止检测webdriver
        await page.evaluateOnNewDocument('()=>{Object.defineProperties(navigator,{webdriver:{get:()=>false}})}')
        await self._load_ua(page)
        await page.setViewport({'width': self._window_width, 'height': self._window_height})
        self._page = page
        self._browser = browser

    async def _handler(self):
        raise NotImplementedError

    async def start(self):
        await self._init_spider()
        try:
            await self._handler()
            await self.stop()
        except:
            await self.stop()
            raise

    async def stop(self):
        await self._update_cookies()
        await self._page.close()
        if self._page.isClosed():
            await self._browser.close()

    @property
    def short_random(self):
        return self._get_random()

    @property
    def long_random(self):
        return self._get_random(5, 10)

    @staticmethod
    def _get_random(start=1, end=5):
        return random.uniform(start, end)

    def __repr__(self):
        return self._name

    async def _input_search(self, select, text, sleep=0.08):
        await self._page.focus(select)
        await self._page.keyboard.type(text, {"delay": sleep * 1000})  # 输入文本字符（推荐使用）
        await self._page.keyboard.press('Enter')

    async def _move_and_click_mouse(self):
        pass

    async def _scroll(self, step=500, once=False, bottom=True):
        if once is False:
            scroll_len_js = "document.body.clientHeight"
            if bottom:
                scroll_step_js = "(step)=>{document.scrollingElement.scrollTop = document.scrollingElement.scrollTop " \
                                 "+ step}"
            else:
                scroll_step_js = "(step)=>{document.scrollingElement.scrollTop = document.scrollingElement.scrollTop " \
                                 "- step}"
            client_height = await self._page.evaluate(scroll_len_js)  # 5206
            # 计算滚动条滑动到最下面需要的次数
            scroll_distance = client_height-self._window_height
            count = int(scroll_distance/step) + 1
            for i in range(count):
                await self._page.evaluate(scroll_step_js, step)
                await asyncio.sleep(self.short_random)
        else:
            await self._page.evaluate("window.scrollBy(0, document.body.scrollHeight)")  # 一步到位

    async def _save_data(self, result):
        pass
