import json                      
import re                        
import unicodedata               
import time                      
from pathlib import Path          
import spacy                     


INPUT_FILE = "../data/articles_complets.json"            # Fichier d'entrée 
OUTPUT_FILE = "../data/articles_avec_ner_clean.json"     # Fichier de sortie 
ORDER = ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]  # labels à conserver


def extract_ner(text: str, nlp_model): # Extrait les entités nommées d’un texte à l’aide du modèle spaCy et filtre les catégories d’intérêt.
    
    if not text:                                 # Vérifie que le texte n’est pas vide
        return {}                                

    doc = nlp_model(text)                        # Analyse du texte avec spaCy
    entities_temp = {label: [] for label in ORDER}  # Initialise les listes d’entités par type

    for ent in doc.ents:                         # Parcourt toutes les entités détectées et conserve que celles d'interet
        if ent.label_ in entities_temp:          
            entities_temp[ent.label_].append(ent.text)  

    ner_results = {}                             # Dictionnaire final des entités filtrées
    for label in ORDER:                          # Parcourt chaque type d’entité et supprime les doublons 
        unique_ents = list(set(entities_temp[label]))  
        if unique_ents:                          
            ner_results[label] = unique_ents     # Ajoute au dictionnaire final

    return ner_results                          



def uf(text: str) -> str:
    """Normalise le texte : Unicode, espaces, ponctuation."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)      # Normalisation Unicode
    t = t.replace("\u2019", "'")                 # Remplace les apostrophes typographiques
    t = t.strip()                                # Supprime les espaces en trop
    t = re.sub(r"\s+", " ", t)                   # Réduit les espaces multiples à un seul
    return t

def strip_leading_articles_org(s: str) -> str: # Supprime les articles ('the', 'a', 'an') au début des organisations.
    return re.sub(r"^(the|a|an)\s+", "", s, flags=re.I)

def strip_possessive(s: str) -> str:    # Supprime les formes possessives ('s).
    return re.sub(r"(\'s|’s)\b", "", s)

def is_acronym(token: str) -> bool:    # Détermine si un mot est un acronyme (majuscule, longueur 2-5).
    return token.isupper() and 2 <= len(token) <= 5

def titlecase_preserve_acronyms(s: str) -> str:    # Met en majuscule la première lettre sauf pour les acronymes.
    tokens = s.split()
    out = []
    for tok in tokens:
        if is_acronym(tok):
            out.append(tok)                      # Conserve l'acronyme tel quel
        else:
            out.append(tok.capitalize())         # Met en majuscule la première lettre
    return " ".join(out)

def surname(name: str) -> str:    # Retourne le dernier mot du nom
    parts = name.split()
    return parts[-1] if parts else ""

def consolidate_persons(persons): # Fusionne les variantes proches d’un même nom (ex: 'Putin' / 'Vladimir Putin').
    cleaned = [uf(p) for p in persons if p and p.strip()]  # Nettoyage de base et regroupementpar nom
    buckets = {}                                          

    for p in cleaned:
        ln = surname(p).lower() or p.lower()               # nom en minuscule
        buckets.setdefault(ln, set()).add(p)               # Ajout dans le groupe correspondant

    canonical = {}                                         # Choix du nom canonique
    for ln, variants in buckets.items():
        best = sorted(variants, key=lambda x: (len(x.split()), len(x)), reverse=True)[0]
        canonical[ln] = best                               # Variante la plus longue choisie

    out = set()                                            # Ensemble final des noms nettoyés
    for p in cleaned:
        ln = surname(p).lower() or p.lower()
        rep = canonical.get(ln, p)
        if p.lower() in rep.lower() or surname(p).lower() == surname(rep).lower():
            out.add(rep)
        else:
            out.add(p)

    final = []                                             # Liste finale triée et normalisée
    seen = set()
    for p in sorted(out, key=lambda s: s.lower()):
        pretty = titlecase_preserve_acronyms(p)
        key = pretty.lower()
        if key not in seen:
            seen.add(key)
            final.append(pretty)
    return final

def clean_org(o: str) -> str:    # Nettoie les noms d’organisations.
    o = uf(o)
    o = strip_possessive(o)
    o = strip_leading_articles_org(o)
    return titlecase_preserve_acronyms(o)

def clean_gpe(g: str) -> str:    # Nettoie les noms de lieux.
    g = uf(g)
    return titlecase_preserve_acronyms(g)

def clean_product(p: str) -> str:    # Nettoie les noms de produits.
    return uf(p)

def dedupe(items, cleaner):    # Supprime les doublons et conserve la variante la plus complète.
    bag = {}
    for it in items:
        if not it or not it.strip():
            continue
        val = cleaner(it)
        key = val.lower()
        if key not in bag or len(val) > len(bag[key]):
            bag[key] = val
    return sorted(bag.values(), key=str.lower)

def drop_empty_labels(ner_obj: dict) -> dict:    # Supprime les labels vides du dictionnaire d’entités.
    return {k: v for k, v in ner_obj.items() if isinstance(v, list) and len(v) > 0}

def process_article(a: dict) -> dict:     # Nettoie et consolide les entités pour un article donné.
    ner = a.get("ner") or {}
    persons = ner.get("PERSON", [])
    orgs    = ner.get("ORG", [])
    gpes    = ner.get("GPE", [])
    prods   = ner.get("PRODUCT", [])

    persons_c = consolidate_persons(persons)
    orgs_c    = dedupe(orgs, clean_org)
    gpes_c    = dedupe(gpes, clean_gpe)
    prods_c   = dedupe(prods, clean_product)

    ner_clean = {
        "PERSON": persons_c,
        "ORG": orgs_c,
        "GPE": gpes_c,
        "PRODUCT": prods_c,
    }
    ner_clean = drop_empty_labels(ner_clean)     # Supprime les catégories vides

    out = dict(a)
    out["ner"] = ner_clean                       # Remplace par la version nettoyée
    return out



def main():    # Exécute l’ensemble du  : extraction + nettoyage NER.
    try:
        print("Chargement du modèle spaCy 'en_core_web_trf'...")
        nlp = spacy.load("en_core_web_trf")      # Chargement du modèle
        print("Modèle chargé.")
    except OSError:
        print("Erreur : le modèle 'en_core_web_trf' n'est pas installé.")
        print("Installez-le avec : python -m spacy download en_core_web_trf")
        return

    if not Path(INPUT_FILE).exists():            # Vérifie que le fichier d’entrée existe
        print(f"Erreur : fichier introuvable : {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)                  # Chargement des articles au format JSON

    print(f"{len(articles)} articles à traiter.\n")

    results = []
    start = time.time()                          # Mesure du temps total

    # Étape 1 : Extraction NER
    for i, art in enumerate(articles, start=1):
        article_id = art.get("id", "N/A")
        title = art.get("title", "Sans titre")[:80]
        text = art.get("text", "")

        print(f"[{i}/{len(articles)}] Analyse (ID: {article_id}) : {title}...")
        ner_entities = extract_ner(text, nlp)    # Extraction des entités

        art_result = dict(art)
        if ner_entities:
            art_result["ner"] = ner_entities     # Ajout du champ 'ner' si non vide
        results.append(art_result)

    # Étape 2 : Nettoyage et regroupement
    print("\nNettoyage et regroupement des entités...")
    cleaned = [process_article(a) for a in results]  # Application du nettoyage

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)  # Sauvegarde du JSON propre

    print(f"\nTerminé : {len(cleaned)} articles traités")
    print(f"Fichier final : {OUTPUT_FILE}")
    print(f"Durée totale : {time.time() - start:.2f} secondes")

# Lancement du programme principal
if __name__ == "__main__":
    main()
