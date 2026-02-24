FROM python:3.12-slim

WORKDIR /app

# システム依存パッケージ
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

# 依存パッケージインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY src/ src/
COPY config/ config/
COPY templates/ templates/
COPY scripts/ scripts/
COPY calendar/ calendar/

# データ・ログディレクトリを作成
RUN mkdir -p data logs

# 非rootユーザーで実行
RUN useradd -r -s /bin/false botuser && \
    chown -R botuser:botuser /app
USER botuser

# tiniをPID1として使用（シグナル処理の改善）
ENTRYPOINT ["tini", "--"]

# デフォルト: 常駐スケジューラー起動
CMD ["python", "scripts/run_all.py"]
