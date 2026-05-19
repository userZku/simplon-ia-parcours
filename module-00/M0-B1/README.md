# M0-B1 - Service IA de criticite maintenance (FastAPI)

## 1) Contexte

Ce module M0-B1 met en production un modele de classification scikit-learn via une API FastAPI.

Objectif: exposer une prediction de criticite machine, la tester, la journaliser et la conteneuriser.

Dossier de travail principal:
- `module-00/M0-B1/squelette`

---

## 2) Ce qui a été fait

### API
- Route `GET /health` operationnelle.
- Route `POST /predict` operationnelle:
  - validation Pydantic des entrees,
  - inference via modele `model/model.joblib`,
  - retour de la classe + probabilites.
- Route `POST /explain` operationnelle:
  - reutilise `/predict`,
  - interroge Ollama (`qwen2.5:1.5b`) pour produire une explication en francais.

### Chargement modele
- Chargement du modele au demarrage (lifespan FastAPI).
- Liberation de l'etat a l'arret du service.

### Logging
- Journalisation avec Loguru:
  - payload recu,
  - prediction et probabilites,
  - duree de traitement,
  - exceptions detaillees.
- Fichier de logs: `squelette/logs/api.log`.

### Tests
- Suite pytest executee: **10 tests passes**.
- Couverture fonctionnelle verifiee sur:
  - `/health`,
  - `/predict` (cas valides, cas invalides, parametrisation par type de machine).

### Docker
- `Dockerfile` present et complet:
  - image `python:3.11-slim`,
  - installation dependances,
  - utilisateur non-root,
  - `HEALTHCHECK` actif,
  - lancement uvicorn.

### CI GitHub (push M0-B1)
- Pipeline CI GitHub Actions configure pour M0-B1.
- Workflow principal: `.github/workflows/pytest-m0-b1.yml`.
- Le pipeline se declenche automatiquement sur:
  - push sur `main` si un fichier de `module-00/M0-B1/squelette/**` change,
  - push sur `main` si le workflow CI M0-B1 change,
  - pull request vers `main` avec les memes chemins surveilles.
- Le job utilise un workflow reusable: `.github/workflows/_python-pytest-reusable.yml`.
- Etapes executees en CI:
  - checkout du repository,
  - setup Python 3.11 + cache pip,
  - installation des dependances,
  - execution `pytest -q` dans `module-00/M0-B1/squelette`.

---

## 3) Etat de l'art

### Exposition de modele tabulaire
Pour un modele scikit-learn tabulaire, la stack retenue est :
- **FastAPI** pour l'API HTTP (performance, typing, docs Swagger),
- **Pydantic v2** pour la validation stricte,
- **joblib** pour charger le modele entraine,
- **pytest + htetpx/TestClient** pour tests API.

### Bonnes pratiques appliquees ici
- Chargement unique du modele au startup (evite le cout de reload par requete).
- Contrats de donnees explicites (schemas entree/sortie).
- Reponses predictives interpretable (classe + proba par classe).
- Logging structure orientee exploitation (latence, payload, erreurs).

### Observabilite et exploitation
- **Loguru** simplifie la journalisation applicative et la rotation fichier.
- Les traces permettent de suivre:
  - demarrage/arret,
  - temps de reponse,
  - etats d'erreur dependances (ex: Ollama indisponible).

### IA explicative locale
L'endpoint `/explain` permet de :
- combiner modele tabulaire predictif + LLM local pour explicabilite en langage naturel

Attention aux latences plus elevees que `/predict`.

### Conteneurisation
Le Dockerfile :
- image slim,
- execution non-root,
- healthcheck runtime,
- separation dependances / code pour le cache de build.

---

## 4) Sorties terminal

### 4.1 Lancement API
Commande:

