import json
from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers import BulkIndexError 

# --- 1) Connexion Elasticsearch ---

ES_ENDPOINT="https://localhost:9200"  
ES_API_KEY="cnZmOVhab0JVb2s3RGYyRFZ3Szg6dkJRNTBsdktJZlZxVHpRNmVDR01rUQ=="
INDEX_NAME="articles21k"             # nom de l'index qur elastic qui va recuillir les données
INPUT_FILE="../data/stage4_v3.json"  # A adapter selon le fichier qui veut être integré sur elastic

# Active/désactive le sous-champ text.semantic, ici désactivé pour performance
USE_SEMANTIC_TEXT = False

client = Elasticsearch(
    ES_ENDPOINT,
    api_key=ES_API_KEY,
    verify_certs=False  # Maintient la désactivation SSL pour votre environnement
)

# --- 2) Settings + Mappings ---

MAPPING = {
    "settings": {
        "analysis": {
            "normalizer": {                   # Normalisation des champs textes pour les mots-clés
                "lowercase_normalizer": {
                    "type": "custom",
                    "char_filter": [],        # Pas de char_filter
                    "filter": ["lowercase"]   # Applique la normalisation en minuscules
                }
            }
        }
    },
    "mappings": {       # Définition des mappings
        "properties": {
            "id": {"type": "long"}, 
            "date": {"type": "date", "format": "epoch_second"},
            "title": {
                "type": "text",
                "fields": {
                    "raw": {"type": "keyword", "ignore_above": 512, "normalizer": "lowercase_normalizer"}
                }
            },
            "lead": {"type": "text"},
            "text": {"type": "text"},
            "tags": {"type": "keyword"},
            "ner": {
                "properties": {
                    "PERSON": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "ORG": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "GPE": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "PRODUCT": {"type": "keyword", "normalizer": "lowercase_normalizer"}
                }
            },
            "structured": {
                "properties": {
                    "topics": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "overall_sentiment": {"type": "float"},
                    "sentiment_by_country": {
                        "type": "nested",
                        "properties": {
                            "country": {"type": "keyword"},
                            "sentiment": {"type": "float"}
                        }
                    },
                    "actors_mentioned": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "article_type": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "id": {"type": "long"}
                }
            }
        }
    }
}


# --- 3) Suppression/Création de l'index ---
print(f"Tentative de suppression de l'index '{INDEX_NAME}' s'il existe...")
client.options(ignore_status=[400, 404]).indices.delete(index=INDEX_NAME)

print(f"Création de l'index '{INDEX_NAME}' ...")
try:
    client.indices.create(index=INDEX_NAME, **MAPPING) # creation de l'index avec mapping
    print("Index créé avec succès.")
except Exception as e:
    print(f"Erreur lors de la création de l'index : {e}")
    exit()

# --- 4) Chargement des documents ---
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    docs = json.load(f)
print(f"{len(docs)} documents chargés depuis {INPUT_FILE}.")

# --- 5) Ingestion bulk (avec diagnostic d'erreur) ---
print(f"Ingestion vers '{INDEX_NAME}' ...")

try:
    # Les documents dans 'docs' doivent avoir un champ '_index' ou un champ 'id'
    # Pour l'ingestion, on s'assure que chaque doc a au moins '_index'
    actions = [
        {'_index': INDEX_NAME, **doc}       # le **doc sort tout les champs du dictionnaire
        for doc in docs
    ]
    ok, errors = helpers.bulk(client.options(request_timeout=300), actions, index=INDEX_NAME)
    
    # Si l'ingestion a réussi 
    print(f"Ingestion terminée : {ok} opérations réussies.")
    if errors:
        print(f"Des erreurs non critiques ont été remontées ({len(errors)} items). Inspectez 'errors' si besoin.")

except BulkIndexError as e:
    # CAPTURE DE L'ERREUR DÉTAILLÉE LORSQUE TOUT ÉCHOUE
    print("\n---------------- ERREURS CRITIQUES ----------------")
    print(f"Erreur d'indexation en masse : {len(e.errors)} documents rejetés.")
    
    # On affiche le message d'erreur du premier document rejeté 
    if e.errors:
        premier_echec = e.errors[0]
        # Vérifie si la clé 'error' est présente
        if 'error' in premier_echec['index']:
            error_detail = premier_echec['index']['error']
            
            print("\nCause la plus probable (1er document rejeté) :")
           
            if 'caused_by' in error_detail and 'field' in error_detail['caused_by']:
                print(f"Champ en cause: {error_detail['caused_by']['field']}")
            print(f"Type d'erreur: {error_detail['type']}")
            print(f"Raison: {error_detail['reason']}")
            
    print("---------------------------------------------------")
    exit()