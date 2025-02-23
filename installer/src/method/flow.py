# coding: utf-8
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# export PYTHONPATH="/Users/nyanyacyan/Desktop/project_file/trefc_site_monitor/installer/src"

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# import
import os
import concurrent.futures
from typing import Dict
from datetime import datetime
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, NoSuchElementException, TimeoutException, WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 自作モジュール
from method.base.utils.logger import Logger
from method.base.selenium.chrome import ChromeManager
from method.base.selenium.seleniumBase import SeleniumBasicOperations
from method.base.spreadsheet.spreadsheetRead import GetDataGSSAPI
from method.base.selenium.get_element import GetElement
from method.base.decorators.decorators import Decorators
from method.base.spreadsheet.spreadsheetWrite import GssWrite
from method.base.selenium.click_element import ClickElement
from method.base.selenium.driverWait import Wait
from method.base.utils.fileWrite import FileWrite
from method.base.utils.path import BaseToPath

# flow


# const
from method.const_element import GssInfo, ElementInfo
from method.const_str import SeleniumWait

deco = Decorators()

# ----------------------------------------------------------------------------------
# **********************************************************************************
# **********************************************************************************
# 一連の流れ

class Flow:
    def __init__(self):
        # logger
        self.getLogger = Logger()
        self.logger = self.getLogger.getLogger()

        # timestamp
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # インスタンス
        self.gss_read = GetDataGSSAPI()
        self.gss_write = GssWrite()


        # 各Flow
        self.single_flow = SingleProcessFlow()

        # const
        self.const_gss_info = GssInfo.trefc.value
        self.const_element_info = ElementInfo.trefc.value
        self.const_by = SeleniumWait.BY.value


# **********************************************************************************
    # ----------------------------------------------------------------------------------

    def flow(self):

        # スプシにアクセス（Worksheet指定）
        df = self.gss_read._get_df_gss_url(gss_info=self.const_gss_info)
        df_filtered = df[df[self.const_gss_info['CHECK']] == "TRUE"]

        self.logger.debug(f'DataFrame: {df_filtered.head()}')

        for i, row in df_filtered.iterrows():
            row_num = i + 1
            get_gss_row_dict = row.to_dict()

            self.single_flow.single_process(gss_info=get_gss_row_dict)


    # ----------------------------------------------------------------------------------

# 一連の流れ

class SingleProcessFlow:
    def __init__(self):
        # logger
        self.getLogger = Logger()
        self.logger = self.getLogger.getLogger()

        # timestamp
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # インスタンス
        self.gss_read = GetDataGSSAPI()
        self.gss_write = GssWrite()
        self.path = BaseToPath()

        # 各Flow

        # const
        self.const_gss_info = GssInfo.trefc.value
        self.const_element_info = ElementInfo.trefc.value
        self.const_by = SeleniumWait.BY.value

# **********************************************************************************
    # ----------------------------------------------------------------------------------


    def single_process(self, gss_info: Dict):
        try:
            # chrome
            self.chromeManager = ChromeManager()
            self.chrome = self.chromeManager.flowSetupChrome()

            # インスタンス
            self.click_element = ClickElement(chrome=self.chrome)
            self.get_element = GetElement(chrome=self.chrome)
            self.element_wait = Wait(chrome=self.chrome)
            self.random_sleep = SeleniumBasicOperations(chrome=self.chrome)
            self.selenium = SeleniumBasicOperations(chrome=self.chrome)

            self.logger.debug(f"ID: {gss_info['ID']}\nブランド名: {gss_info['brand_name']}\nurl: {gss_info['url']}")

            # サイトを開く
            self.chrome.get(gss_info['url'])

            # display,noneの解除
            self.get_element.unlockDisplayNone()

            self.element_wait.jsPageChecker(self.chrome, timeout=20)

            # サイトが開いているかを確認
            searchWord = self.get_element.getElement(by='id', value='searchWord')
            self.logger.debug(f'searchWord: {searchWord}')

            if not searchWord:
                raise ValueError("サイトがみつかりません")


            # テーブルの取得
            ul_element = self.get_element.getElement(by='css', value=self.const_element_info['UL_ELEMENT_VALUE'])
            self.logger.info(f'ul_elements: {ul_element}')
            self.element_wait.jsPageChecker(self.chrome, timeout=20)

            # １つ１つのアイテムを取得
            li_elements = ul_element.find_elements(self.const_by['CSS'], self.const_element_info['LI_ELEMENT_VALUE'])
            self.logger.info(f"liの数: {len(li_elements)}")
            self.element_wait.jsPageChecker(self.chrome, timeout=20)

            # NEWがついているものに絞り込む
            new_icon = [li for li in li_elements if li.find_elements(self.const_by['CSS'], self.const_element_info['NEW_ITEM_ELEMENT_VALUE'])]

            item_data_list = []
            if new_icon:

                # item_infoを取得
                for li in new_icon:
                    item = {
                        "id" : gss_info['id'],  # ブランド名の取得
                        "brand_name" : li.find_element(self.const_by['CSS'], self.const_element_info['BRAND_NAME_ELEMENT_VALUE']).text,  # サイズの取得
                        "size" : li.find_element(self.const_by['CSS'], self.const_element_info['BRAND_SIZE_ELEMENT_VALUE']).text,  # サイズの取得
                        "price" : li.find_element(self.const_by['CSS'], self.const_element_info['BRAND_PRICE_ELEMENT_VALUE']),  # 価格取得
                        "link" : li.find_element(self.const_by['TAG'], "a").text,  # リンク
                    }
                    item_data_list.append(item)
                    self.logger.info(f"{gss_info['id']} をリストに追加")
            else:
                self.logger.warning(f'{self.__class__.__name__}new_iconがありません: {new_icon}')

            self.logger.critical(f'{self.__class__.__name__} item_data_list: {item_data_list}')

            # 過去のpickleからデータを取得
            pickle_path = self._pickle_path(file_name=gss_info['ID'])
            

            # 突合する

            # 差分のリストを作成（新商品の入荷）

            # pickleに保存する

            # メッセージ用に変換する

            # Discordにて送る




        except TimeoutError:
            timeout_comment = "ログインでreCAPTCHA処理にが長引いてしまったためエラー"

        except Exception as e:
            self.logger.error(f'{self.__class__.__name__} エラー: {e}')

        finally:

            # ✅ Chrome を終了
            self.chrome.quit()


    # ----------------------------------------------------------------------------------

    def _delete_file(self, file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)
            self.logger.info(f'指定のファイルの削除を実施: {file_path}')

        else:
            self.logger.error(f'{self.__class__.__name__} ファイルが存在しません: {file_path}')

    # ----------------------------------------------------------------------------------
    # picklePath(ファイルがなかったら空のファイルを作成)

    def _pickle_path(self, file_name: str):
        return self.path._get_pickle_path(file_name=file_name)

    # ----------------------------------------------------------------------------------


    # ----------------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# テスト実施

if __name__ == "__main__":

    test_flow = Flow()
    # 引数入力
    test_flow.flow()
