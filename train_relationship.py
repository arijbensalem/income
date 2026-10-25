"""
Entraînement du modèle pour la cible RELATIONSHIP — utilise le modèle CatBoost pré-entraîné du dossier relation/.
Lancer :  python train_relationship.py
Produit : ml_models/relationship/relationship_model.cbm  +  ml_models/relationship/config.json
"""
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "relationship"
OUT.mkdir(parents=True, exist_ok=True)

# Copier le modèle et le schéma depuis le dossier relation/
relation_model = BASE / "relation" / "ml_models" / "relationship_model.cbm"
relation_schema = BASE / "relation" / "ml_models" / "relationship_schema.json"

if relation_model.exists():
    shutil.copy(relation_model, OUT / "pipeline.cbm")
    print(f"✓ Modèle copié : {OUT / 'pipeline.cbm'}")
else:
    print(f"✗ Erreur : {relation_model} introuvable")

if relation_schema.exists():
    schema = json.loads(relation_schema.read_text(encoding="utf-8"))
    # Garder le format du schéma pour la compatibilité
    (OUT / "config.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Schéma copié : {OUT / 'config.json'}")
else:
    print(f"✗ Erreur : {relation_schema} introuvable")

print(f"\nModèle relationship prêt dans {OUT}")
