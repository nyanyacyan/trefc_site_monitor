# coding: utf-8
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 2024/9/23 更新

# sudo tree /Users/nyanyacyan/Desktop/Project_file/SNS_auto_upper -I 'venv|pyvenv.cfg|__pycache__'
# Mac mini PYTHONPATH=/Users/nyanyacyan/Desktop/Project_file/ImageAutomation/installer/src
# MacBook export PYTHONPATH="/Users/nyanyacyan/Desktop/Project_file/ImageAutomation/installer/src"


# 辞書データデバッグ
# import json
# json.dumps(data, indent=4, ensure_ascii=False)

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# import
import os, asyncio
from dotenv import load_dotenv

# 自作モジュール
from installer.src.method.base.utils.logger import Logger
from installer.src.method.base.selenium.chrome import ChromeManager
from installer.src.method.base.selenium.cookieManager import CookieManager
from base.loginWithCookie import CookieLogin
from base.insertSql import InsertSql
from installer.src.method.base.database.dataFormatterToSql import DataFormatterToSql
from const import SiteUrl
from constElementInfo import LoginElement

load_dotenv()

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# **********************************************************************************
# 一連の流れ


class Flow:
    def __init__(self):

        # logger
        self.getLogger = Logger()
        self.logger = self.getLogger.getLogger()

        # chrome
        self.chromeManager = ChromeManager()
        self.chrome = self.chromeManager.flowSetupChrome()

        self.loginUrl = SiteUrl.LoginUrl.value
        self.homeUrl = SiteUrl.HomeUrl.value
        self.targetUrl = SiteUrl.TargetUrl.value
        self.signInUrl = SiteUrl.SIGN_IN_URL.value

        # インスタンス
        self.cookieManager = CookieManager(
            chrome=self.chrome,
            loginUrl=self.loginUrl,
            homeUrl=self.homeUrl,
            ,
        )
        self.cookieLogin = CookieLogin(
            chrome=self.chrome,
            loginUrl=self.loginUrl,
            homeUrl=self.homeUrl,
            signInUrl=self.signInUrl,
            ,
        )
        self.insertSql = InsertSql(chrome=self.chrome, )
        self.createImage = DataFormatterToSql(chrome=self.chrome, )

    # ----------------------------------------------------------------------------------

    async def flow(self):
        # ログイン情報を呼び出し
        loginInfo = LoginElement.LOGIN_INFO.value
        loginInfo["idText"] = os.getenv("ID")
        loginInfo["passText"] = os.getenv("PASS")

        # DBチェッカーから
        cookies = self.cookieManager.startBoolFilePath(
            url=self.homeUrl, loginInfo=loginInfo
        )

        # cookiesの出力によってログイン方法を分ける
        self.cookieLogin.flowSwitchLogin(
            cookies=cookies, url=self.homeUrl, loginInfo=loginInfo
        )

        # text, imageを取得してSQLiteに入れ込む→入れ込んだIDのリストを返す
        listPageInfoDict = self.insertSql.getListPageInfo()
        allData = await self.insertSql.getDetailPageInfo(
            listPageInfoDict=listPageInfoDict
        )

        self.createImage.flowAllDataCreate(allDataDict=allData)


# TODO batFileの作成→実行、install

# TODO 手順書の作成


# ----------------------------------------------------------------------------------


if __name__ == "__main__":
    process = Flow()
    asyncio.run(process.flow())
