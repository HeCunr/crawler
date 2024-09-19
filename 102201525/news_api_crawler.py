import requests
import json
import certifi

# 请在此处替换为您的 News API 密钥
API_KEY = '04c1848491d143f9a9af8a64655167e8'

# 定义查询参数
query = '2024 Paris Olympics AND AI technology'
language = 'en'
page_size = 100

# 定义请求 URL 和参数
url = 'https://newsapi.org/v2/everything'
params = {
    'q': query,
    'language': language,
    'pageSize': page_size,
    'apiKey': API_KEY
}

def fetch_articles():
    all_articles = []
    page = 1
    while True:
        params['page'] = page
        try:
            response = requests.get(url, params=params, proxies={"http": None, "https": None})

            response.raise_for_status()  # 检查HTTP错误
            data = response.json()

            if data['status'] != 'ok':
                print(f"获取文章时出错：{data.get('message')}")
                break

            articles = data.get('articles', [])
            if not articles:
                break

            all_articles.extend(articles)
            print(f"已获取第 {page} 页，共 {len(all_articles)} 篇文章")
            page += 1

            if len(all_articles) >= 100:
                break

        except requests.exceptions.RequestException as e:
            print(f"请求出现异常：{e}")
            break

    return all_articles

def save_articles(articles, filename='articles.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print(f"已将 {len(articles)} 篇文章保存到 {filename}")

if __name__ == '__main__':
    articles = fetch_articles()
    if articles:
        save_articles(articles)
