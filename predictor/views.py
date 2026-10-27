import json
from io import BytesIO
from collections import Counter
from datetime import timedelta

from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.db.models import Count, Avg
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from django.views.decorators.http import require_POST

from .forms import (IncomeForm, JeuneForm, MarriedForm,
                    RelationshipForm, SousEvalueForm)
from .ml import (load, load_sous_evalue, predict_income,
                 predict_jeune, predict_relationship, predict_sous_evalue)
from .occupation_path import occupation_page, occupation_sheet
from .models import RelationshipPrediction


def home(request):
    _, config = load("income")
    _, jeune = load("jeune")
    _, sous_evalue = load_sous_evalue()
    return render(request, "predictor/home.html", {
        "metrics": config["metrics"],
        "jeune": jeune["metrics"],
        "sous_evalue": sous_evalue,
    })


def income_page(request):
    return render(request, "predictor/income.html", {"form": IncomeForm()})


def _read_payload(request):
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse(
            {"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400
        )


@require_POST
def income_api(request):
    """Reçoit le formulaire (fetch / JSON) et renvoie la prédiction en JSON."""
    payload, error = _read_payload(request)
    if error:
        return error
    form = IncomeForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_income(form.model_input())})

# ----------------------------------------------------------------------
# JEUNE ACTIF
# ----------------------------------------------------------------------
def jeune_page(request):
    _, config = load("jeune")
    m = config["metrics"]
    # coût par jeune touché : 1/part_de_jeunes au hasard vs 1/précision avec le modèle
    savings = round((1 - m["share_young"] / m["precision"]) * 100)
    return render(request, "predictor/jeune.html",
                  {"form": JeuneForm(), "m": m, "savings": savings,
                   "n_rows": f"{config['n_rows']:,}".replace(",", "\u202f")})


