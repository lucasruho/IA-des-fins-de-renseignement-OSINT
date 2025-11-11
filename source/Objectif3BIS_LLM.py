import json
import os
from dotenv import load_dotenv
from mistralai import Mistral 

# --- 1. Configuration et Initialisation ---

# Charger les variables du fichier .env
load_dotenv()

# Récupérer la clé API Mistral depuis les variables d'environnement
api_key = os.getenv("cle_API") 

if not api_key:
    raise ValueError("Clé API Mistral introuvable dans le fichier .env")

# Initialiser le client Mistral avec la clé API
client = Mistral(api_key=api_key)
MODEL_NAME = "mistral-medium-latest" # définition du modèle à utiliser

# Fichiers de données
FICHIER_ENTREE = "../data/resultat_bapt_100.json"
FICHIER_SORTIE = "../data/resultat_llm_mistral_final.json"

# --- 2. Définition du Schéma et du Prompt Système ---

# Le SCHÉMA DE SORTIE STRICT que l'on veut
JSON_SCHEMA = {
    "topics": ["string"],
    "overall_sentiment": 0.0,
    "sentiment_by_country": [
        {"country": "string", "sentiment": 0.0}
    ],
    "actors_mentioned": ["string"],
    "article_type": "string",
    "id": 0
}

# prompt en anglais pour permettre une meilleure compréhension par le LLM
SYSTEM_PROMPT = f"""
You are an expert in news content analysis. Your task is to analyze the text of a press article and extract structured information from it in strict JSON format.

You must respond only with a JSON object that adheres to the following output schema:
{json.dumps(JSON_SCHEMA, indent=4)}

Specific Analysis Instructions:
1. Semantic Analysis: Generate the fields 'topics', 'overall_sentiment', 'sentiment_by_country', 'actors_mentioned', and 'article_type' based only on the semantic analysis of the 'Titre', 'Résumé', and 'Texte' of the provided article.
2. Sentiment: The 'sentiment' value (global and per country) must be a float between -1.0 (very negative) and 1.0 (very positive).
3. Country Codes: Use ISO 3166-1 alpha-2 codes (e.g., RU, US, UA) for the 'country' field.
4. ID: The 'id' field in the JSON output must exactly match the ID of the article provided in the input.
5. Format: Do NOT add ANY text, explanation, or commentary outside of the JSON object itself.
"""

# --- 3. Fonction de Traitement d'Article ---

def get_structured_data(article_data): # Fonction pour structurer les données d'un article
   
    
    user_prompt = f"""
Article ID: {article_data['id']}

Titre: {article_data.get('title', '')}
Résumé: {article_data.get('lead', '')}
Texte: {article_data.get('text', '')}

Génère l'objet JSON structuré correspondant.
"""
    
    # Utilisation de dictionnaires simples pour les messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        # Utilisation de client.chat.complete() pour obtenir la complétion
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"} # Demande de réponse au format JSON 
        )
        
        json_string = response.choices[0].message.content
        structured_data = json.loads(json_string)
        
        article_data['structured'] = structured_data
        
        return article_data
        
    except Exception as e:
        print(f"Erreur lors du traitement de l'article {article_data['id']} : {e}")
        article_data['error_llm'] = str(e)
        return article_data


# --- 4. Boucle Principale de Traitement ---

try:
    with open(FICHIER_ENTREE, 'r', encoding='utf-8') as f:
        articles = json.load(f)
except Exception as e:
    print(f"Erreur de lecture du fichier '{FICHIER_ENTREE}' : {e}")
    exit()

# Traitement de test : les 100 premiers articles 
ARTICLES_A_TRAITER = 100 
articles_traites = []

print(f"Démarrage du traitement de {ARTICLES_A_TRAITER} articles avec le modèle {MODEL_NAME}...")
print("----------------------------------------------------------------------")

for i, article in enumerate(articles[:ARTICLES_A_TRAITER]):
    print(f"Traitement de l'article {i+1}/{ARTICLES_A_TRAITER} (ID: {article['id']})...", end="")
    
    resultat = get_structured_data(article)
    articles_traites.append(resultat)
    
    status = "SUCCÈS" if 'structured' in resultat else "ÉCHEC"
    print(f"\rTraitement de l'article {i+1}/{ARTICLES_A_TRAITER} (ID: {article['id']}) : {status}")

print("----------------------------------------------------------------------")

# Sauvegarde des résultats
try:
    with open(FICHIER_SORTIE, 'w', encoding='utf-8') as f:
        json.dump(articles_traites, f, indent=4, ensure_ascii=False)

    print(f"\nTraitement terminé. {len(articles_traites)} articles sauvés dans '{FICHIER_SORTIE}'.")

except Exception as e:
    print(f"Erreur lors de la sauvegarde du fichier : {e}")