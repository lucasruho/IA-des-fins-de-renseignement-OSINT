import json

# --- 1) Chargement des articles ---
try:
    with open("../data/stage4_V3.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
except FileNotFoundError:
    print("Erreur : Le fichier 'stage4_V3.json' est introuvable.")
    exit()
except json.JSONDecodeError:
    print("Erreur : Le fichier 'stage4_V3.json' n'est pas un JSON valide.")
    exit()


# --- Transformer chaque article en country-sentiment ---
output = []

for article in articles:
    article_id = article.get("id") # ID de l'article
    article_date = article.get("date") # Date de l'article


    structured_data = article.get("structured") or {}  # Accès aux données structurées

   
    for c in structured_data.get("sentiment_by_country", []):   # Pour chaque pays mentionné on recupere son sentiment, son nom et l'id de l'article ainsi que la date
        output.append({
            "id": article_id,
            "date": article_date,
            "country": c.get("country"),
            "sentiment": c.get("sentiment")
        })

# --- Sauvegarde du résultat ---
with open("../data/articles_pays_21k.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print(f"{len(output)} entrées générées dans 'articles_pays_21k.json'")