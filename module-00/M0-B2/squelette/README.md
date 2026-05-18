# M0-B2 — Squelette : sentiment FR Aubergine Hôtels

Stack `docker compose` à 2 services qui démarre dès le clone (healthcheck
inclus).

```bash
# 1. Configurer l'environnement
cp .env.example .env

# 2. Construire et lancer la stack
docker compose up --build

# 3. Vérifier
curl http://localhost:8000/health        # API NLP
open  http://localhost:8501              # UI Streamlit
```

À l'arrêt : `Ctrl+C` puis `docker compose down` (les volumes `models/` et
`logs/` sont conservés — le modèle HF n'est pas re-téléchargé au prochain `up`).

> ⏱️ Le **1ᵉʳ démarrage** prend 3-5 min de build + 1-3 min de download du
> modèle CamemBERT (~270 Mo). Les démarrages suivants sont < 30 s grâce au
> cache volume `models/`.

---

## Modèle utilisé

**`cmarkea/distilcamembert-base-sentiment`** — DistilCamemBERT FR,
68 M paramètres, ~270 Mo.

⚠️ Le modèle sort **5 étoiles** (`'1 star'` … `'5 stars'`). Le métier
(Aubergine Hôtels) veut **3 classes** (`négatif/neutre/positif`).

→ Tu dois implémenter le **mapping 5★ → 3 classes** dans
`services/api-nlp/app/inference.py`. C'est le geste cœur de ce brief
(adaptation d'un service au format métier).

---

## Endpoints fournis

| Endpoint | Statut au clone | Ce que tu dois faire |
|---|---|---|
| `GET /health` | ✅ fonctionnel | rien |
| `GET /info` | ✅ fonctionnel | rien |
| `POST /predict` | ❌ 501 Not Implemented | implémenter (avec mapping 5→3) |

L'UI Streamlit est lancée mais affiche **« API non branchée »** tant que tu
n'as pas branché l'appel HTTP dans `services/ui-streamlit/app.py`.

---

## Structure

```
.
├── docker-compose.yml             ← 2 services + healthcheck api-nlp
├── .env.example
├── services/
│   ├── api-nlp/                   ← FastAPI + transformers
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py            ← routes (lifespan + /health + /info + /predict)
│   │   │   ├── schemas.py         ← Pydantic ReviewIn / SentimentOut
│   │   │   └── inference.py       ← TON CODE + mapping 5→3
│   │   └── tests/
│   │       └── test_health.py     ← 1 test pytest qui passe
│   └── ui-streamlit/              ← UI utilisateur
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app.py                 ← UI à compléter
├── data/
│   └── sample_reviews.csv         ← 30 reviews FR fictives (Aubergine Hôtels)
└── postman/
    └── M0-B2_collection.json      ← à compléter
```

---

## Healthcheck

Le `docker-compose.yml` inclut un `healthcheck` sur `api-nlp`. Au bout de
~40 s (le temps que le modèle se charge), le service passe `healthy`.
Vérification :

```bash
docker compose ps
# m0b2-api-nlp        Up X seconds (healthy)
```

Si le service reste `unhealthy` au bout de 2 min, regarde les logs :
`docker compose logs api-nlp`.

---

## Tests

Lance les tests **dans le conteneur API** :

```bash
docker compose exec api-nlp pytest -v
```

Au clone, 1 test passe (`test_health.py`). À toi d'ajouter au moins
2 tests pour `/predict`.

---

## Variables d'environnement (`.env`)

| Variable | Défaut | Usage |
|---|---|---|
| `MODEL_NAME_HF` | `cmarkea/distilcamembert-base-sentiment` | Modèle HF à charger |
| `MAX_TEXT_LENGTH` | `2000` | Validation Pydantic (longueur max texte) |

---

## Débugging rapide

| Symptôme | À tenter |
|---|---|
| `docker compose up` reste bloqué sur `pulling/building` | 1ᵉʳ build = 3-5 min + 1-3 min download modèle, patiente |
| `/predict` renvoie toujours 501 | Tu n'as pas encore complété `inference.py`, c'est normal |
| `/predict` renvoie `"1 star"` au lieu de `"négatif"` | Mapping 5→3 pas implémenté |
| L'UI affiche « API non branchée » | Tu dois compléter `app.py` dans `services/ui-streamlit/` |
| `Connection refused` depuis l'UI | Vérifie que l'URL est `http://api-nlp:8000` (nom de service docker), pas `localhost` |
| `ModuleNotFoundError` | Rebuild : `docker compose build --no-cache api-nlp` |
| Service `unhealthy` | `docker compose logs api-nlp` — le modèle ne se charge probablement pas (réseau, mémoire) |

Logs en temps réel : `docker compose logs -f api-nlp`.