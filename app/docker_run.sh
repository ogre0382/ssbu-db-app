# Publishing your Docker image https://www.streamsync.cloud/deploy-with-docker.html#publishing-your-docker-image
# Docker Hubにプッシュしたイメージのコンテナを立ち上げてコマンド実行
docker run --rm -p 5000:5000 ${DOCKER_ACCOUNT_ID}/${DOCKER_IMAGE_NAME} > /dev/null 2> /tmp/local_update_error.log
if [ $? -eq 0 ]; then
    echo "Local update success"
else
    # エラーメッセージを表示する
    cat /tmp/local_update_error.log
    return 1
fi

# 一時ファイルを削除
rm -f /tmp/local_update_error.log