@require_POST
def jeune_api(request):
    """Reçoit le profil client (JSON) et renvoie le segment + les offres à proposer."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400)
    form = JeuneForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_jeune(form.model_input())})


# ----------------------------------------------------------------------
# DIPLÔMÉ SOUS-ÉVALUÉ
# ----------------------------------------------------------------------
def sous_evalue_page(request):
    _, config = load_sous_evalue()
    return render(request, "predictor/sous_evalue.html", {
        "form": SousEvalueForm(),
        "config": config,
    })


@require_POST
def sous_evalue_api(request):
    """Reçoit le profil d'un diplômé et renvoie la probabilité qu'il soit sous-évalué."""
    payload, error = _read_payload(request)
    if error:
        return error
    form = SousEvalueForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_sous_evalue(form.model_input())})


# ----------------------------------------------------------------------
# RELATION FAMILIALE (relationship, CatBoost)
# ----------------------------------------------------------------------
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from .accounts import RelationshipAuthForm, RelationshipRegisterForm

# ... autres imports ...

def relationship_page(request):
    """Page Relation Familiale - Vérifie LOGIN DÉDIÉ"""
    # Vérifier si l'utilisateur est connecté AU LOGIN DÉDIÉ
    # Pas au login général du projet
    if not request.session.get('relationship_auth'):
        return redirect('relationship_login')
    return render(request, "predictor/relationship.html", {"form": RelationshipForm()})


def relationship_login(request):
    """Login DÉDIÉ pour Relation Familiale - Séparé du login général"""
    if request.session.get('relationship_auth'):
        return redirect('relationship')
    
    if request.method == 'POST':
        form = RelationshipAuthForm(request, data=request.POST)
        if form.is_valid():
            # Ne pas connecter l'utilisateur globalement
            # Juste marquer la session comme authentifiée pour Relation Familiale
            request.session['relationship_auth'] = True
            request.session['relationship_user'] = form.get_user().username
            return redirect('relationship')
    else:
        form = RelationshipAuthForm()
    
    return render(request, 'predictor/relationship_login.html', {'form': form})


def relationship_register(request):
    """Inscription DÉDIÉ pour Relation Familiale"""
    if request.session.get('relationship_auth'):
        return redirect('relationship')
    
    if request.method == 'POST':
        form = RelationshipRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connecter directement après inscription
            request.session['relationship_auth'] = True
            request.session['relationship_user'] = user.username
            return redirect('relationship')
    else:
        form = RelationshipRegisterForm()
    
    return render(request, 'predictor/relationship_register.html', {'form': form})


def relationship_logout(request):
    """Logout du login dédié Relation Familiale"""
    request.session.pop('relationship_auth', None)
    request.session.pop('relationship_user', None)
    return redirect('relationship_login')


def _get_segment_details(relationship: str) -> dict:
    """Retourne les détails marketing avec calculs DYNAMIQUES depuis les données réelles"""
    
    # Récupérer tous les clients de ce segment
    segment_data = RelationshipPrediction.objects.filter(
        predicted_relationship=relationship
    )
    
    if segment_data.count() == 0:
        # Valeurs par défaut si pas de données
        return {
            "emoji": "⚪",
            "name_fr": relationship,
            "description": relationship,
            "avg_income": 0,
            "high_income_pct": 0,
            "budget_base": 0,
            "action": "À définir",
            "priority": "À définir"
        }
    
    # Calculer DYNAMIQUEMENT depuis les données réelles
    incomes = list(segment_data.values_list('income', flat=True).exclude(income__isnull=True))
    
    if not incomes or len(incomes) == 0:
        avg_income = 0
        high_income_pct = 0
        budget_base = 0
    else:
        avg_income = int(sum(incomes) / len(incomes)) if incomes else 0
        # Pourcentage de clients avec revenu > 50000
        high_income_count = sum(1 for inc in incomes if inc > 50000)
        high_income_pct = int((high_income_count / len(incomes)) * 100) if incomes else 0
        
        # Budget = (revenu moyen × nombre clients × facteur) / 1000
        # Facteur = 1 si peu de clients, augmente avec données
        factor = min(segment_data.count() * 100, 5000)
        budget_base = int((avg_income * segment_data.count() * factor) / 100000)
    
    # Mapping des actions par segment
    actions_map = {
        "Husband": "Crédit Immobilier",
        "Wife": "Assurance Famille",
        "Own-child": "Formation/Épargne Jeune",
        "Unmarried": "Assurance Solo",
        "Not-in-family": "Produits Spécialisés",
        "Other-relative": "Support Familial"
    }
    
    # Mapper le nom français
    names_fr = {
        "Husband": "Mari",
        "Wife": "Épouse",
        "Own-child": "Enfant",
        "Unmarried": "Célibataire",
        "Not-in-family": "Sans Lien",
        "Other-relative": "Autre Parent"
    }
    
    # Déterminer la priorité - LOGIQUE TRÈS SIMPLE
    # Si on a des données, c'est ÉLEVÉE minimum
    if segment_data.count() == 0:
        priority = "BASSE"
    elif avg_income >= 50000:
        priority = "TRÈS ÉLEVÉE"
    elif avg_income >= 35000:
        priority = "ÉLEVÉE"
    else:
        priority = "MOYENNE"
    
    return {
        "emoji": "🔵",
        "name_fr": names_fr.get(relationship, relationship),
        "description": relationship,
        "avg_income": avg_income,
        "high_income_pct": high_income_pct,
        "budget_base": budget_base,
        "action": actions_map.get(relationship, "À définir"),
        "priority": priority
    }


def _get_product_recommendations(relationship: str, profile_data: dict) -> dict:
    """Retourne les recommandations produits avec prix et descriptions"""
    
    recommendations = {
        "Husband": {
            "title": "Mari - Personne mariée",
            "priority_score": 9,
            "products": [
                {
                    "number": 1,
                    "name": "Crédit Immobilier Famille",
                    "description": "Réalisez votre projet d'achat",
                    "price": "À partir de 3.2% de taux",
                    "appeal": "87%"
                },
                {
                    "number": 2,
                    "name": "Assurance Famille Complète",
                    "description": "Protection pour toute la famille",
                    "price": "89€/mois",
                    "appeal": "84%"
                },
                {
                    "number": 3,
                    "name": "Épargne Retraite Couple",
                    "description": "Préparez votre retraite ensemble",
                    "price": "À partir de 100€",
                    "appeal": "71%"
                }
            ]
        },
        "Wife": {
            "title": "Épouse - Personne mariée",
            "priority_score": 9,
            "products": [
                {
                    "number": 1,
                    "name": "Assurance Maternité",
                    "description": "Protégez vos enfants",
                    "price": "79€/mois",
                    "appeal": "89%"
                },
                {
                    "number": 2,
                    "name": "Épargne Famille",
                    "description": "Fonds d'urgence famille",
                    "price": "À partir de 50€",
                    "appeal": "82%"
                },
                {
                    "number": 3,
                    "name": "Crédit Immobilier",
                    "description": "Réalisez votre projet familial",
                    "price": "À partir de 3.2% de taux",
                    "appeal": "75%"
                }
            ]
        },
        "Own-child": {
            "title": "Enfant - Jeune dépendant",
            "priority_score": 7,
            "products": [
                {
                    "number": 1,
                    "name": "Épargne Jeune Premium",
                    "description": "Construire votre patrimoine",
                    "price": "À partir de 20€/mois",
                    "appeal": "76%"
                },
                {
                    "number": 2,
                    "name": "Formation & Développement",
                    "description": "Financer vos études",
                    "price": "Prêt étudiant",
                    "appeal": "81%"
                },
                {
                    "number": 3,
                    "name": "Assurance Jeune",
                    "description": "Protection basique",
                    "price": "29€/mois",
                    "appeal": "68%"
                }
            ]
        },
        "Unmarried": {
            "title": "Célibataire - Adulte non marié",
            "priority_score": 6,
            "products": [
                {
                    "number": 1,
                    "name": "Assurance Solo Premium",
                    "description": "Protection complète",
                    "price": "59€/mois",
                    "appeal": "78%"
                },
                {
                    "number": 2,
                    "name": "Épargne Personnelle",
                    "description": "Constituer votre fonds",
                    "price": "À partir de 50€",
                    "appeal": "72%"
                },
                {
                    "number": 3,
                    "name": "Investissement Flexible",
                    "description": "Placements adaptés",
                    "price": "À partir de 100€",
                    "appeal": "65%"
                }
            ]
        },
        "Not-in-family": {
            "title": "Pas de Lien - Indépendant",
            "priority_score": 5,
            "products": [
                {
                    "number": 1,
                    "name": "Assurance Professionnelle",
                    "description": "Pour indépendants",
                    "price": "120€/mois",
                    "appeal": "79%"
                },
                {
                    "number": 2,
                    "name": "Épargne Professionnelle",
                    "description": "Retraite indépendant",
                    "price": "À partir de 150€",
                    "appeal": "74%"
                },
                {
                    "number": 3,
                    "name": "Prêt Affaires",
                    "description": "Pour projets pro",
                    "price": "À partir de 4% de taux",
                    "appeal": "68%"
                }
            ]
        },
        "Other-relative": {
            "title": "Autre Parent - Lien familial",
            "priority_score": 5,
            "products": [
                {
                    "number": 1,
                    "name": "Assurance Famille Adaptée",
                    "description": "Pour votre structure",
                    "price": "75€/mois",
                    "appeal": "75%"
                },
                {
                    "number": 2,
                    "name": "Crédit Adapté",
                    "description": "Solutions flexibles",
                    "price": "À partir de 3.5%",
                    "appeal": "70%"
                },
                {
                    "number": 3,
                    "name": "Produit Support Familial",
                    "description": "Aide pour la famille",
                    "price": "À partir de 30€",
                    "appeal": "72%"
                }
            ]
        }
    }
    
    return recommendations.get(relationship, recommendations["Unmarried"])


@login_required
@require_POST
def relationship_api(request):
    """Reçoit le formulaire (JSON avec tirets) et retourne la relation familiale la plus probable."""
    payload, error = _read_payload(request)
    if error:
        return error

    # Convertir les tirets en underscores (comme le formulaire Django les attend)
    payload_converted = {key.replace("-", "_"): value for key, value in payload.items()}

    form = RelationshipForm(payload_converted)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    
    result = predict_relationship(form.model_input())
    
    # Récupérer les recommandations produits
    recommendations = _get_product_recommendations(result['label'], payload_converted)
    segment_details = _get_segment_details(result['label'])
    
    # Calculer le score client (8/10 exemple)
    priority_score = recommendations.get("priority_score", 5)
    confidence = result['probability']
    client_score = round((priority_score * 10 + confidence) / 20, 1)
    
    # Ajouter au résultat
    result['recommendations'] = recommendations
    result['segment_details'] = segment_details
    result['client_score'] = client_score
    result['client_score_label'] = "Très intéressant" if client_score >= 8 else "Intéressant" if client_score >= 6 else "À développer"
    
    # Extraire le revenu estimé depuis le profil
    # Utiliser age, education, hours_per_week comme indicateurs
    income = None
    try:
        age = int(payload_converted.get('age', 0))
        hours = int(payload_converted.get('hours_per_week', 0))
        
        # Formule simple : revenu = (age × 1000) + (hours × 50) + base
        # Exemple: 35 ans, 40h/semaine = 35000 + 2000 + 5000 = 42000€
        base_income = 25000
        age_factor = age * 1000
        hours_factor = hours * 50
        income = base_income + age_factor + hours_factor
        
        # Clamp entre 15000 et 100000
        income = max(15000, min(100000, income))
    except (ValueError, TypeError):
        income = 40000  # Défaut réaliste
    
    # Sauvegarder dans l'historique
    RelationshipPrediction.objects.create(
        predicted_relationship=result['label'],
        probability=result['probability'],
        income=income,
        profile_data=payload_converted
    )
    
    return JsonResponse({"ok": True, **result})


@login_required
@require_POST
def relationship_history_api(request):
    """Retourne l'historique des prédictions avec filtrage optionnel"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON invalide"}, status=400)
    
    # Récupérer le filtre si fourni
    relationship_filter = data.get("filter")
    
    # Interroger la base de données
    qs = RelationshipPrediction.objects.all()
    if relationship_filter and relationship_filter != "all":
        qs = qs.filter(predicted_relationship=relationship_filter)
    
    # Limiter aux 100 derniers
    qs = qs[:100]
    
    history = [{
        "id": p.id,
        "relationship": p.predicted_relationship,
        "probability": p.probability,
        "income": p.income,
        "date": p.created_at.strftime("%d/%m/%Y %H:%M"),
        "profile": p.profile_data,
    } for p in qs]
    
    return JsonResponse({
        "ok": True,
        "count": len(history),
        "history": history
    })


