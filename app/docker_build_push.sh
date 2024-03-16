#!/bin/bash -e

# シェルスクリプト内のエラーで実行を停止する「-e」と、実行コマンドを出力する「-x」オプションを使ったシェルスクリプトの開発 https://www.konosumi.net/entry/2020/01/01/154355
# （小ネタ）docker-compose.yml をビルドに使う https://qiita.com/knjname/items/5ca14c36fce82776c1c0

# ./.envファイルを読み込んで変数として参照できるようにする
source ./.env

# Imageをbuild
docker-compose build
if [ $? -ne 0 ]; then
    echo "Failed to build the Docker image."
    return 1
else
    echo "Docker build success"
fi

# Docker Hubにログイン
docker login
if [ $? -ne 0 ]; then
    echo "Failed to login to Docker Hub."
    return 1
else
    echo "Docker Hub login success"
fi

# DockerイメージをDocker Hubにプッシュ
docker-compose push
if [ $? -ne 0 ]; then
    echo "Failed to push the Docker image to Docker Hub."
    return 1
else
    echo "Docker push success"
fi