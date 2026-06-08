# Verdict — Modèle de scoring Pyrenex Crédit v2

> Document destiné à Sophie Léger (Lead Data, Pyrenex Crédit).
> 1 page max.

## Contexte

Objectif du brief : décider si le modèle historique `pyrenex-risk-v1` doit être remplacé par un modèle réentraîné sur des données plus récentes, évalué proprement sur holdout intact.

## Démarche

Nous avons entraîné 3 configurations (`default`, `balanced`, `gb_variant_a`) sur `lending_club_train.csv` avec split interne stratifié (`test_size=0.2`, `random_state=42`) et preprocessing cohérent baseline. La config retenue est `balanced` (meilleur compromis performance/stabilité). L'évaluation finale a été réalisée une seule fois sur `lending_club_holdout.csv`.

## Verdict chiffré

| Métrique | Baseline 2017 (Pyrenex-risk-v1) | Modèle retenu (v2) | Variation |
|---|---|---|---|
| F1 macro (holdout) | 0.5018 | 0.6123 | +0.1105 |
| F1 défaut | 0.0860 | 0.4357 | +0.3497 |
| ROC-AUC | 0.7296 | 0.7370 | +0.0074 |
| Recall défaut | 0.0500 | 0.6455 | +0.5955 |

**Configuration retenue** : `RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=10, class_weight='balanced', random_state=42, n_jobs=-1)`.

## Trade-off explicité au métier

Le gain principal est la détection des défauts : le rappel défaut passe de 5% à 64.6%, ce qui réduit fortement le risque de laisser passer des mauvais payeurs. En contrepartie, la précision défaut reste modérée (~32.9%), donc le modèle génère plus de fausses alertes. Concrètement, Pyrenex capte bien plus de dossiers risqués, mais doit absorber plus de revues manuelles/refus discutables.

## Précautions avant mise en production

- Vérifier que le **schéma d'entrée** en production correspond exactement
  au schéma d'entraînement (cf. `pyrenex_risk_v2.json` → `feature_columns`)
- Re-évaluer le **seuil de décision** (0.5 par défaut) avec l'équipe
  métier — un seuil 0.3 peut être plus adapté selon l'appétence au risque
- Mettre en place un **monitoring** dès le déploiement (cf. M5/M6)
- Surveiller les **variables sensibles** identifiées (FICO, état US,
  revenu) — risque de disparate impact à auditer (M2/M7)
- Lancer un déploiement progressif (pilot/shadow mode) pour mesurer l'impact opérationnel réel avant généralisation.

## Recommandation

✅ **Remplacer Pyrenex-risk-v1 par v2**, car le v2 améliore nettement la détection du défaut (indicateur métier critique) tout en gardant un ROC-AUC au moins équivalent. À condition de calibrer le seuil de décision et de monitorer la dérive après mise en prod.

---

*Signé : Théo Capitaine, FastIA, le 2026-06-08*
