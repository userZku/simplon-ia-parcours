# Expériences — M1-B1 Pyrenex Crédit (Lending Club)

> Trace tes runs au fur et à mesure. Format imposé : un bloc par run, avec
> date, modèle, hyperparams, métriques **test interne uniquement**, verdict.
> Commit à chaque run final (pas à chaque essai jetable).
>
> ⚠️ **Règle d'or — comparabilité.** Le holdout **n'apparaît jamais** dans les
> blocs `exp_NNN`. Il sort **une seule fois**, pour le modèle retenu, dans
> la section finale en bas de fichier. Cf. mini-cours 04.

---

## exp_001 — RF par défaut

- **Date** : 2026-06-08 08:58 UTC
- **Modèle** : RandomForestClassifier (sklearn 1.5.1)
- **Dataset** : lending_club_train.csv (sha256 d2da093bee40024b196e73a0d2d763193782f947e3d60552a3d7bbad0bd944e3), n=24000
- **Split** : test_size=0.2, stratify=y, random_state=42
- **Hyperparamètres** : tous par défaut, `n_jobs=-1`, `random_state=42`
- **Pré-traitement** : OneHotEncoder + StandardScaler (Pipeline scikit-learn)
- **Métriques (test interne)** :
  - F1 macro : 0.5131
  - F1 défaut : non mesuré dans ce run
  - ROC-AUC : 0.7170
  - Recall défaut : non mesuré dans ce run
- **Temps d'entraînement** : non mesuré dans ce run notebook/train.py
- **Verdict** : baseline de comparaison correcte mais performance insuffisante sur dataset drifté.

---

## exp_002 — RF balanced

- **Date** : 2026-06-08 08:58 UTC
- **Modèle** : RandomForestClassifier (sklearn 1.5.1)
- **Dataset** : lending_club_train.csv (sha256 d2da093bee40024b196e73a0d2d763193782f947e3d60552a3d7bbad0bd944e3), n=24000
- **Split** : test_size=0.2, stratify=y, random_state=42
- **Hyperparamètres** : `n_estimators=200`, `max_depth=10`, `min_samples_leaf=10`, `class_weight='balanced'`, `random_state=42`, `n_jobs=-1`
- **Pré-traitement** : OneHotEncoder + StandardScaler (Pipeline scikit-learn)
- **Métriques (test interne)** :
  - F1 macro : 0.6123
  - F1 défaut : non mesuré dans ce run
  - ROC-AUC : 0.7442
  - Recall défaut : non mesuré dans ce run
- **Temps d'entraînement** : non mesuré dans ce run notebook/train.py
- **Verdict** : meilleure config à ce stade (gain net vs défaut : +0.0992 F1 macro et +0.0272 ROC-AUC). Candidat retenu pour l'évaluation holdout (tâche 5).

---

## exp_003 — GradientBoosting + SHAP (gb_variant_a)

- **Date** : 2026-06-08
- **Modèle** : GradientBoostingClassifier (sklearn 1.5.1)
- **Dataset** : lending_club_train.csv (split interne)
- **Split** : test_size=0.2, stratify=y, random_state=42
- **Hyperparamètres** : `n_estimators=250`, `learning_rate=0.05`, `max_depth=3`, `subsample=0.8`, `random_state=42`
- **Pré-traitement** : `build_preprocessor()` depuis `src/preprocess.py`
- **Métriques (test interne)** :
  - F1 macro : 0.5207
  - F1 défaut : non mesuré dans ce run
  - ROC-AUC : 0.7430
  - Recall défaut : non mesuré dans ce run
- **Artefacts explicabilité** : `models/shap_bar_gb_variant_a.png`, `models/shap_summary_gb_variant_a.png`
- **Verdict** : meilleure explicabilité, mais performance inférieure à `exp_002` sur F1 macro (0.5207 vs 0.6123). Variante utile pour interprétation, non retenue comme meilleur modèle prédictif.

---

## 🏁 Évaluation finale sur holdout (modèle retenu)

> **À remplir une seule fois**, à la tâche 5 du brief, **après** avoir choisi
> ton modèle retenu parmi les `exp_NNN` ci-dessus. Le holdout n'est consulté
> qu'ici.

- **Date** : 2026-06-08
- **Expérience retenue** : exp_002 (RF balanced)
- **Modèle persisté** : `models/pyrenex_risk_v2.joblib`
- **Données holdout** : `data/lending_club_holdout.csv` (n=6000)
- **Métriques** :
  - F1 macro : 0.6123
  - F1 défaut : 0.4357
  - ROC-AUC : 0.7370
  - Recall défaut : 0.6455
- **Matrice de confusion** :

|  | Pred Fully Paid | Pred Charged Off |
|---|---|---|
| **Vrai Fully Paid** | 3444 | 1453 |
| **Vrai Charged Off** | 391 | 712 |

- **Comparaison baseline 2017** : gain fort sur la détection des défauts (recall défaut 0.6455 vs 0.05), avec davantage de faux positifs.