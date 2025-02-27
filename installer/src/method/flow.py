# coding: utf-8
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# export PYTHONPATH="/Users/nyanyacyan/Desktop/Project_file/trefc_site_monitor/installer/src"

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# import
import os
from typing import Dict
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from pathlib import Path


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
from method.base.utils.fileRead import InputDataFileRead
from method.base.utils.fileWrite import FileWrite
from method.base.utils.path import BaseToPath
from method.base.notify.notify import DiscordNotify

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

    def process(self):

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
        self.file_read = InputDataFileRead()
        self.file_write = FileWrite()
        self.discord = DiscordNotify()

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
            # self.get_element.unlockDisplayNone()

            self.element_wait.jsPageChecker(self.chrome, timeout=20)

            # サイトが開いているかを確認
            searchWord = self.get_element.getElement(by='id', value='searchWord')
            self.logger.debug(f'サイトは開けてます: {searchWord}')

            if not searchWord:
                raise ValueError("サイトがみつかりません")

            by_css = self.const_by['CSS']
            self.logger.debug(f'by_css: {by_css}')

            # テーブルの取得
            ul_element = self.get_element.getElement(by='css', value=self.const_element_info['UL_ELEMENT_VALUE'])
            self.logger.info(f'ul_elements: {ul_element}')
            self.element_wait.jsPageChecker(self.chrome, timeout=20)

            # １つ１つのアイテムを取得
            li_xpath = self.const_element_info['LI_ELEMENT_VALUE']
            self.logger.debug(f'li_xpath: {li_xpath}')
            self.get_element.filterElements(parentElement=ul_element, by='css', value=li_xpath)
            li_elements = ul_element.find_elements(By.CSS_SELECTOR, ".p-itemlist_item")
            self.logger.info(f"liの数: {len(li_elements)}")
            self.element_wait.jsPageChecker(self.chrome, timeout=20)

            try:
                new_icon_element_list = []
                for li in li_elements:
                    # iconの入っている用をにフィルタリング
                    icon_box_element = self.get_element.filterElement(parentElement=li, by='css', value=self.const_element_info['NEW_ITEM_ELEMENT_VALUE'])
                    # icon_boxに入っているtextが"NEW"になっているものだけに厳選
                    icon_text= icon_box_element.text
                    if "NEW" == icon_text:
                        # 対象のWebElementのみ追加
                        new_icon_element_list.append(li)

                self.logger.info(f'[NEW]のアイコン商品: {len(new_icon_element_list)} つあります。')
            except NoSuchElementException:
                self.logger.warning(f"{gss_info['ID']} new_iconがありません(新商品なし)")
                return

            # NEWが入っているものの詳細を取得
            new_item_data_list = []
            if new_icon_element_list:

                # item_infoを取得
                for new_icon_element in new_icon_element_list:

                    # 各要素の取得
                    brand_name_element = self.get_element.filterElement(parentElement=new_icon_element, by='css', value=self.const_element_info['BRAND_NAME_ELEMENT_VALUE'])
                    size_element = self.get_element.filterElement(parentElement=new_icon_element, by='css', value=self.const_element_info['BRAND_SIZE_ELEMENT_VALUE'])
                    link_element = self.get_element.filterElement(parentElement=new_icon_element, by='tag', value='a')

                    try:
                        price_element = self.get_element.filterElement(parentElement=new_icon_element, by='css', value=self.const_element_info['BRAND_PRICE_ELEMENT_VALUE'])

                    except NoSuchElementException:
                        self.logger.warning(f'{self.__class__.__name__} SALE対象品の価格')
                        price_element = self.get_element.filterElement(parentElement=new_icon_element, by='css', value=self.const_element_info['BRAND_SALE_PRICE_ELEMENT_VALUE'])


                    # 各要素から必要情報を取得
                    item = {
                        "id" : gss_info['ID'],  # ブランド名の取得
                        "brand_name" : brand_name_element.text,  # サイズの取得
                        "size" : size_element.text,  # サイズの取得
                        "price" : price_element.text,  # 価格取得
                        "link" : link_element.get_attribute("href"),  # リンク
                    }
                    # 取得した情報をリストに格納
                    new_item_data_list.append(item)
                    self.logger.info(f"{gss_info['ID']} をリストに追加\n{item}")

            self.logger.critical(f'{self.__class__.__name__} new_item_data_list: {new_item_data_list}')

            # 過去のpickleからデータを取得
            pickle_file_path = self._pickle_path(file_name=gss_info['ID'])
            old_list = self.file_read.read_pickle_input(pickle_file_path=pickle_file_path)

            # 突合する
            if set(map(str, new_item_data_list)) == set(map(str, old_list)):
                self.logger.warning(f"{gss_info['ID']} - {gss_info['brand_name']} 新商品入荷はありません")
                return

            else:
                self.logger.critical(f"{gss_info['ID']} - {gss_info['brand_name']} 新商品入荷してます。")

                # 差分があった場合
                diff_list = [item for item in new_item_data_list if not any(item == old_item for old_item in old_list)]
                self.logger.info(f'新しい商品情報リスト: {diff_list}')

                # pickleに保存する
                self.file_write.write_pickle_input(data=new_item_data_list, pickle_file_path=Path(pickle_file_path))

                # メッセージ用に変換する
                item_msg_list = []
                for i, diff_data in enumerate(diff_list):
                    msg = f"{i + 1}, {diff_data['brand_name']}\n{diff_data['size']}\n{diff_data['price']}\n{diff_data['link']}\n"
                    item_msg_list.append(msg)

                # すべてのmsgを結合
                main_msg = "\n\n".join(item_msg_list)

                # Discordにて送る
                opening_msg = f"■ 新しい商品が入荷しました ■ \n\n-------- {gss_info['ID']} - {gss_info['brand_name']} --------\n\n"
                all_msg = f"{opening_msg}{main_msg}"
                self.logger.info(f'送信msg: {all_msg}')

                self.discord.discord_notify(message=all_msg)


        except TimeoutError:
            timeout_comment = "ログインでreCAPTCHA処理にが長引いてしまったためエラー"

        except Exception as e:
            self.logger.error(f'{self.__class__.__name__} エラー: {e}')

        finally:
            self.logger.info(f" {gss_info['ID']} 処理完了")
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
    test_flow.process()
