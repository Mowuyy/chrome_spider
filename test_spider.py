# -*- coding: utf-8 -*-

import asyncio
from spider_core.basic import BaseSpider


class TestSpider(BaseSpider):

    async def _handler(self):
        # 首页
        await self._page.goto("https://www.taobao.com")
        # await self._page.waitForSelector("button.button.is-medium")
        # element = await self._page
        # await self._page.waitForSelector("#pos-backend")  # 等待标题出现

        # await asyncio.sleep(self.short_random)
        # 搜索
        # await self._input_search("input#kw", "pycharm")
        # await asyncio.sleep(self.short_random)
        # 移动鼠标点击
        # element_handler = await self._page.querySelector("input.input.is-medium")
        await self._scroll()
        await asyncio.sleep(self.short_random)
        await self._scroll(bottom=False)
        # box = element_handler.boundingBox()
        # print(dir(box))
        # await self._page.hover("#1")
        # await self._page.mouse.click(300., 300., {"delay": 1000})
        # await self._page.mouse.down()
        # await self._page.mouse.move(100, 100)
        # await self._page.mouse.up()
        # await self._page.mouse.move(1680, 530)
        # await self._page.mouse.down()
        # await self._page.mouse.move(100, 100)
        # await self._page.mouse.up()
        await asyncio.sleep(self.long_random)


if __name__ == '__main__':

    spider = TestSpider()
    asyncio.get_event_loop().run_until_complete(spider.start())

