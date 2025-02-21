# coding: utf-8
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# export PYTHONPATH="/Users/nyanyacyan/Desktop/project_file/domain_search/installer/src"


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# import
import os, time, asyncio
from selenium_stealth import stealth

# 自作モジュール
from installer.src.method.base.utils.logger import Logger
from installer.src.method.base.selenium.chrome import ChromeManager
from installer.src.method.base.selenium.login_db_cookie import SingleLoginDBCookie
from installer.src.method.base.utils.fileRead import ResultFileRead


from const_str import SiteName, GameClubInfo

# ----------------------------------------------------------------------------------
# **********************************************************************************
# 一連の流れ


class FlowLoginCookie:
    def __init__(self, home_url: str, db_file_name: str):

        # logger
        self.getLogger = Logger()
        self.logger = self.getLogger.getLogger()

        # chrome
        self.chromeManager = ChromeManager()
        self.chrome = self.chromeManager.flowSetupChrome()

        # navigator.webdriver を undefined に設定
        self.chrome.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
            },
        )

        # const
        self.home_url = home_url
        self.db_file_name = db_file_name

        # インスタンス
        self.cookie_login = SingleLoginDBCookie(
            chrome=self.chrome,
            db_file_name=self.db_file_name,
        )
        self.pickle_read = ResultFileRead()

    ####################################################################################
    # ----------------------------------------------------------------------------------
    # todo 各メソッドをまとめる

    async def process(self):
        cookies = self.pickle_read.readPickleLatestResult()

        self.cookie_login._session_login(home_url=self.home_url, cookies=cookies)


# ----------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# テスト実施

if __name__ == "__main__":
    home_url = GameClubInfo.HOME_URL.value
    db_file_name = SiteName.LGRAM.value
    test_flow = FlowLoginCookie(home_url=home_url, db_file_name=db_file_name)
    asyncio.run(test_flow.process())
