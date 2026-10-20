#!/usr/bin/env python
"""
Script de test pour vérifier que l'application fonctionne correctement.
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).parent))

django.setup()

# Tests
from django.test import Client
from django.urls import reverse
import json

def test_homepage():
    """Test que la page d'accueil se charge"""
    print("Test 1: Chargement de la page d'accueil...")
    client = Client()
    response = client.get('/')
    
    if response.status_code == 200:
        print("✓ Page d'accueil chargée avec succès (status 200)")
        return True
    else:
        print(f"✗ Erreur: Status {response.status_code}")
        return False


def test_model_loading():
    """Test que le modèle se charge correctement"""
    print("\nTest 2: Vérification du chargement du modèle...")
    try:
        from predictor.views import model, schema
        print("✓ Modèle chargé avec succès")
        print(f"  - Colonnes du modèle: {len(schema['feature_columns'])}")
        print(f"  - Colonnes catégoriques: {len(schema['cat_cols'])}")
        print(f"  - Classes cibles: {schema.get('target', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ Erreur lors du chargement du modèle: {e}")
        return False


def test_prediction():
    """Test une prédiction simple"""
    print("\nTest 3: Test de prédiction...")
    client = Client()
    
    # Données de test
    test_data = {
        'age': '45',
        'workclass': 'Private',
        'fnlwgt': '215646',
        'education': 'Bachelors',
        'education-num': '13',
        'marital-status': 'Married-civ-spouse',
        'occupation': 'Exec-managerial',
        'race': 'White',
        'sex': 'Male',
        'capital-gain': '0',
        'capital-loss': '0',
        'hours-per-week': '40',
        'native-country': 'United-States',
        'income': '<=50K'
    }
    
    try:
        response = client.post('/predict/', test_data)
        
        if response.status_code == 200:
            data = json.loads(response.content)
            if 'error' in data:
                print(f"✗ Erreur de prédiction: {data['error']}")
                return False
            
            print("✓ Prédiction réussie")
            print(f"  - Relation prédite: {data['prediction']}")
            print(f"  - Confiance: {data['confidence']}%")
            print(f"  - Probabilités: {data['probabilities']}")
            return True
        else:
            print(f"✗ Status HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Erreur lors du test: {e}")
        return False


def test_static_files():
    """Test que les fichiers statiques sont accessibles"""
    print("\nTest 4: Vérification des fichiers statiques...")
    client = Client()
    
    files = [
        '/static/predictor/style.css',
        '/static/predictor/script.js',
    ]
    
    all_ok = True
    for file_path in files:
        response = client.get(file_path)
        if response.status_code == 200:
            print(f"✓ {file_path} trouvé")
        else:
            print(f"✗ {file_path} - Status {response.status_code}")
            all_ok = False
    
    return all_ok


def main():
    """Exécuter tous les tests"""
    print("=" * 60)
    print("Tests de l'application Django - Prédiction de Relation")
    print("=" * 60)
    
    results = []
    results.append(("Page d'accueil", test_homepage()))
    results.append(("Chargement du modèle", test_model_loading()))
    results.append(("Prédiction", test_prediction()))
    results.append(("Fichiers statiques", test_static_files()))
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSÉ" if result else "✗ ÉCHOUÉ"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n✓ Tous les tests sont passés ! L'application est prête.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
