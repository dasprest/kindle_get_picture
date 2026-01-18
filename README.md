# Kindle Web Reader Image Downloader

Kindle Web Reader にサインインし、ページをめくりながら HTML を保存し、読み込み中に取得できた画像をすべてダウンロードするためのスクリプトです。

> **注意**
> - ご自身が閲覧権限を持つコンテンツのみを対象にしてください。
> - 本スクリプトは Kindle Web Reader の挙動に依存するため、UI の変更などで動かなくなる場合があります。

## 事前準備（誰でも使うために必要なもの）

- **Python 3.9+**
- **Google Chrome / Chromium** 相当のブラウザ実行環境（Playwright が自動で入れます）
- **Kindle の閲覧権限**（購入済み/レンタル済み）

## 使い方

1. 依存関係をインストールします。

```bash
pip install -r requirements.txt
python -m playwright install
```

2. スクリプトを実行します。

```bash
python kindle_image_downloader.py \
  --url "https://read.amazon.co.jp/?asin=B0BJ6PQHCH" \
  --output-dir output
```

3. ブラウザが起動したら、Kindle にサインインし、対象の本を開いて最初のページを表示します。
4. ターミナルで Enter を押すとキャプチャが開始され、ページをめくりながら HTML と画像を保存します。

## 出力内容

- `output/html/` : 各ページごとの HTML（フレームごとに保存されます）
- `output/images/` : 取得できた画像ファイル
- `output/browser_profile/` : ブラウザのログイン状態を保存（次回以降のサインインを省略できます）

## オプション

- `--headless` : ヘッドレスモードで起動（ログインが難しいため通常は非推奨）
- `--max-pages` : 最大ページ数（デフォルト 300）
- `--delay` : ページ送り後の待機秒数（デフォルト 1.0）
- `--stop-unchanged` : HTML 変化がない状態が続いたら停止する回数（デフォルト 3）
