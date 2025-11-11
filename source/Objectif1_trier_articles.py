import requests
import json

# --- Cookies et headers généré par curlconverter.com ---
cookies = {
    'spid': '1761819328340_b441a5eb0df51df8a1beb5c2832cf624_g5tabwck8i4o4x88',
    '_ym_uid': '1761819327166514326',
    '_ym_d': '1761819327',
    'newsListCounter': '0',
    '_ym_isad': '2',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://tass.com',
    'priority': 'u=1, i',
    'referer': 'https://tass.com/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'spid=1761819317890_67a022ec8674c53b37b7c9b6f0d8941f_jfkqmonixdsoo176; _ym_uid=176181931877156985; _ym_d=1761819318; newsListCounter=0; _ym_isad=2',
}

# --- Corps JSON de la requête ---
json_data = {
    'sectionId': 4953,
    'limit': 200000,
    'type': 'all',
    'excludeNewsIds': '2039839,2039681,2039641,2039585',
    'imageSize': 434,
}

start_date = 1682940613 # Date de début 2023-05-01 13:30:13
end_date = 1697519349 # Date de fin 2023-10-17 07:09:09


response = requests.post(
    'https://tass.com/userApi/categoryNewsList',
    cookies=cookies,
    headers=headers,
    json=json_data,
    timeout=10
)

data = response.json()


# --- Filtrer les articles selon la date ---
filtered_news = [
    article for article in data["newsList"]
    if start_date <= article["date"] <= end_date
]

print(f"{len(filtered_news)} articles trouvés entre les deux dates.")

# --- Enregistrer dans un nouveau fichier ---
with open("../data/resultat_filtre.json", "w", encoding="utf-8") as f:
    json.dump(filtered_news, f, ensure_ascii=False, indent=4)

print("Résultats filtrés enregistrés dans 'data/resultat_filtre.json'")
