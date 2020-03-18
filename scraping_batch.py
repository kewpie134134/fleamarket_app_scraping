import pandas as pd
from selenium import webdriver
import matplotlib.pyplot as plt
import time
import csv
import os
import datetime


def search_mercari(search_words):

    # 検索ワードをそのままディレクトリ名とするため、一時避難する
    org_search_words = search_words

    # 検索ワードが複数の場合、「+」で連結するよう整形する
    words = search_words.split("_")
    search_words = words[0]
    for i in range(1, len(words)):
        search_words = search_words + "+" + words[i]

    # メルカリで検索するためのURL
    url = "https://www.mercari.com/jp/search/?keyword=" + search_words

    # ブラウザを開く
    # 本pythonファイルと同じディレクトリにchromeriver.exeがある場合、
    # 引数空でも良い
    browser = webdriver.Chrome()

    # 起動時に時間がかかるため、5秒スリープ
    time.sleep(5)

    # 表示ページ
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
            # 商品ごとのHTMLを全取得
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

                # 商品のURLを取得
                Url = post.find_element_by_css_selector(
                    "a").get_attribute("href")

                # スクレイピングした情報をリストに追加
                se = pd.Series([title, price, sold, Url], columns)
                df = df.append(se, columns)

            # ページ数をインクリメント
            page += 1
            # 次のページに進むためのURLを取得
            url = browser.find_element_by_css_selector(
                "li.pager-next .pager-cell a").get_attribute("href")
            print("Moving to next page ...")
    except:
        print("Next page is nothing.")

    # 最後に得たデータをCSVにして保存
    filename = "mercari_scraping_" + org_search_words + ".csv"
    df.to_csv(org_search_words + "/" + filename, encoding="utf-8-sig")
    print("Finish!")


def make_graph(search_words, except_words, max_price, bins):
    # CSV ファイルを開く
    df = pd.read_csv(search_words + "/" +
                     "mercari_scraping_" + search_words + ".csv")

    # "Name"に"except_words"が入っているものを除く
    if(len(except_words) != 0):
        exc_words = except_words.split("_")
        for i in range(len(exc_words)):
            df = df[df["Name"].str.contains(exc_words[i]) == False]
    else:
        pass

    # 購入済み(sold=1)の商品だけを表示
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
    dfPercent.to_csv(search_words + "/" + filename, encoding="utf-8-sig")

    # グラフの描画
    """
    :param kind: グラフの種類を指定
    :param y: y 軸の値を指定
    :param bins: グラフ幅を指定 
    :param alpha: グラフの透明度(0:透明 ~ 1:濃い)
    :param figsize: グラフの大きさを指定
    :param color: グラフの色
    :param secondary_y: 2 軸使用の指定(Trueの場合)
    """
    ax1 = dfSold.plot(kind="hist", y="Price", bins=25,
                      secondary_y=True, alpha=0.9)
    dfPercent.plot(kind="area", x="Price", y=[
        "Percent"], alpha=0.5, ax=ax1, figsize=(20, 10), color="k")
    plt.savefig(search_words + "/" + "mercari_histgram_" +
                search_words + ".jpg")


def read_csv():
    # メルカリ検索用リストのcsvファイルを読み込む
    with open("mercari_search.csv", encoding="utf-8") as f:

        # 検索ワード格納用の空リストを準備
        csv_lists = []
        # csvファイルの何行目を読み込むかを確認するためのカウンター
        counter = 0

        # csvファイルを1行ずつ読み込む
        reader = csv.reader(f)
        for row in reader:
            counter += 1
            csv_lists.append(row)
            try:
                # 検索ワードチェック
                # 空の場合、エラーメッセージを表示して終了する
                if(len(row[0]) == 0):
                    print("File Error: 検索ワードがありません-> " +
                          "mercari_search.csv " + str(counter) + "行目")
                    break
            except IndexError:
                # 行が空いている場合、エラーメッセージを表示して終了する
                print("File Error: CSVファイルに問題があります。行間を詰めるなどしてください。")
                break
            try:
                if(len(row[2]) == 0):
                    # グラフ描画時の最高値チェック
                    # 空の場合、エラーメッセージを表示して終了する
                    print("File Error: 金額が設定されていません-> " +
                          "mercari_search.csv " + str(counter) + "行目")
                    break
                else:
                    try:
                        int(row[2])
                    except ValueError:
                        # 値が数字出ない場合、エラーメッセージを表示して終了する
                        print("File Error: 金額には数字を入力してください-> " +
                              "mercari_search.csv " + str(counter) + "行目")
                        break
            except IndexError:
                # そもそも金額自体が書かれていない場合、エラーメッセージを表示して終了する。
                print("File Error: 金額が設定されていません-> " +
                      "mercari_search.csv " + str(counter) + "行目")
                break
            try:
                if(len(row[3]) == 0):
                    # グラフ描画時の最高値チェック
                    # 空の場合、エラーメッセージを表示して終了する
                    print("File Error: グラフ幅が設定されていません-> " +
                          "mercari_search.csv " + str(counter) + "行目")
                    break
                else:
                    try:
                        int(row[3])
                    except ValueError:
                        # 値が数字出ない場合、エラーメッセージを表示して終了する
                        print("File Error: グラフ幅には数字を入力してください->" +
                              "mercari_search.csv " + str(counter) + "行目")
                        break
            except IndexError:
                # そもそも金額自体が書かれていない場合、エラーメッセージを表示して終了する。
                print("File Error: グラフ幅が設定されていません-> " +
                      "mercari_search.csv " + str(counter) + "行目")
                break
        return csv_lists

# ------------------------------------------------------ #


# 処理開始時刻を記録
start_time = datetime.datetime.now()

# 0. メルカリ検索CSVファイルから読み取ったリストを格納する箱を用意
"""
検索用CSVファイルからリストを読み込む
:param csv_lists[i][0]: 検索ワード
:param csv_lists[i][1]: 検索結果から除外するワード
:param csv_lists[i][2]: グラフ表示する際の最高金額
:param csv_lists[i][3]: グラフ幅(bin)
"""
csv_lists = read_csv()

# バッチ処理
for i in range(len(csv_lists)):
    # 1. ディレクトリ作成
    os.mkdir(csv_lists[i][0])
    # 2. スクレイピング処理
    search_mercari(csv_lists[i][0])
    # 3. グラフ描画
    make_graph(csv_lists[i][0], csv_lists[i][1],
               int(csv_lists[i][2]), int(csv_lists[i][3]))

# 処理終了時刻を記録
end_time = datetime.datetime.now()

# 全処理が完了するまでにかかった時間を算出
print("All Finish!!")
print("実行処理時間：" + str(end_time - start_time))
