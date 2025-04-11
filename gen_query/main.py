import json
import sys

def main():
    # コマンドライン引数を取得
    args = sys.argv[1:]  # 最初の引数(スクリプト名)を除く
    
    # 最初の引数をファイル名として使用
    filename = args[0] if args else 'wiki.json'

    with open(filename, 'r', encoding='utf-8') as f:
        text = json.load(f)
    
    # ここでtextを使った処理を行う
    print(f"ファイル {filename} を読み込みました")

if __name__ == "__main__":
    main()
