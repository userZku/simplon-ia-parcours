# 🤖 Parcours IA — Simplon

**Auteur :** Théo Capitaine (@userZku)  
**Démarrage :** Mai 2026

Parcours de formation complet en Intelligence Artificielle couvrant les fondamentaux jusqu'aux applications en production : du ML basique à l'orchestration multi-services en conteneurs.

---

## 📋 Table des matières

- [Module 00 — Fondamentaux ML & Intégration](#module-00-fondamentaux-ml-intégration)
  - [M0-B1 — FastIA : API de Prédiction](#m0-b1-fastia-api-de-prédiction)
  - [M0-B2 — NLP Multi-Services](#m0-b2-nlp-multi-services)
- [Autres Modules](#autres-modules)
- [Installation Rapide](#installation-rapide)
- [Structure du Repo](#structure-du-repo)
- [CI/CD](#cicd)
- [Notes](#notes)

---

## 🎯 Module 00 — Fondamentaux ML & Intégration

Le module 00 couvre l'intégration d'un modèle ML pré-entraîné dans une API REST, en passant par la conteneurisation et les logs structurés.

### M0-B1 — FastIA : API de Prédiction

**Objectif :** Exposer un modèle scikit-learn via une API FastAPI en production.

#### 📁 Contenu

- **Modèle :** Classification de criticité (maintenance prédictive) — 3 classes : basse, moyenne, haute
- **Dataset :** 6 500 lignes synthétiques (machine_id, type_machine, age, maintenance, température, vibration, pression, incidents)
- **Framework :** FastAPI + scikit-learn + Pydantic
- **Endpoints :**
  - `GET /health` : santé du service + état du modèle
  - `POST /predict` : prédiction de criticité d'une machine (input JSON → criticite + probabilités)

#### 🛠️ Tech Stack

- **API :** FastAPI 0.115+
- **Serveur :** Uvicorn 0.32+
- **ML :** scikit-learn 1.7+, joblib, pandas, numpy
- **Tests :** pytest 8+, httpx
- **Logs :** Loguru (fichier + console, rotation 5 MB, 7 jours rétention)
- **Container :** Docker (image < 780 MB, non-root, healthcheck)

#### ✅ Compétences Acquises

- Charger un modèle pré-entraîné au démarrage (lifespan FastAPI)
- Implémenter une validation Pydantic stricte
- Logger structuré avec latence de prédiction
- Dockerfile optimisé + .dockerignore
- Tests pytest avec fixtures, paramétrisation, assertions sur schéma
- CI/CD GitHub Actions (pytest sur push/PR)

#### 📖 Resources

- `squelette/` : code de démarrage + modèle pré-entraîné
- `ressources/01_FastAPI_essentiel.md` : mini-cours FastAPI
- `ressources/02_Docker_essentiel.md` : mini-cours Docker
- `ressources/03_Loguru_essentiel.md` : mini-cours Loguru
- `ressources/04_Pytest_API_essentiel.md` : mini-cours pytest

#### 🚀 Quick Start (M0-B1)

```bash
cd module-00/M0-B1/squelette
python -m venv .venv
source .venv/bin/activate  # ou .\.venv\Scripts\Activate.ps1 (Windows)
pip install -r requirements.txt
uvicorn app.main:app --reload  # API démarre sur http://localhost:8000
pytest -q                       # Lancer les tests
```

Accès Swagger : http://localhost:8000/docs

#### 🐳 Docker

```bash
cd module-00/M0-B1/squelette
docker build -t fastia-maintenance:dev .
docker run --rm -p 8000:8000 fastia-maintenance:dev
curl http://localhost:8000/health
```

---

### M0-B2 — NLP Multi-Services

*(À compléter demain)*

---

## 🔄 Autres Modules

| Module | Sujet | Statut |
|--------|-------|--------|
| M1-xx  | ... | 🟡 À venir |
| M2-xx  | ... | 🟡 À venir |
| ...    | ... | 🟡 À venir |

---

## 💾 Installation Rapide

**Pré-requis globaux :**
- Python 3.11+
- Docker 24+ (pour la partie conteneurs)
- Git

**Par module :**
Chaque module possède son propre `squelette/` avec :
- `.venv/` (env virtuel local)
- `requirements.txt` (dépendances figées)
- `README.md` (instructions spécifiques)

---

## � Structure du Repo

```
simplon-ia-parcours/
├── README.md                          ← (ce fichier)
├── .github/
│   └── workflows/
│       ├── _python-pytest-reusable.yml
│       └── pytest-m0-b1.yml
├── module-00/
│   ├── M0-B1/
│   │   ├── ressources/
│   │   │   ├── 01_FastAPI_essentiel.md
│   │   │   ├── 02_Docker_essentiel.md
│   │   │   ├── 03_Loguru_essentiel.md
│   │   │   ├── 04_Pytest_API_essentiel.md
│   │   │   └── liens_officiels.md
│   │   └── squelette/
│   │       ├── .venv/
│   │       ├── app/
│   │       ├── model/
│   │       ├── tests/
│   │       ├── logs/ (généré à l'exécution)
│   │       ├── Dockerfile
│   │       ├── .dockerignore
│   │       ├── requirements.txt
│   │       └── README.md
│   └── M0-B2/
│       ├── ressources/
│       └── squelette/
└── module-01/ ... (à venir)
```

---

## �🔗 CI/CD

- **GitHub Actions :** Workflows pytest par module (déclenchement filtré par chemin)
- **M0-B1 :** ✅ Actif — lancer sur tout changement dans `module-00/M0-B1/squelette/**`
- **M0-B2 :** 🟡 Désactivé temporairement (tests en cours)

---

## 📝 Notes

- Chaque module est **indépendant** avec ses dépendances propres
- Les ressources (mini-cours) sont liées au brief but peuvent servir à d'autres modules
- Le parcours est progressif : fondamentaux → intégration → production → orchestration

---
