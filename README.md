# Projet IA à des fins de Renseignement

👥 **Équipe projet :**  
- LOTTIAUX Adrien 
- RUHOMUTALLY Lucas  

Projet réalisé dans le cadre du module *IA à des fins de renseignement (OSINT)*  
Plateforme : SSPCloud (Onyxia)

*Testé avec Python 3.10+*

##  Sommaire
- [1. Présentation rapide du projet](#1-présentation-rapide-du-projet)
- [2. Description des étapes](#2-description-des-étapes)
- [3. Tableau récapitulatif](#3-tableau-récapitulatif)
- [4. Tutoriel d’utilisation](#4-tutoriel-dutilisation)
- [5. Dépendances par partie](#5-dépendances-par-partie)
- [6. Résultats analytiques et visualisation](#6-résultats-analytiques-et-visualisation)
- [7. Résumé](#7-résumé)

## 1. Présentation rapide du projet
Ce projet vise à construire un corpus d’articles issus du site **TASS** (agence de presse russe), puis à mettre en place une chaîne d’analyse OSINT complète :  
1. **Collecte** d’articles via API,  
2. **Extraction** du texte et des métadonnées,  
3. **Analyse NER (entités nommées)**,  
4. **Structuration sémantique via LLM (Mistral)**,  
5. **Indexation et visualisation** des résultats dans Elasticsearch/Kibana.  

L’objectif est de **comprendre la rhétorique d’État russe** en étudiant les acteurs, lieux, thèmes et sentiments présents dans les articles.

>Ce pipeline OSINT automatise la transformation d’une source médiatique brute (TASS) en une base de données exploitable pour l’analyse stratégique, permettant de détecter les tendances narratives, la perception internationale de la Russie, et la polarité des discours dans le temps.


---

## 2. Description des étapes

### Objectif 1 — Récupérer et filtrer les articles (API TASS)
- Envoie une requête POST à l’API TASS `categoryNewsList` pour récupérer des articles.
- Filtre les articles selon une plage de dates définie.
- Sauvegarde la sortie dans `data/resultat_filtre.json`.

**Sortie :** `resultat_filtre.json` — liste d’articles filtrés avec leurs métadonnées de base.

---

### Objectif 2 — Extraire le contenu complet des articles
- Lit le fichier `resultat_filtre.json`.
- Télécharge le contenu HTML de chaque article.
- Extrait le **texte principal** et les **tags** via *BeautifulSoup*.
- Conserve les métadonnées originales et sauvegarde dans `data/articles_complets.json`.

**Sortie :** `articles_complets.json` — texte complet + tags pour chaque article.

---

### Objectif 3 — Reconnaissance d’entités nommées (NER)
- Utilise le modèle **spaCy** `en_core_web_trf` pour détecter les entités : `PERSON`, `ORG`, `GPE`, `PRODUCT`, `EVENT`.
- Nettoie et déduplique les entités détectées.
- Produit un fichier `data/articles_avec_ner_clean.json`.



**Sortie :** `articles_avec_ner_clean.json` — articles enrichis avec les entités NER nettoyées.

---

### Objectif 3BIS — Structuration sémantique via LLM (Mistral)
- Utilise l’API **Mistral** via le SDK `mistralai`.
- Nécessite une **clé API Mistral** à placer dans un fichier `.env` : `cle_API=VOTRE_CLE_MISTRAL`
- Le LLM renvoie une **analyse structurée** :
  - `topics`  
  - `overall_sentiment`  
  - `sentiment_by_country` (avec codes ISO2)  
  - `actors_mentioned`  
  - `article_type`  
  - `id`

#### **Note importante :**
L’analyse a été réalisée sur 100 articles issus du jeu de données fourni par Baptiste HUVELLE afin d’accélérer le traitement et de limiter la consommation de tokens lors des appels à l’API Mistral.

**Sortie :** `data/resultat_llm_mistral_final.json` — analyse sémantique enrichie de chaque article.

---


### Objectif 4 — Indexation et visualisation (Elasticsearch & Kibana)
- Nous avons utilisé le fichier JSON complet fourni par le professeur, contenant 21 742 articles issus de tass.com, afin de réaliser des dashboards complets.
- Le script `Objectif4_elastic.py` permet d’adapter et d’envoyer la base de données complète dans Elasticsearch.
- L’index contient :
  - les `tags`, `ner.*` (PERSON, ORG, GPE, etc.),
  - les `structured.*` (topics, sentiments, acteurs, etc.).

Pour créer un dashboard du sentiment global par pays, nous avons d’abord restructuré les données à l’aide du script `convertir_pays.py`.

Ce script génère le fichier `articles_pays_21k.json` au format suivant :
```json
[
  { "id": 2035207, "date": 1761470423, "country": "RU", "sentiment": 0.5 },
  { "id": 2035199, "date": 1761467797, "country": "RU", "sentiment": 0.1 },
  { "id": 2035199, "date": 1761467797, "country": "UA", "sentiment": -0.7 }
]
```

**Sortie :** un **index Elasticsearch** prêt à l’emploi pour dashboards Kibana.

---

## 3. Tableau récapitulatif

| Étape | Script                         | Entrée                                               | Sortie JSON                       | Description                            |
| :---: | :----------------------------- | :--------------------------------------------------- | :-------------------------------- | :------------------------------------- |
|   1   | `Objectif1_trier_articles.py`  | tass.com                                             | `resultat_filtre.json`            | Récupère et filtre les articles        |
|   2   | `Objectif2_contenu_article.py` | `resultat_filtre.json`                               | `articles_complets.json`          | Extrait texte complet et tags          |
|   3   | `Objectif3_NER.py`             | `articles_complets.json`                             | `articles_avec_ner_clean.json`    | Détecte et nettoie les entités nommées |
|  3BIS | `Objectif3BIS_LLM.py`          | 100 articles `resultat_bapt_100.json`                | `resultat_llm_mistral_final.json` | Analyse sémantique via LLM (Mistral)   |
|   4   | `Objectif4_elastic.py`         | JSON du professeur (21 742 articles) `stage4_v3.json`| Index Elasticsearch               | Envoie la base complète vers Elastic   |


---

## 4. Tutoriel d’utilisation

### Étapes 1 à 3 (avec 3BIS) — via **Onyxia SSPCloud Datalab**

1. **Lancer** un service **VSCode-Python** sur Onyxia (SSPCloud).  
2. **Cloner** le dépôt du projet.  
3. **Installer les bibliothèques nécessaires :**
 ```bash
 pip install requests beautifulsoup4 spacy python-dotenv mistralai elasticsearch
 python -m spacy download en_core_web_trf
 ```
4. Exécuter les scripts dans l’ordre :

```bash
python Objectif1_trier_articles.py
python Objectif2_contenu_article.py
python Objectif3_NER.py
```

5. Configurer la clé Mistral (Objectif 3BIS) :
- Créez un fichier .env : `cle_API=VOTRE_CLE_MISTRAL`
- Puis lancer :
  ```bash
   python Objectif3BIS_LLM.py
  ```

### Étape 4 — via Docker Compose en local
Cette étape te permet de démarrer un **cluster Elasticsearch multi-nœuds avec Kibana** à l’aide de **Docker Compose**, comme décrit dans la documentation officielle Elastic.

> ⚠️ Attention : ne pas versionner le fichier .env contenant la clé API Mistral.

#### 1. Préparation
1. Installer **Docker** et **Docker Compose**.  

2. Créer un **nouveau dossier** de projet vide (ex: `elastic-cluster`).

3. Télécharger les deux fichiers de configuration officiels :
   - [`docker-compose.yml`](https://github.com/elastic/elasticsearch/blob/master/docs/reference/setup/install/docker/docker-compose.yml)
   - [`.env`](https://github.com/elastic/elasticsearch/blob/master/docs/reference/setup/install/docker/.env)

   Les placer dans ton dossier `elastic-cluster/`.

---

#### 2. Configuration du fichier `.env`

Ouvrir le fichier `.env` et **modifier les variables suivantes** :

```bash
# Mot de passe pour l'utilisateur 'elastic' (min. 6 caractères alphanumériques)
ELASTIC_PASSWORD=changeme

# Mot de passe pour l'utilisateur 'kibana_system'
KIBANA_PASSWORD=changeme

# Version de la stack Elastic (à ajuster si besoin)
STACK_VERSION=9.2.0

# Port HTTP exposé (ne pas exposer publiquement)
ES_PORT=127.0.0.1:9200
```
#### 3. Démarrer le cluster :
Depuis le dossier du projet :
```bash
docker compose up -d
```
Cela lance trois nœuds Elasticsearch et Kibana dans des conteneurs séparés.

Une fois le cluster prêt :

- Kibana → http://localhost:5601

- Elasticsearch → http://127.0.0.1:9200

Se connecter à Kibana avec :
```yaml
Nom d’utilisateur : elastic
Mot de passe : changeme
```
#### 4. Indexer les articles :

##### A) Indexer l'intégralité des 21 742 articles du professeur
- Dans Objectif4_elastic.py, vérifier :
```python
INDEX_NAME = "tass_osint"
INPUT_FILE = "data/stage4_v3.json"
```
- Puis lancer 
```bash
python Objectif4_elastic.py
```

##### B) Indexer le dataset pour le dashboard "sentiment par pays"
- Lancer 
```bash
python convertir_pays.py
```
- Dans Objectif4_elastic.py, **modifier** :
```python
INDEX_NAME = "tass_osint_countries"
INPUT_FILE = "data/articles_pays_21k.json"
```
- Puis lancer 
```bash
python Objectif4_elastic.py
```
- L’index est alors créé et alimenté.

#### 5. Créer deux Data View dans Kibana :
Une fois les index créés dans Elasticsearch, il faut créer deux Data View distinctes dans Kibana afin d’explorer séparément :
- le corpus complet des articles (21 742),
- et le jeu de données agrégé des sentiments par pays.

##### A) Data View 1 — Corpus complet
1. Ouvrir Kibana → Stack Management → Data Views → Create data view.
2. Nom : `tass-osint`
3. Pattern : `tass_osint`
4. Time field : `date` *correspond à un timestamp UNIX (epoch seconds)*
5. Valider la création.

**Champs principaux à explorer :**
- `tags`
- `ner.PERSON`, `ner.ORG`, `ner.GPE`
- `structured.topics`, `structured.actors_mentioned`
- `structured.overall_sentiment`, `structured.sentiment_by_country.sentiment`

Cette Data View permet d’analyser la structure sémantique complète (entités, thèmes, tonalité, acteurs, etc.) issue du pipeline d’analyse OSINT.

##### B) Data View 2 — Sentiment par pays
1. Ouvrir Kibana → Stack Management → Data Views → Create data view.
2. Nom : `tass-osint-countries`
3. Pattern : `tass_osint_countries`
4. Time field : `date` *correspond à un timestamp UNIX (epoch seconds)*
5. Valider la création.

**Champs principaux à explorer :**
- `country`
- `sentiment`

Cette Data View repose sur le fichier `articles_pays_21k.json`, généré via le script `convertir_pays.py`.
Elle permet de visualiser le sentiment global par pays, par exemple :
- la moyenne du sentiment (`avg(sentiment)`) par `country`,
- l’évolution temporelle du ton des articles selon les zones géographiques.

## 5. Dépendances par partie
  
| Partie        | Bibliothèques principales                       |
| :------------ | :---------------------------------------------- |
| Objectif 1–2  | `requests`, `beautifulsoup4`, `pathlib`, `time` |
| Objectif 3    | `spacy`, `en_core_web_trf`                      |
| Objectif 3BIS | `python-dotenv`, `mistralai`                    |
| Objectif 4    | `elasticsearch`, `elasticsearch.helpers`        |

## 6. Résultats analytiques et visualisation

Une fois les données indexées dans Elasticsearch, nous avons conçu plusieurs **dashboards Kibana** afin d’explorer les tendances médiatiques et sémantiques de la presse russe (TASS).

### Objectifs analytiques
L’analyse vise à identifier :
- Les **acteurs les plus cités** (personnalités politiques, organisations, pays).  
- Les **thématiques dominantes** (topics) et leur évolution temporelle.  
- Le **sentiment global** des articles, notamment **par pays mentionné**, pour évaluer la tonalité du discours médiatique.  
- Les **corrélations entre acteurs et tonalité** (ex. relations positives/négatives entre États).  

### Dashboards réalisés
1. **Répartition des sentiments par pays**  
   → Visualisation du champ `structured.sentiment_by_country.sentiment`, permettant de repérer les zones géopolitiques valorisées ou critiquées par la presse russe.

2. **Fréquence des acteurs les plus cités**  
   → Basé sur `structured.actors_mentioned` et `ner.PERSON` / `ner.ORG`, pour détecter les figures et institutions dominantes dans le discours.

3. **Analyse thématique (topics)**  
   → Exploration des champs `structured.topics` pour observer les sujets récurrents : conflits, diplomatie, énergie, économie, etc.

4. **Distribution des sentiments globaux**  
   → Moyenne des `structured.overall_sentiment` pour estimer la tonalité générale du corpus (positif / négatif / neutre).

5. **Nuage de mots et filtres croisés**  
   → Permet une exploration dynamique du corpus : filtrage par date, acteur, ou sujet afin d’étudier les cooccurrences.

Ces visualisations offrent une **lecture OSINT claire** des orientations narratives de TASS.  
Elles permettent de **cartographier la rhétorique médiatique russe**, en mettant en lumière :
- les **alliances perçues positivement**,  
- les **adversaires représentés négativement**,  
- et les **thèmes géopolitiques dominants** sur la période étudiée.

>  Les dashboards présentés (voir `Dashboard final.pdf` et `dashboard100.pdf`) illustrent concrètement ces analyses.

## 7. Résumé


### 🔄 Pipeline global


TASS.com → Extraction HTML → NER (spaCy) → Structuration (Mistral) → Indexation (Elastic) → Visualisation (Kibana)

Ce pipeline OSINT complet permet de :

1. Collecter des articles depuis TASS,
2. Extraire le texte et les métadonnées,
3. Identifier les entités nommées,
4. Enrichir les données sémantiquement via un LLM,
5. Visualiser les résultats dans un dashboard interactif Kibana.

