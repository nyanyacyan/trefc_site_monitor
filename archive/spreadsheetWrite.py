# coding: utf-8
# ----------------------------------------------------------------------------------
# 2023/5/8更新

# ? APIを使って書き込みする
# ----------------------------------------------------------------------------------
import gspread
import pandas as pd
from typing import Any, Dict
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials

from googleapiclient import errors
from gspread_dataframe import set_with_dataframe
from gspread.exceptions import APIError
from dotenv import load_dotenv


# 自作モジュール
from method.base.utils.logger import Logger
from method.base.selenium.errorHandlers import NetworkHandler
from method.base.utils.path import BaseToPath
from method.base.utils.popup import Popup

load_dotenv()

# ----------------------------------------------------------------------------------
####################################################################################
# **********************************************************************************


class GssWrite:
    def __init__(self):

        # logger
        self.getLogger = Logger()
        self.logger = self.getLogger.getLogger()

        # インスタンス
        self.networkError = NetworkHandler()
        self.path = BaseToPath()
        self.popup = Popup()

        self.timestamp = datetime.now()

    ####################################################################################
    #✅ データをWorksheetに書き込む

    def write_data_by_url(self, gss_info: Dict, cell: str, input_data: Any):
        client = self.client(jsonKeyName=gss_info["JSON_KEY_NAME"])
        selectWorkSheet = client.open_by_url(gss_info["SHEET_URL"]).worksheet(gss_info["WORKSHEET_NAME"])

        # ✅ 1次元リストなら2次元リストに変換
        if isinstance(input_data, list):
            if not any(isinstance(i, list) for i in input_data):  # ネストされていなければ
                input_data = [input_data]
        else:
            input_data = [[input_data]]  # 文字列や数値を2次元リストに変換


        writeData = selectWorkSheet.update(cell, input_data)
        self.logger.info(f"{input_data}を{cell}への書き込み完了")
        return writeData

    ####################################################################################
    # ----------------------------------------------------------------------------------
    # スプシの認証プロパティ

    def creds(self, jsonKeyName: str):
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        jsonKeyPath = self.path._get_secret_key_path(file_name=jsonKeyName)
        creds = Credentials.from_service_account_file(jsonKeyPath, scopes=SCOPES)
        return creds

    # ----------------------------------------------------------------------------------
    # スプシアクセスのプロパティ

    def client(self, jsonKeyName: str):
        creds = self.creds(jsonKeyName=jsonKeyName)
        client = gspread.authorize(creds)
        return client

    # ----------------------------------------------------------------------------------
    # 日付とエラー内容書き込み

    def _err_write_to_gss(self, gss_info: Dict, err_datetime_cell: str, err_cmt_cell: str, gss_check_err_comment: str):
            self.logger.error(f"エラー内容をスプレッドシートに書込開始\n{gss_check_err_comment}")
            # エラーのタイムスタンプの書込
            self.write_data_by_url(gss_info=gss_info, cell=err_datetime_cell, input_data=self.timestamp)

            # エラー内容を書込
            self.write_data_by_url(gss_info=gss_info, cell=err_cmt_cell, input_data=gss_check_err_comment)
            self.logger.warning('エラー内容書込完了')

            # POPUPを出す
            self.popup.popupCommentOnly(popupTitle=self.const_err_cmt_dict["POPUP_TITLE_SHEET_INPUT_ERR"], comment=gss_check_err_comment)

    # ----------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------
    # cellの値がない行を特定

    def _gss_none_cell_update(
        self, worksheet: str, col_left_num: int, start_row: int, input_values: int
    ):
        self.logger.info(f"********** _column_none_cell 開始 **********")

        try:
            self.logger.debug(
                f"self.spreadsheetId: {self.spreadsheetId}, start_row: {start_row}"
            )
            self.logger.debug(
                f"worksheet: {worksheet}, col_left_num: {col_left_num}, start_row: {start_row}"
            )

            # スプシへのアクセスを定義（API）
            # * Scopeはこの場所で特定が必要
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            c = ServiceAccountCredentials.from_json_keyfile_name(
                self.jsonKeyName, scope
            )
            gs = gspread.authorize(c)

            # 指定のスプシへアクセス
            select_sheet = gs.open_by_key(self.spreadsheetId).worksheet(worksheet)

            self.logger.debug(f"select_sheet: {select_sheet}")

            # 指定したcolumnの値を入手
            col_row = select_sheet.col_values(col_left_num)

            # Noneのcellを見つけたIndexを見つけてそのIndexを取得
            for i, cell in enumerate(col_row, start=start_row):
                if cell == "":
                    none_cell_row = i

            # もしなにもなかったらスタートする行の次の行がスタート
            else:
                none_cell_row = len(col_row) + start_row

            self.logger.debug(f"none_cell_row: {none_cell_row}")

            # Aが１になるように変更
            column = chr(64 + col_left_num)

            # 正しく変換したものを文字列に変換->「A21」みたいにする
            cell_range = f"{column}{none_cell_row}"

            # スプシに入力できる値に変換  スプシに値を入力する際にはリスト型
            input_list = [[value] for value in input_values]

            self.logger.debug(f"cell_range: {cell_range}")
            self.logger.debug(f"input_list: {input_list}")

            # スプシ更新
            select_sheet.update(cell_range, input_list)

            self.logger.info(f"********** _column_none_cell 終了 **********")

        except errors.HttpError as e:
            self.logger.error(f"スプシ: 認証失敗{e}")
            raise

        except gspread.exceptions.APIError as e:
            self.logger.error(f"スプシ: サーバーエラーのため実施不可{e}")
            raise

        except Exception as e:
            self.logger.error(f"スプシ: 処理中にエラーが発生{e}")
            raise

    # ----------------------------------------------------------------------------------
    # cellの値がない場所を指定

    def update_timestamps(self, worksheet: str):
        self.logger.info(f"********** update_timestamps 開始 **********")

        try:
            self.logger.debug(f"worksheet: {worksheet}")

            # スプシへのアクセスを定義（API）
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            c = ServiceAccountCredentials.from_json_keyfile_name(
                self.jsonKeyName, scope
            )
            gs = gspread.authorize(c)

            select_sheet = gs.open_by_key(self.spreadsheetId).worksheet(worksheet)

            self.logger.debug(f"select_sheet: {select_sheet}")

            get_a_values = select_sheet.col_values(1)
            get_b_values = select_sheet.col_values(2)

            # filtered_a_values = get_a_values[2:]
            # filtered_b_values = get_b_values[2:]

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for index, b_val in enumerate(get_b_values[2:], start=3):
                try:
                    a_val = (
                        get_a_values[index - 1] if index - 1 < len(get_a_values) else ""
                    )

                except IndexError:
                    a_val = ""

                if b_val and not a_val:

                    date_cell = f"A{index}"
                    select_sheet.update(date_cell, [[current_date]])
                    self.logger.debug(f"a_val: {a_val}, b_val: {b_val}")

            self.logger.info(f"********** update_timestamps 終了 **********")

        except APIError as e:
            if e.response.status_code == 429:
                self.logger.error(f"APIの利用限界: しばらく立ってから再試行が必要 {e}")
            else:
                self.logger.error(f"APIエラーが発生 {e}")

        except errors.HttpError as error:
            self.logger.error(f"スプシ: 認証失敗: {error}")
            raise

        except gs.exceptions.APIError as e:
            self.logger.error(f"スプシ: サーバーエラーのため実施不可{e}")
            raise

        except Exception as e:
            self.logger.error(f"スプシ: 処理中にエラーが発生: {e}")
            raise

    # ----------------------------------------------------------------------------------
    # noneのcellを見つけて、そのcellの次の行から書き込む

    def _gss_none_cell_next_row_df_write(
        self, worksheet: str, col_left_num: int, start_row: int, df: pd.DataFrame
    ):
        self.logger.info(f"********** _gss_none_cell_next_row_df_write 開始 **********")

        try:
            self.logger.debug(
                f"self.spreadsheetId: {self.spreadsheetId}, start_row: {start_row}"
            )

            self.logger.debug(
                f"worksheet: {worksheet}, col_left_num: {col_left_num}, start_row: {start_row}"
            )

            # スプシへのアクセスを定義（API）
            # * Scopeはこの場所で特定が必要
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            c = ServiceAccountCredentials.from_json_keyfile_name(
                self.jsonKeyName, scope
            )
            gs = gspread.authorize(c)

            # 指定のスプシへアクセス
            select_sheet = gs.open_by_key(self.spreadsheetId).worksheet(worksheet)

            self.logger.debug(f"select_sheet: {select_sheet}")

            self.logger.info(df.head())
            self.logger.info(df.index)

            # 特定のcolumnの値を入手
            col_val = select_sheet.col_values(col_left_num)

            self.logger.warning(f"col_val: {col_val}")

            # noneのcellの次の行から書き込む
            # Noneのcellを見つけたIndexを見つけてそのIndexを取得
            for i, cell in enumerate(col_val, start=start_row):
                if cell == "":
                    none_cell_row = i
                    none_cell_next = none_cell_row + 1
            # もしなにもなかったらスタートする行の次の行がスタート
            else:
                none_cell_row = len(col_val) + start_row
                none_cell_next = none_cell_row + 1

            self.logger.debug(f"none_cell_next: {none_cell_next}")

            # cellにDataFrameを書き込む
            set_with_dataframe(select_sheet, df, row=none_cell_next, col=col_left_num)

            self.logger.info(
                f"********** _gss_none_cell_next_row_df_write 終了 **********"
            )

        except errors.HttpError as e:
            self.logger.error(f"スプシ: 認証失敗{e}")
            raise

        except gspread.exceptions.APIError as e:
            self.logger.error(f"スプシ: サーバーエラーのため実施不可{e}")
            raise

        except Exception as e:
            self.logger.error(f"スプシ: 処理中にエラーが発生{e}")
            raise

    # ----------------------------------------------------------------------------------
    # noneのcellを見つけて、そのcellの次の行から書き込む

    def _gss_none_cell_next_row_df_write_at_grid(
        self, worksheet_name: str, col_left_num: int, start_row: int, df: pd.DataFrame
    ):
        self.logger.info(
            f"********** _gss_none_cell_next_row_df_write_at_grid 開始 **********"
        )

        try:
            self.logger.debug(
                f"self.spreadsheetId: {self.spreadsheetId}, start_row: {start_row}"
            )

            self.logger.debug(
                f"worksheet_name: {worksheet_name}, col_left_num: {col_left_num}, start_row: {start_row}"
            )

            # スプシへのアクセスを定義（API）
            # * Scopeはこの場所で特定が必要
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            c = ServiceAccountCredentials.from_json_keyfile_name(
                self.jsonKeyName, scope
            )
            gs = gspread.authorize(c)

            # 指定のスプシへアクセス
            select_sheet = gs.open_by_key(self.spreadsheetId).worksheet(worksheet_name)

            self.logger.debug(f"select_sheet: {select_sheet}")

            self.logger.info(df.head())
            self.logger.info(df.index)

            # 特定のcolumnの値を入手
            col_val = select_sheet.col_values(col_left_num)

            self.logger.warning(f"col_val: {col_val}")

            # noneのcellの次の行から書き込む
            # Noneのcellを見つけたIndexを見つけてそのIndexを取得
            for i, cell in enumerate(col_val, start=start_row):
                if cell == "":
                    none_cell_row = i
                    none_cell_next = none_cell_row + 1
            # もしなにもなかったらスタートする行の次の行がスタート
            else:
                none_cell_row = len(col_val) + start_row
                none_cell_next = none_cell_row + 1

            self.logger.debug(f"none_cell_next: {none_cell_next}")

            # cellにDataFrameを書き込む
            set_with_dataframe(select_sheet, df, row=none_cell_next, col=col_left_num)

            # gridを追加
            self._grid_input(
                df=df,
                worksheet=select_sheet,
                start_row=none_cell_next,
                start_col=col_left_num,
                spreadsheet=gs.open_by_key(self.spreadsheetId),
            )

            self.logger.info(
                f"********** _gss_none_cell_next_row_df_write_at_grid 終了 **********"
            )

        except errors.HttpError as e:
            self.logger.error(f"スプシ: 認証失敗{e}")
            raise

        except gspread.exceptions.APIError as e:
            self.logger.error(f"スプシ: サーバーエラーのため実施不可{e}")
            raise

        except Exception as e:
            self.logger.error(f"スプシ: 処理中にエラーが発生{e}")
            raise

    # ----------------------------------------------------------------------------------
    # グリッドを入れる

    def _grid_input(
        self,
        df: pd.DataFrame,
        worksheet: str,
        start_row: int,
        start_col: int,
        spreadsheet: str,
    ):
        try:
            self.logger.info(f"********** _grid_input 開始 **********")

            if not df.empty:
                # DataFrameの縦と横の長さを取得
                num_rows, num_cols = df.shape
                self.logger.debug(f"num_rows: {num_rows}")
                self.logger.debug(f"num_cols: {num_cols}")

                requests = {
                    "updateBorders": {
                        "range": {
                            "sheetId": worksheet._properties["sheetId"],
                            "startRowIndex": start_row - 1,
                            "endRowIndex": start_row - 1 + num_rows + 1,
                            "startColumnIndex": start_col - 1,
                            "endColumnIndex": start_col - 1 + num_cols,
                        },
                        "top": {
                            "style": "SOLID",
                            "width": 1,
                            "color": {
                                "red": 0,
                                "green": 0,
                                "blue": 0,
                            },
                        },
                        "bottom": {
                            "style": "SOLID",
                            "width": 1,
                            "color": {
                                "red": 0,
                                "green": 0,
                                "blue": 0,
                            },
                        },
                        "left": {
                            "style": "SOLID",
                            "width": 1,
                            "color": {
                                "red": 0,
                                "green": 0,
                                "blue": 0,
                            },
                        },
                        "right": {
                            "style": "SOLID",
                            "width": 1,
                            "color": {
                                "red": 0,
                                "green": 0,
                                "blue": 0,
                            },
                            # 空の横の部分に線を引く
                        },
                        "innerHorizontal": {
                            "style": "SOLID",
                            "width": 1,
                            "color": {
                                "red": 0,
                                "green": 0,
                                "blue": 0,
                            },
                            # 空の縦の部分に線を引く
                        },
                        "innerVertical": {
                            "style": "SOLID",
                            "width": 1,
                            "color": {
                                "red": 0,
                                "green": 0,
                                "blue": 0,
                            },
                        },
                    }
                }

            else:
                self.logger.debug(f"DataFrameが空になってしまってる")

            spreadsheet.batch_update({"requests": [requests]})

            self.logger.info(f"********** _grid_input 終了 **********")

        except Exception as e:
            self.logger.error(f"_grid_input: 処理中にエラーが発生: {e}")
            raise


# **********************************************************************************
