import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

# === Configuration ===
INPUT_FILE = "../data/resultat_filtre.json"   # fichier d’entrée
OUTPUT_FILE = "../data/articles_complets.json"     # fichier de sortie
BASE_URL = "https://tass.com"

# --- Cookies et headers généré par curlconverter.com ---
cookies = {
    'spid': '1761819317890_67a022ec8674c53b37b7c9b6f0d8941f_jfkqmonixdsoo176',
    '_ym_uid': '176181931877156985',
    '_ym_d': '1761819318',
    '_ym_isad': '2',
    'newsListCounter': '8',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=0, i',
    'referer': 'https://tass.com/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'spid=1761819317890_67a022ec8674c53b37b7c9b6f0d8941f_jfkqmonixdsoo176; _ym_uid=176181931877156985; _ym_d=1761819318; _ym_isad=2; newsListCounter=8',
}


def extract_article_content(html: str): 
    # Extrait le texte de <div class="text-block"> et les tags de <div class="tags__list">
    soup = BeautifulSoup(html, "html.parser")

    # Contenu principal
    text_block = soup.select_one("div.text-block")
    text = ""
    if text_block:
        paragraphs = [p.get_text(" ", strip=True) for p in text_block.select("p")] # A chaque nouveau paragraphe, on ajoute un double /n pour séparer les contenu de l'article
        text = "\n\n".join(paragraphs)

    # Tags
    tags = [a.get_text(strip=True) for a in soup.select("div.tags__list a.tags__item")]

    return text, tags


def get_article(url: str, session: requests.Session):
    # Télécharge et parse un article donné
    try:
        r = session.get(url, headers=headers, cookies=cookies, timeout=15)
        if r.ok:
            return extract_article_content(r.text)
        else:
            print(f"[!] Erreur HTTP {r.status_code} sur {url}")
            return "", []
    except requests.RequestException as e:
        print(f"[!] Erreur de connexion sur {url}: {e}")
        return "", []


def main():
    # Lecture du JSON d’entrée
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data if isinstance(data, list) else data.get("newsList", []) # Récupération des articles dans le fichier d'entré JSON
    print(f"→ {len(articles)} articles à traiter.\n")

    results = []
    with requests.Session() as session:
        for i, art in enumerate(articles, start=1):
            # Construction URL complète
            url = BASE_URL + art["link"]

            print(f"[{i}/{len(articles)}] Téléchargement : {url}") # Affichage du nombre d'articles traités sur le nombre restant
            text, tags = get_article(url, session)

            # On garde TOUTES les clés d’origine + on ajoute text et tags
            art_result = dict(art)
            art_result["text"] = text
            art_result["tags"] = tags
            results.append(art_result)

            time.sleep(0.4)  # pause pour éviter le bannissement

    # Écriture du fichier final
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n Terminé ! {len(results)} articles enregistrés dans '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()
