import subprocess

# Getting started https://www.streamsync.cloud/getting-started.html
cmd = "streamsync edit app"
#cmd = "streamsync edit app --port 10000"

# 【Python入門】subprocessを使ってコマンドを実行しよう！ https://www.sejuku.net/blog/51090
subprocess.call(cmd.split())