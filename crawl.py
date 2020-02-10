import requests
from bs4 import BeautifulSoup
import pandas as pd
from multiprocessing import Pool, cpu_count


def parse_page(page):
    pool = []
    soup = BeautifulSoup(page.text, 'html.parser')
    articles = soup.find_all("article")
    for article in articles:
        header = article.find("a", class_='header-h3')
        title = header.getText()
        url = "https://www.banki.ru" + header["href"]
        try:
            mark = article.find("span", itemprop="rating").getText().strip()
        except:
            mark = None
        try:
            time = article.find("time", class_="display-inline-block").getText()
        except:
            time = None
        pool.append((title, url, mark, time))
    df = pd.DataFrame(pool, columns=["Title", "url", "mark", "time"])
    return df


def crawl_pages():
    i = 1
    pool = []
    while True:
        url = "https://www.banki.ru/services/responses/bank/sberbank/?is_countable=on&page={}".format(str(i))
        page = requests.get(url)
        if not (i % 300):
            print(i)
        if page.status_code == 404:
            break
        else:
            df = parse_page(page)
            pool.append(df)
            i += 1
    df = pd.concat(pool)
    df = df[df.time.notna()]
    return df


def parse_text(url):
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        text = soup.find("div", itemprop="description").getText().strip()
    except:
        text = None
    return url, text


def main():
    df = crawl_pages()
    df.to_csv("data/banki_data.csv")
    p = Pool(cpu_count())
    result = p.map(parse_text, df.url.values)
    df_texts = pd.DataFrame(result, columns=["url", "text"])
    df_texts = df_texts[df_texts.text.notna()]
    df_full_data = df.merge(df_texts)
    df_full_data.to_json("full_data.json")


main()
