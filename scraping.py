import pandas as pd
from selenium import webdriver
import matplotlib.pyplot as plt
import time

# 検索ワード
search_words = "リンガメタリカ"
# スクレイピング結果から除くワード(なければ空("")にする)
except_words = "CD"
# 表示する最高値
max_price = 1500
# bin幅(何円ごとのグラフ幅にするか、ここでは50円毎とした)
bins = 50


def search_mercari(search_words):
    words = search_words.split(" ")
    search_words = words[0]
    for i in range(1, len(words)):
        search_words = search_words + "+" + words[i]

    # メルカリで検索するためのURL
    url = "https://www.mercari.com/jp/search/?keyword=" + search_words

    # ブラウザを開く
    browser = webdriver.Chrome()

    # 起動時に時間がかかるため、5秒スリープ
    time.sleep(5)

    page = 1
    # リストを作成
    columns = ["Name", "Price", "Sold", "Url"]
    # 配列名を指定する
    df = pd.DataFrame(columns=columns)

    # 実行
    try:
        while(True):
            # ブラウザで検索
            browser.get(url)
            # 商品ごとのHTMLを取得
            posts = browser.find_elements_by_css_selector(".items-box")
            # 何ページ目を取得しているか表示
            print(str(page) + "ページ取得中")

            # 商品ごとに名前と値段、購入済みかどうか、URLを取得
            for post in posts:
                # 商品名
                title = post.find_element_by_css_selector(
                    "h3.items-box-name").text

                # 値段を取得
                price = post.find_element_by_css_selector(
                    ".items-box-price").text
                # 余計なものが取得されてしまうので削除
                price = price.replace("¥", "")
                price = price.replace(",", "")

                # 購入済みであれば1、未購入であれば0になるように設定
                sold = 0
                if (len(post.find_elements_by_css_selector(".item-sold-out-badge")) > 0):
                    sold = 1

                # URLを取得
                Url = post.find_element_by_css_selector(
                    "a").get_attribute("href")
                se = pd.Series([title, price, sold, Url], columns)
                df = df.append(se, columns)

            page += 1
            # 次のページに進むためのURLを取得
            url = browser.find_element_by_css_selector(
                "li.pager-next .pager-cell a").get_attribute("href")
            print("Moving to next page ...")
    except:
        print("Next page is nothing.")

    # 最後に得たデータをCSVにして保存
    filename = "mercari_scraping_" + search_words + ".csv"
    df.to_csv(filename, encoding="utf-8-sig")
    print("Finish!")


def make_graph(search_words, except_words, max_price, bins):
    # CSV ファイルを開く
    df = pd.read_csv("mercari_scraping_" + search_words + ".csv")

    # "Name"に"except_words"が入っているものを除く
    if(len(except_words) != 0):
        df = df[df["Name"].str.contains(except_words) == False]

    # 購入済み(1)の商品だけを表示
    dfSold = df[df["Sold"] == 1]

    # 価格(Price)が1500円以下の商品のみを表示
    dfSold = dfSold[dfSold["Price"] < max_price]

    # カラム名を指定「値段」「その値段での個数」「パーセント」の3つ
    columns = ["Price",  "Num", "Percent"]

    # 配列名を指定する
    all_num = len(dfSold)
    num = 0
    dfPercent = pd.DataFrame(columns=columns)

    for i in range(int(max_price/bins)):

        MIN = i * bins - 1
        MAX = (i + 1) * bins

        # MINとMAXの値の間にあるものだけをリストにして、len()を用いて個数を取得
        df0 = dfSold[dfSold["Price"] > MIN]
        df0 = df0[df0["Price"] < MAX]
        sold = len(df0)

        # 累積にしたいので、numに今回の個数を足していく
        num += sold

        # ここでパーセントを計算する
        percent = num / all_num * 100

        # 値段はMINとMAXの中央値とした
        price = (MIN + MAX + 1) / 2
        se = pd.Series([price, num, percent], columns)
        dfPercent = dfPercent.append(se, columns)

    # CSVに保存
    filename = "mercari_histgram_" + search_words + ".csv"
    dfPercent.to_csv(filename, encoding="utf-8-sig")

    # グラフの描画
    ax1 = dfSold.plot(kind="hist", y="Price", bins=25,
                      secondary_y=True, alpha=0.9)
    dfPercent.plot(kind="area", x="Price", y=[
        "Percent"], alpha=0.5, ax=ax1, figsize=(20, 10), color="k")
    plt.savefig("mercari_histgram_" + search_words + ".jpg")


# 1. スクレイピング
search_mercari(search_words)

# 2. グラフ描画
make_graph(search_words, except_words, max_price, bins)
