import json
from pathlib import Path
import pandas as pd
from catboost import CatBoostClassifier
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Charger le modèle une seule fois au démarrage
MODEL_DIR = Path(settings.BASE_DIR) / "ml_models"
model = CatBoostClassifier()
model.load_model(str(MODEL_DIR / "relationship_model.cbm"))

# Charger le schéma
with open(MODEL_DIR / "relationship_schema.json", encoding="utf-8") as f:
    schema = json.load(f)


def home(request):
    """Affiche la page d'accueil avec le formulaire."""
    return render(request, "predictor/index.html")


@require_http_methods(["POST"])
def predict(request):
    """Reçoit les données du formulaire et retourne la prédiction."""
    try:
        # Récupérer les données du formulaire
        data = {}
        for col in schema["feature_columns"]:
            # Ignorer le champ 'relationship' - ce n'est pas une feature
            if col == "relationship":
                continue
            
            value = request.POST.get(col, "").strip()
            
            if value == "":
                return JsonResponse({
                    "error": f"Veuillez renseigner le champ : {col}"
                }, status=400)
            
            if col in schema["cat_cols"]:
                data[col] = value
            else:
                try:
                    data[col] = float(value)
                except ValueError:
                    return JsonResponse({
                        "error": f"Valeur numérique invalide pour : {col}"
                    }, status=400)
        
        # Créer un DataFrame avec les bonnes colonnes dans le bon ordre
        # Filtrer les colonnes pour exclure 'relationship'
        features_for_prediction = [col for col in schema["feature_columns"] if col != "relationship"]
        
        X_new = pd.DataFrame(
            [data],
            columns=features_for_prediction
        )
        
        # Convertir les colonnes catégoriques en string
        for col in schema["cat_cols"]:
            if col in X_new.columns:
                X_new[col] = X_new[col].astype(str)
        
        # Faire la prédiction
        prediction = model.predict(X_new)[0]
        probabilities = model.predict_proba(X_new)[0]
        
        # Obtenir le label de la cible
        target_name = prediction
        confidence = round(float(max(probabilities)) * 100, 2)
        
        return JsonResponse({
            "success": True,
            "prediction": str(target_name),
            "confidence": confidence,
            "probabilities": {
                "Husband": round(float(probabilities[0]) * 100, 2),
                "Not-in-family": round(float(probabilities[1]) * 100, 2),
                "Other-relative": round(float(probabilities[2]) * 100, 2),
                "Own-child": round(float(probabilities[3]) * 100, 2),
                "Unmarried": round(float(probabilities[4]) * 100, 2),
                "Wife": round(float(probabilities[5]) * 100, 2),
            }
        })
    
    except Exception as e:
        return JsonResponse({
            "error": f"Erreur lors de la prédiction : {str(e)}"
        }, status=500)