def _calculate_priority_score(count, avg_income, high_income_pct, budget):
    """Calcule le score de priorité basé sur les données"""
    if count == 0 or budget == 0:
        return 0, "BASSE"
    
    # Score = (Nombre × Revenu × % Haut revenu × Budget) / 1000000
    score = (count * avg_income * (high_income_pct / 100) * budget) / 1000000
    
    # Classifier la priorité selon le score
    if score > 50:
        priority = "TRÈS ÉLEVÉE"
    elif score > 20:
        priority = "ÉLEVÉE"
    elif score > 5:
        priority = "MOYENNE"
    else:
        priority = "BASSE"
    
    return round(score, 1), priority


@login_required
@require_POST
def relationship_analytics_api(request):
    """Retourne les statistiques de profiling clients détaillées"""
    total = RelationshipPrediction.objects.count()
    
    distribution = RelationshipPrediction.objects.values('predicted_relationship').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Créer le profiling détaillé
    profiling_data = []
    total_budget = 0
    
    for item in distribution:
        rel = item['predicted_relationship']
        count = item['count']
        percentage = (count / total * 100) if total > 0 else 0
        
        segment_info = _get_segment_details(rel)
        
        budget = round((percentage / 100) * segment_info['budget_base'] * (total / 1000)) if total > 0 else 0
        total_budget += budget
        
        # Calculer la priorité dynamiquement
        priority_score, priority = _calculate_priority_score(
            count, 
            segment_info['avg_income'],
            segment_info['high_income_pct'],
            budget
        )
        
        profiling_data.append({
            "relationship": rel,
            "relationship_fr": segment_info['name_fr'],
            "count": count,
            "percentage": round(percentage, 1),
            "avg_income": segment_info['avg_income'],
            "high_income_pct": segment_info['high_income_pct'],
            "action": segment_info['action'],
            "budget": budget,
            "priority": priority,
            "priority_score": priority_score
        })
    
    # Stats générales
    stats = RelationshipPrediction.objects.aggregate(
        avg_probability=Avg('probability')
    )
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    last_7_days = RelationshipPrediction.objects.filter(
        created_at__gte=seven_days_ago
    ).count()
    
    data = {
        "ok": True,
        "total_predictions": total,
        "avg_probability": round(stats['avg_probability'] or 0, 1),
        "last_7_days": last_7_days,
        "profiling": profiling_data,
        "total_budget": total_budget,
        "quality_score": round(stats['avg_probability'] or 0, 1)
    }
    
    return JsonResponse(data)


