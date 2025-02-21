# coding: utf-8
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 2024/9/19 更新
# テストOK

# Pathの設定 export PYTHONPATH="${PYTHONPATH}:/Users/nyanyacyan/Desktop/project_file/SNS_auto_upper/installer/src/method/base"

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# import


# 自作モジュール
from installer.src.method.base.utils.context import GetContext

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# **********************************************************************************
# 単体テスト 写真を取得


class TestContext:

    # ----------------------------------------------------------------------------------
    # 成功したときのテスト
    # @patch('method')→この中にいれるmethodがモック化される→モック化されたものは引数に渡す必要がある

    def testContextSuccess(self):
        # ダミーデータセット

        # インスタンスの作成
        instance = GetContext()

        sheetNames = instance.getWeekday()

        # 結果の検証
        assert sheetNames == "木曜"


# ----------------------------------------------------------------------------------
