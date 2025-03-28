#!/bin/bash

# ログファイルの設定
LOG_FILE="/var/log/my_script.log"
exec > >(tee -a $LOG_FILE) 2>&1

echo "$(date) - Starting script"

# ユーザーの確認
whoami

# 仮想環境のアクティブ化
source /home/ec2-user/venv/bin/activate

# ディレクトリが存在するか確認
if [ ! -d "/home/ec2-user/trefc_site_monitor/installer/src" ]; then
    echo "$(date) - ERROR: ディレクトリが見つかりません！"
    exit 1
fi

# `ec2-user` で `main.py` を実行
cd /home/ec2-user/trefc_site_monitor/installer/src || { echo "$(date) - Failed to change directory"; exit 1; }
python main.py &
MAIN_PID=$!
echo "$(date) - MAIN_PID: $MAIN_PID"

if ! ps -p $MAIN_PID > /dev/null; then
    echo "$(date) - ERROR: プロセスが見つかりません！"
    exit 1
fi
echo "$(date) - プロセスが正常に開始されました。PID: $MAIN_PID"

# 30分待機
START_TIME=$(date +%s)
while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

    echo "$(date) - 経過時間: $ELAPSED_TIME 秒"

    if [ $ELAPSED_TIME -ge 1800 ]; then
        echo "$(date) - 30分が経過。インスタンスを停止します..."
        timeout 60 aws ec2 stop-instances --instance-ids i-070bbbe489226569a 2>&1
        if [ $? -eq 0 ]; then
            echo "$(date) - インスタンスの停止に成功しました。"
        else
            echo "$(date) - インスタンスの停止に失敗しました！" >&2
        fi
        break
    fi

    if ! kill -0 $MAIN_PID 2>/dev/null; then
        echo "$(date) - メインスクリプトが終了。インスタンスを停止します..."
        timeout 60 aws ec2 stop-instances --instance-ids i-070bbbe489226569a 2>&1
        if [ $? -eq 0 ]; then
            echo "$(date) - インスタンスの停止に成功しました。"
        else
            echo "$(date) - インスタンスの停止に失敗しました！" >&2
        fi
        break
    fi

    sleep 10
done

echo "$(date) - スクリプトが終了しました。"