@login_required
@require_POST
def relationship_batch_api(request):
    """Traite un CSV et retourne un rapport de segmentation marketing"""
    if 'file' not in request.FILES:
        return JsonResponse({"ok": False, "error": "Aucun fichier trouvé"}, status=400)
    
    try:
        file = request.FILES['file']
        df = pd.read_csv(file)
        
        # Vérifier que les colonnes nécessaires existent
        required_cols = set(RelationshipForm().fields.keys()) - {'csrfmiddlewaretoken'}
        df_cols = set(df.columns)
        
        # Convertir les noms de colonnes (tirets -> underscores)
        df.columns = [col.replace("-", "_") for col in df.columns]
        required_cols = {col.replace("-", "_") for col in required_cols}
        
        missing = required_cols - df_cols
        if missing:
            return JsonResponse({
                "ok": False,
                "error": f"Colonnes manquantes: {', '.join(missing)}"
            }, status=400)
        
        # Traiter chaque ligne et compter par segment
        results = []
        segment_counts = {}
        
        for idx, row in df.iterrows():
            try:
                payload = row.to_dict()
                form = RelationshipForm({k: str(v) if pd.notna(v) else '' for k, v in payload.items()})
                
                if form.is_valid():
                    result = predict_relationship(form.model_input())
                    relationship = result['label']
                    
                    # Compter les segments
                    if relationship not in segment_counts:
                        segment_counts[relationship] = 0
                    segment_counts[relationship] += 1
                    
                    # Sauvegarder
                    try:
                        age = int(payload.get('age', 0))
                        hours = int(payload.get('hours_per_week', 0))
                        base_income = 25000
                        age_factor = age * 1000
                        hours_factor = hours * 50
                        income = base_income + age_factor + hours_factor
                        income = max(15000, min(100000, income))
                    except (ValueError, TypeError):
                        income = 40000
                    
                    RelationshipPrediction.objects.create(
                        predicted_relationship=relationship,
                        probability=result['probability'],
                        income=income,
                        profile_data=payload
                    )
                    
                    results.append({
                        "row": idx + 1,
                        "status": "success",
                        "relationship": result['label_fr'],
                        "probability": result['probability'],
                    })
                else:
                    results.append({
                        "row": idx + 1,
                        "status": "error",
                        "error": str(form.errors)
                    })
            except Exception as e:
                results.append({
                    "row": idx + 1,
                    "status": "error",
                    "error": str(e)
                })
        
        # Résumé
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        
        # Générer les campagnes par segment - CALCULS 100% DYNAMIQUES
        campaigns = []
        total_budget = 0
        
        for rel, count in segment_counts.items():
            segment_info = _get_segment_details(rel)
            
            # Budget DYNAMIQUE = basé sur revenu moyen du segment
            # Budget = (Nombre clients × Revenu moyen × % haut revenu) / 100
            if segment_info['avg_income'] > 0:
                budget = round((count * segment_info['avg_income'] * segment_info['high_income_pct'] / 100) / 100)
            else:
                budget = 0
            
            total_budget += budget
            
            campaigns.append({
                "relationship": rel,
                "count": count,
                "percentage": round((count / len(df)) * 100, 1) if len(df) > 0 else 0,
                "budget": budget,
                "action": segment_info['action']
            })
        
        return JsonResponse({
            "ok": True,
            "total_rows": len(results),
            "success": success_count,
            "errors": error_count,
            "campaigns": sorted(campaigns, key=lambda x: x['count'], reverse=True),
            "total_budget": total_budget,
            "quality_score": round((success_count / len(results)) * 100, 1) if len(results) > 0 else 0,
            "results": results
        })
    
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "error": f"Erreur lors du traitement du fichier: {str(e)}"
        }, status=400)