```powershell
c:/.../module-00/M0-B1/squelette/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Extrait:

```text
INFO:     Started server process [24004]
INFO:     Waiting for application startup.
2026-05-19 15:42:42.159 | INFO | app.main:lifespan:80 - Chargement du modele depuis .../model/model.joblib
```

### 4.2 Requete GET /health
Commande:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8002/health' -Method Get
```

Sortie:

```json
{
  "status": "ok",
  "model_loaded": true
}
```

### 4.3 Requete POST /predict (valide)
Commande:

```powershell
$payload = @{ 
  type_machine='compresseur';
  age_machine_jours=1500;
  derniere_maintenance_jours=45;
  temperature_moyenne=68.5;
  vibration_moyenne=3.2;
  pression_moyenne=7.8;
  nb_incidents_3_mois=2
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:8002/predict' -Method Post -ContentType 'application/json' -Body $payload
```

Sortie:

```json
{
  "criticite": "basse",
  "probabilites": {
    "basse": 0.97,
    "haute": 0.0,
    "moyenne": 0.03
  }
}
```

### 4.4 Requete POST /predict (invalide -> 422)
Commande:

```powershell
$payload = @{ 
  type_machine='compresseur';
  age_machine_jours=1500;
  derniere_maintenance_jours=45;
  temperature_moyenne=68.5;
  vibration_moyenne=3.2;
  pression_moyenne=7.8;
  nb_incidents_3_mois=-1
} | ConvertTo-Json
```

Sortie:

```text
StatusCode: 422
{"detail":[{"type":"greater_than_equal","loc":["body","nb_incidents_3_mois"],"msg":"Input should be greater than or equal to 0","input":-1,"ctx":{"ge":0}}]}
```

### 4.5 Requete POST /explain
Commande:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8002/explain' -Method Post -ContentType 'application/json' -Body $payload
```

Sortie (extrait):

```json
{
  "criticite": "basse",
  "probabilites": {
    "basse": 0.97,
    "haute": 0.0,
    "moyenne": 0.03
  },
  "explication": "La machine de compresseur, âgée de 1500 jours et ayant reçu sa dernière maintenance il y a 45 jours, présente des caractéristiques normales avec une température moyenne de 68.5°C, une vibration moyenne de 3.2 et une pression moyenne de 7.8 bar. Bien que la machine ait subi deux incidents d'incidents dans les trois derniers mois, le taux de probabilité pour un incident élevé est très faible (0%). Cela signifie que malgré ces anomalies, l'état général de la machine reste stable et n'est pas critique.",
  "modele_llm": "qwen2.5:1.5b"
}
```

### 4.6 Tests
Commande:

```powershell
c:/.../module-00/M0-B1/squelette/.venv/Scripts/python.exe -m pytest -q
```

Sortie:

```text
..........                                                               [100%]
10 passed in 5.67s
```

---

## 5) Extrait de logs applicatifs

Fichier: `squelette/logs/api.log`

```text
2026-05-19 15:42:47.021 | INFO | app.main:lifespan:82 - Modele charge.
2026-05-19 15:43:05.437 | INFO | app.main:predict:139 - /predict - payload recu: {...}
2026-05-19 15:43:05.509 | INFO | app.main:predict:162 - /predict - prediction: basse | proba_basse=0.97 | proba_moyenne=0.03 | proba_haute=0.0 | duree: 65.26 ms
2026-05-19 15:44:05.553 | INFO | app.main:explain:185 - /explain - payload recu: {...}
2026-05-19 15:44:20.151 | INFO | app.main:explain:233 - /explain - prediction: basse | modele_llm: qwen2.5:1.5b | duree: 14597.15 ms
```

---

## 6) Lancer rapidement le projet

```powershell
cd module-00/M0-B1/squelette
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs interactive: http://127.0.0.1:8000/docs

---

## 7) Points d'attention

- Le endpoint `/explain` depend de Ollama local (port 11434).
- Si Ollama n'est pas disponible, `/explain` peut retourner une erreur de service dependant.
