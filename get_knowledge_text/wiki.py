from datasets import load_dataset
import re
import json

def main():
    articles = extract_kirara_articles()
    # for article in articles:
    #     print(f"Title: {article['title']}")
    #     print(f"URL: {article['source']}")
    #     print("-" * 50)
        
    # JSONファイルとして保存
    with open('wiki.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def extract_kirara_articles():
    """
    Wikimedia/Wikipediaの日本語サブセットから
    『まんがタイムきらら』と『4コマ漫画作品』に関連する記事を抽出する
    """
    # データセットのロード
    dataset = load_dataset('wikimedia/wikipedia', '20231101.ja')
    
    # 検索キーワード
    keywords_and = ['4コマ漫画作品']
    keywords_or = ['まんがタイムきららの4コマ漫画作品', 'まんがタイムKRコミックスのアニメ作品', 'まんがタイムきららフォワード']
    
    # キーワードを含む記事をフィルタリング
    filtered_articles = []
    for article in dataset['train']:
        text = article['text']
        if all(keyword in text for keyword in keywords_and) and any(keyword in text for keyword in keywords_or):
            filtered_articles.append({
                'title': article['title'],
                'text': text,
                'source': f"https://ja.wikipedia.org/wiki/{article['title']}"
            })

    
    return filtered_articles

if __name__ == "__main__":
    main()