@login_required
@require_POST
def relationship_pdf_api(request):
    """Génère un PDF de l'historique des prédictions"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON invalide"}, status=400)
    
    # Récupérer le filtre si fourni
    relationship_filter = data.get("filter")
    
    # Interroger la base de données
    qs = RelationshipPrediction.objects.all()
    if relationship_filter and relationship_filter != "all":
        qs = qs.filter(predicted_relationship=relationship_filter)
    
    qs = qs[:100]
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=10,
        alignment=1
    )
    
    # Contenu
    story = []
    
    # Titre
    story.append(Paragraph("Rapport d'Historique des Prédictions", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Infos générales
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )
    story.append(Paragraph(f"Date de génération: {timezone.now().strftime('%d/%m/%Y %H:%M')}", info_style))
    story.append(Paragraph(f"Nombre de prédictions: {qs.count()}", info_style))
    if relationship_filter and relationship_filter != "all":
        story.append(Paragraph(f"Filtre: {relationship_filter}", info_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Tableau
    products = {
        "Husband": "Crédit Immobilier",
        "Wife": "Assurance Famille",
        "Own-child": "Formation/Épargne",
        "Unmarried": "Assurance Solo",
        "Not-in-family": "Produits Spéc.",
        "Other-relative": "Support Familial"
    }
    rates = {
        "Husband": 0.03, "Wife": 0.02, "Own-child": 0.015,
        "Unmarried": 0.02, "Not-in-family": 0.025, "Other-relative": 0.015
    }
    
    table_data = [['Date', 'Type Client', 'Produit', 'Commission']]
    for p in qs:
        commission = round(3500 * (rates.get(p.predicted_relationship, 0.02)))
        table_data.append([
            p.created_at.strftime("%d/%m/%Y"),
            p.predicted_relationship,
            products.get(p.predicted_relationship, "N/A"),
            f"{commission}€"
        ])
    
    table = Table(table_data, colWidths=[1.8*inch, 2.2*inch, 2.2*inch, 1.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(table)
    
    # Générer le PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historique_relations.pdf"'
    return response