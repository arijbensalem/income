# Module « Ciblage premium » (cible income) — intégration

## 1. Copier les fichiers dans votre projet (même arborescence)
| Fichier | Action |
|---|---|
| `build_income_insights.py` | NOUVEAU, à la racine (à côté de `manage.py`) |
| `ml_models/income/config.json` | REMPLACE l'ancien (les anciennes clés sont conservées, une clé `pro` est ajoutée) |
| `ml_models/income/pipeline_fair.joblib` | NOUVEAU |
| `ml_models/income/background.csv` | NOUVEAU |
| `predictor/income_pro.py` | NOUVEAU |
| `predictor/views_income.py` | NOUVEAU |
| `predictor/offers_income.py` | NOUVEAU |
| `predictor/templates/predictor/_tech.html` | NOUVEAU (bloc « informations techniques » replié, inclus par income.html et ciblage.html) |
| `predictor/urls.py` | REMPLACE (seules 2 routes income changent + 3 routes ajoutées) |
| `predictor/templates/predictor/base.html` | REMPLACE (seul ajout : le bloc `head`, aucun lien dans le menu) |
| `predictor/templates/predictor/income.html` | REMPLACE |
| `predictor/templates/predictor/ciblage.html` | NOUVEAU |
| `predictor/static/predictor/income_pro.css` | NOUVEAU |

Aucun fichier de vos collègues (`views.py`, `forms.py`, `ml.py`, `style.css`, `home.html`…) n'est modifié.
Aucune nouvelle bibliothèque : `requirements.txt` ne change pas.

## 2. Lancer
```
python manage.py runserver
```
Pages : `/prediction-revenu/` (client unique) et `/ciblage-premium/` (portefeuille + simulateur).

## 3. Si vous changez de version de scikit-learn, régénérer le modèle équitable
```
python train_income.py
python build_income_insights.py
```

## 4. (Optionnel) carte sur l'accueil — à coller dans `home.html`, dans `<div class="model-grid">`
```html
    <a class="model" href="{% url 'ciblage' %}">
      <p class="eyebrow">Cible <code>income</code> · Banque &amp; assurance</p>
      <h3>Ciblage premium</h3>
      <p>Classe un portefeuille clients en Premium / Potentiel / Standard et simule la rentabilité d'une campagne.</p>
      <span class="go">Cibler mon portefeuille →</span>
    </a>
```
