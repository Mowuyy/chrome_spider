# -*- coding: utf-8 -*-

import asyncio
from asyncio import CancelledError
from pyppeteer.errors import NetworkError
from spider_core.basic import BaseSpider

"""
1、IP代理池
2、ua池
3、cookie池
批量真实账号登录维护cookie池
"""


class SaveListPageResult:

    __slots__ = ("price", "sale_num", "title_name", "title_link", "addr", "shop_name", "shop_link")

    def __init__(self, price, sale_num, title_name, title_link, addr, shop_name, shop_link):
        self.price = price
        self.sale_num = sale_num
        self.title_name = title_name
        self.title_link = title_link
        self.addr = addr
        self.shop_name = shop_name
        self.shop_link = shop_link

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)


class TaobaoSpider(BaseSpider):

    _name = "taobao"
    _login_url = 'https://login.taobao.com/member/login.jhtml?redirectURL=https://www.taobao.com/'
    _index_url = 'https://www.taobao.com/'

    def __init__(self, is_headless=False, qrcode_login=True, loop=None, driver_path=None,
                 cookies_path="./data/cookies.json", **kwargs):
        super().__init__(is_headless=is_headless, loop=loop, driver_path=driver_path, cookies_path=cookies_path,
                         **kwargs)
        self._qrcode_login = qrcode_login
        self._cookie_login = kwargs.get("cookie_login", False)

    async def _load_login_page(self):
        """加载登录页面"""
        await self._page.goto(self._login_url)
        await asyncio.sleep(self.short_random)
        # 防webdriver反爬
        # await self._page.evaluate('()=>{Object.defineProperties(navigator,{webdriver:{get:()=>false}})}')
        # await self._page.evaluate('()=>{window.navigator.chrome={runtime: {}}}')
        # await self._page.evaluate("()=>{Object.defineProperty(navigator,'languages',{get:()=>['en-US','en'})}")
        # await self._page.evaluate("()=>{Object.defineProperty(navigator,'plugins',{get:()=>[1, 2, 3, 4, 5,6]})}")
        # await asyncio.sleep(self.short_random)

    async def _login_by_account(self):
        """账号登录，手动跳转到淘宝首页"""
        username = self._options.get("username")
        password = self._options.get("password")
        await self._page.click("div.login-blocks.login-switch-tab > a.password-login-tab-item")  # 点击密码登陆（嵌套选择器）
        await asyncio.sleep(self.short_random)
        await self._page.type('#fm-login-id', username)  # 输入账号（id选择器）
        await asyncio.sleep(self.short_random)
        await self._page.type('#fm-login-password', password)  # 输入密码
        await asyncio.sleep(self.short_random)
        await self._page.click(".fm-button.fm-submit.password-login")  # 点击登录（class选择器.）
        # 问题1：频繁登录会弹出最近买过什么商品及地址进行身份验证,解决：手动登录一次后不会出现该情况
        await asyncio.sleep(self.long_random)
        self._cookies = await self._page.cookies()
        # await self._save_cookie(self._cookies)
        # await self._page.click("#J_SiteNavHome > div.site-nav-menu-hd > a")  # 点击淘宝首页，可通过js加载click（防止报错）
        # await asyncio.sleep(self.long_random)
        print("账号登录成功!")

    async def _login_by_qrcode(self):
        """扫码登录，自动跳转到淘宝首页"""
        await self._page.click("#login > div.corner-icon-view.view-type-qrcode > i.iconfont.icon-qrcode")  # 点击手机扫码登录
        await asyncio.sleep(self.long_random)  # 掏出手机扫码
        self._cookies = await self._page.cookies()
        print("扫码登录成功!")

    async def _login_by_cookies(self):
        """加载cookies登录"""
        await self._page.goto(self._index_url)
        await asyncio.sleep(self.short_random)
        await self._load_cookie()
        await self._set_cookies()
        print("cookie登录成功!")

    async def _crawl(self):
        """业务逻辑"""
        await asyncio.sleep(self.long_random)
        key_words = input("请输入您要搜索的关键词：")
        await self._input_search("#q", key_words)
        await asyncio.sleep(self.long_random)
        await self._page.click("li.sort > a[title='销量从高到低']")
        await asyncio.sleep(self.long_random)
        await self._scroll()
        await self._scroll(bottom=False)
        await asyncio.sleep(self.long_random)
        # 获取列表数据
        result = await self._get_list_page_info()
        # 保存列表页数据
        await self._save_data(result)

    async def _get_list_page_info(self):
        result = list()
        element_list = await self._page.querySelectorAll("div.item.J_MouserOnverReq")
        for item in element_list:
            price = await item.querySelector("div.row.row-1.g-clearfix > div.price.g_price.g_price-highlight > strong")
            price = await self._page.evaluate('(element) => element.textContent', price)
            sale_num = await item.querySelector("div.row.row-1.g-clearfix > div.deal-cnt")
            sale_num = await self._page.evaluate('(element) => element.textContent', sale_num)

            title = await item.querySelector("div.row.row-2.title > a")
            title_name = await self._page.evaluate('(element) => element.textContent', title)
            title_link = await (await title.getProperty("href")).jsonValue()

            addr = await item.querySelector("div.row.row-3.g-clearfix > div.location")
            addr = await (await addr.getProperty("textContent")).jsonValue()
            shop = await item.querySelector("div.row.row-3.g-clearfix > div.shop > a")
            shop_name = await (await shop.getProperty("textContent")).jsonValue()
            shop_link = await (await shop.getProperty("href")).jsonValue()

            obj = SaveListPageResult(sale_num.strip(), price.strip(), title_name.strip(), title_link.strip(),
                                     addr.strip(), shop_name.strip(), shop_link.strip())
            result.append(obj)
            print(obj.price, obj.sale_num, obj["title_name"], obj.title_link, obj.addr, obj.shop_name, obj.shop_link)
            print("=" * 100)
        return result

    async def _handler(self):
        if not self._cookie_login:
            await self._load_login_page()
            if self._qrcode_login:
                await self._login_by_qrcode()
            else:
                await self._login_by_account()
            await self._save_cookie(self._cookies)
        else:
            await self._login_by_cookies()
        await self._crawl()


def install_info():
    import pyppeteer.chromium_downloader
    print('默认版本是：{}'.format(pyppeteer.__chromium_revision__))
    print('可执行文件默认路径：{}'.format(pyppeteer.chromium_downloader.chromiumExecutable.get('mac')))
    print('win64平台下载链接为：{}'.format(pyppeteer.chromium_downloader.downloadURLs.get('mac')))


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookie_login", default=False, action="store_true", required=False)
    parser.add_argument("--qrcode_login", default=False, action="store_true", required=False)
    parser.add_argument("-u", "--username", type=str, required=False)
    parser.add_argument("-p", "--password", type=str, required=False)
    return parser.parse_args()


def main():
    kwargs = vars(get_args())
    print(kwargs)
    spider = TaobaoSpider(**kwargs)
    try:
        asyncio.get_event_loop().run_until_complete(spider.start())
    except (NetworkError, CancelledError):
        print("安全退出!")
    # except Exception as e:
    #     print("异常退出：%s" % e)


if __name__ == '__main__':

    main()
