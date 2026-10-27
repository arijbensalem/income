import hashlib
import html
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase
from django.urls import NoReverseMatch, reverse

from predictor.career_routes import build_direction, rank_families, score_families
from predictor.models import OccupationAccount
from predictor.occupation_auth import SESSION_KEY
from predictor.occupation_path import MODEL_FEATURES, PATH_KEY
from predictor.transformers import LABELS_FR


PIPELINE_SHA256 = "4a775d027167a459a66bee4ca005c3a1ab68fdd3a885bfe9ddec7c3ca5c2c157"
REPORT_SHA256 = "8e0d3822ad12a9abcf25d2e1f06845a2a2ef85b56f128d845c45f5611931e1c1"
DATASET_SHA256 = "4381848d760f7879de465dcb8ffc4820f995640063fa7e199a98eaed1e54c178"


def _page(response):
    return html.unescape(response.content.decode())


def _probabilities(data):
    classes = [
        {"label": "White-collar", "label_fr": "ancien", "probability": 58.0},
        {"label": "Blue-collar", "label_fr": "ancien", "probability": 27.0},
        {"label": "Service", "label_fr": "ancien", "probability": 15.0},
    ]
    return {
        "label": "White-collar",
        "label_fr": "ancien",
        "probability": 58.0,
        "classes": classes,
    }


def _profile(**overrides):
    payload = {
        "age": "34",
        "hours_per_week": "40",
        "education_num": "9",
        "capital_gain": "0",
        "capital_loss": "0",
        "workclass": "Private",
        "marital_status": "Never-married",
        "relationship": "Not-in-family",
        "sex": "Female",
        "race": "White",
        "native_country": "United-States",
        "income": "<=50K",
        "goal": "studies",
        "interests": ["craft", "machines"],
        "note": "Je cherche une voie technique.",
    }
    payload.update(overrides)
    return payload


class OccupationArtifactTests(SimpleTestCase):
    def test_production_model_report_and_dataset_are_unchanged(self):
        from django.conf import settings

        root = settings.BASE_DIR
        pipeline = hashlib.sha256((root / "ml_models" / "occupation" / "pipeline.joblib").read_bytes()).hexdigest()
        report = hashlib.sha256((root / "ml_models" / "occupation" / "holdout_evaluation_report.json").read_bytes()).hexdigest()
        dataset = hashlib.sha256((root / "data" / "adult_clean.csv").read_bytes()).hexdigest()
        self.assertEqual(pipeline, PIPELINE_SHA256)
        self.assertEqual(report, REPORT_SHA256)
        self.assertEqual(dataset, DATASET_SHA256)

    def test_interest_scoring_prefers_matching_families_over_model_top(self):
        shortlist = score_families("work", ["craft", "machines"], 9)
        self.assertEqual(shortlist[0], "Blue-collar")
        self.assertIn("Blue-collar", shortlist)

    def test_career_change_follows_interests_only(self):
        self.assertEqual(score_families("change", ["craft"], 13), ["Blue-collar"])
        ranked = rank_families("change", ["security", "craft"], 13)
        self.assertEqual([row["role"] for row in ranked], ["primary", "primary"])
        self.assertEqual([row["label"] for row in ranked], ["Blue-collar", "Service"])

    def test_goal_only_direction_stays_secondary(self):
        ranked = rank_families("work", ["craft"], 9)
        self.assertEqual(ranked[0]["role"], "primary")
        self.assertEqual(ranked[0]["label"], "Blue-collar")
        self.assertEqual([(row["label"], row["role"]) for row in ranked[1:]], [("Service", "secondary")])

    def test_examples_and_steps_follow_the_selected_interest(self):
        support = build_direction(
            "White-collar", "work", ["tech_support"], 13, "Licence (Bachelors)", 22,
            {"role": "primary", "interest_points": 2.0, "goal_points": 0.0},
        )
        self.assertEqual(support["examples"], ["Support technique"])
        self.assertIn("dépannage", " ".join(support["next_steps"]))
        self.assertNotIn("Vente", support["examples"])
        security = build_direction(
            "Service", "work", ["security"], 9, "Baccalauréat / HS-grad", 30,
            {"role": "primary", "interest_points": 2.0, "goal_points": 1.0},
        )
        steps = " ".join(security["next_steps"])
        self.assertIn("protection", steps)
        self.assertNotIn("Clarifier si vous visez", steps)
        self.assertEqual(security["examples"], ["Services de protection"])

    def test_education_label_and_age_change_the_training_text(self):
        licence = build_direction(
            "White-collar", "studies", ["office"], 13, "Licence (Bachelors)", 22,
            {"role": "primary", "interest_points": 2.0, "goal_points": 1.0},
        )
        doctorate = build_direction(
            "White-collar", "studies", ["office"], 16, "Doctorat", 22,
            {"role": "primary", "interest_points": 2.0, "goal_points": 1.0},
        )
        self.assertIn("Licence (Bachelors)", " ".join(licence["training"]))
        self.assertIn("Doctorat", " ".join(doctorate["training"]))
        self.assertNotEqual(licence["training"], doctorate["training"])
        young = build_direction(
            "Blue-collar", "studies", ["craft"], 9, "Baccalauréat / HS-grad", 18,
            {"role": "primary", "interest_points": 2.0, "goal_points": 0.5},
        )
        adult = build_direction(
            "Blue-collar", "studies", ["craft"], 9, "Baccalauréat / HS-grad", 34,
            {"role": "primary", "interest_points": 2.0, "goal_points": 0.5},
        )
        self.assertTrue(any("moins de 20 ans" in line for line in young["training"]))
        self.assertFalse(any("moins de 20 ans" in line for line in adult["training"]))


class OccupationPathTests(TestCase):
    def setUp(self):
        self.site_user = User.objects.create_user("site-user", password="site-secret-123")
        self.account = OccupationAccount(username="pro-user")
        self.account.set_password("pro-secret-123")
        self.account.save()
        session = self.client.session
        session[SESSION_KEY] = self.account.pk
        session.save()

    def test_site_login_alone_does_not_open_occupation(self):
        anonymous = Client()
        anonymous.force_login(self.site_user)
        blocked = anonymous.get(reverse("occupation"))
        self.assertEqual(blocked.status_code, 302)
        self.assertIn("/prediction-profession/connexion/", blocked.url)
        self.assertIn("next=", blocked.url)
        self.assertIn("prediction-profession", blocked.url)

    def test_anonymous_visitors_are_sent_to_occupation_login(self):
        anonymous = Client()
        explorer = anonymous.get(reverse("occupation"))
        sheet = anonymous.get(reverse("occupation_sheet"))
        self.assertEqual(explorer.status_code, 302)
        self.assertIn("/prediction-profession/connexion/", explorer.url)
        self.assertEqual(sheet.status_code, 302)
        self.assertIn("/prediction-profession/connexion/", sheet.url)
        login_page = anonymous.get(reverse("occupation_login"))
        self.assertEqual(login_page.status_code, 200)
        self.assertIn("Connexion profession", _page(login_page))
        self.assertIn("séparé", _page(login_page))
        register_page = anonymous.get(reverse("occupation_register"))
        self.assertEqual(register_page.status_code, 200)
        self.assertIn("Créer un compte profession", _page(register_page))
        self.assertEqual(anonymous.get(reverse("login")).status_code, 200)
        self.assertEqual(anonymous.get(reverse("register")).status_code, 200)
        income = anonymous.get(reverse("income"))
        self.assertEqual(income.status_code, 302)
        self.assertIn("/prediction-revenu/connexion/", income.url)

    def test_occupation_account_can_open_pages_until_occupation_logout(self):
        explorer = self.client.get(reverse("occupation"))
        self.assertEqual(explorer.status_code, 200)
        page = _page(explorer)
        self.assertIn("Trouver mon parcours", page)
        self.assertIn("Déconnexion profession (pro-user)", page)
        sheet = self.client.get(reverse("occupation_sheet"), follow=True)
        self.assertContains(sheet, "Aucune recommandation")
        self.client.post(reverse("occupation_logout"))
        after = self.client.get(reverse("occupation"))
        self.assertEqual(after.status_code, 302)
        self.assertIn("/prediction-profession/connexion/", after.url)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_register_and_login_create_a_separate_occupation_session(self):
        client = Client()
        client.force_login(self.site_user)
        created = client.post(reverse("occupation_register"), {
            "username": "nouveau-pro",
            "password1": "nouveau-secret-123",
            "password2": "nouveau-secret-123",
            "next": "/prediction-profession/",
        })
        self.assertEqual(created.status_code, 302)
        self.assertEqual(created.url, "/prediction-profession/")
        self.assertTrue(OccupationAccount.objects.filter(username="nouveau-pro").exists())
        self.assertIn(SESSION_KEY, client.session)
        self.assertEqual(client.get(reverse("occupation")).status_code, 200)

        other = Client()
        denied = other.post(reverse("occupation"), _profile())
        self.assertEqual(denied.status_code, 302)
        logged = other.post(reverse("occupation_login"), {
            "username": "nouveau-pro",
            "password": "nouveau-secret-123",
            "next": "/prediction-profession/",
        })
        self.assertEqual(logged.status_code, 302)
        self.assertEqual(other.get(reverse("occupation")).status_code, 200)

    def test_prediction_requires_occupation_login_and_csrf(self):
        anonymous = Client(enforce_csrf_checks=True)
        anonymous.get(reverse("occupation_login"))
        token = anonymous.cookies["csrftoken"].value
        blocked = anonymous.post(reverse("occupation"), {**_profile(), "csrfmiddlewaretoken": token})
        self.assertEqual(blocked.status_code, 302)
        self.assertIn("/prediction-profession/connexion/", blocked.url)

        signed_in = Client(enforce_csrf_checks=True)
        session = signed_in.session
        session[SESSION_KEY] = self.account.pk
        session.save()
        signed_in.get(reverse("occupation"))
        missing = signed_in.post(reverse("occupation"), _profile())
        self.assertEqual(missing.status_code, 403)

    def test_recommendation_uses_one_model_call_and_follows_interests(self):
        with patch("predictor.occupation_path.predict_occupation", side_effect=_probabilities) as predict:
            response = self.client.post(reverse("occupation"), _profile())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(predict.call_count, 1)
        payload = predict.call_args.args[0]
        self.assertEqual(list(payload), MODEL_FEATURES)
        self.assertEqual(payload["education-num"], 9)
        self.assertEqual(payload["capital-gain"], 0)
        self.assertEqual(payload["capital-loss"], 0)
        page = _page(response)
        self.assertNotIn("Gains en capital", page)
        self.assertNotIn("Pertes en capital", page)
        self.assertIn("Pistes à explorer", page)
        self.assertIn(LABELS_FR["Blue-collar"], page)
        self.assertIn('data-family="Blue-collar"', page)
        first_card = page.index('path-card path-card--')
        self.assertTrue(page[first_card:].startswith('path-card path-card--Blue-collar'))
        self.assertIn("Artisanat et réparation", page)
        self.assertIn("à investiguer", page)
        self.assertIn("58,0 %", page)
        self.assertIn("indice", page.lower())
        self.assertNotIn("Écart en points", page)
        self.assertNotIn("path-card-score", page)
        self.assertNotIn("path-meter", page)
        self.assertIn("ne sert pas à classer", page)
        self.assertIn("n'a pas été utilisée pour classer", page)
        self.assertIn("Ce n'est pas l'ordre des pistes", page)
        self.assertLess(page.index("path-card path-card--"), page.index("path-chart-panel"))
        first = page.index("path-card path-card--")
        second = page.index("path-card path-card--", first + 1)
        first_card = page[first:second]
        self.assertIn('data-role="primary"', first_card)
        self.assertIn("Conduite de machines", first_card)
        self.assertNotIn("Manutention", first_card)
        self.assertIn("Piste secondaire", page)
        self.assertIn("1994", page)
        self.assertIn("tunisien", page)
        self.assertIn("15,7", page)
        self.assertIn("ni des offres d'emploi", page)

    def test_goal_and_interests_are_required(self):
        with patch("predictor.occupation_path.predict_occupation", side_effect=_probabilities) as predict:
            missing_goal = self.client.post(reverse("occupation"), _profile(goal=""))
            missing_interest = self.client.post(reverse("occupation"), _profile(interests=[]))
        self.assertEqual(predict.call_count, 0)
        self.assertIn("Choisissez un objectif", _page(missing_goal))
        self.assertIn("au moins un centre d'intérêt", _page(missing_interest))
        self.assertNotIn(PATH_KEY, self.client.session)

    def test_sheet_reuses_the_saved_result_and_prints_without_recalculating(self):
        with patch("predictor.occupation_path.predict_occupation", side_effect=_probabilities) as predict:
            self.client.post(reverse("occupation"), _profile())
            self.assertEqual(predict.call_count, 1)
            sheet = self.client.get(reverse("occupation_sheet"))
            self.assertEqual(predict.call_count, 1)
        page = _page(sheet)
        self.assertEqual(sheet.status_code, 200)
        self.assertIn("Ma voie recommandée", page)
        self.assertIn("34", page)
        self.assertIn("Poursuivre des études", page)
        self.assertIn("Je cherche une voie technique.", page)
        self.assertIn(LABELS_FR["Blue-collar"], page)
        self.assertIn("Prochaines étapes", page)
        self.assertIn("Indice du modèle historique", page)
        self.assertIn("58,0 %", page)
        self.assertIn("Imprimer / Enregistrer en PDF", page)
        self.assertIn("@media print", page)
        self.assertIn("n'est pas recalculée", page)
        self.assertIn("n'a pas été utilisée pour classer", page)
        self.assertNotIn("Revenu (modèle)", page)
        self.assertNotIn("path-card-score", page)
        self.assertLess(page.index("Limites à lire avant les pistes"), page.index("Directions recommandées"))
        self.assertLess(page.index("Directions recommandées"), page.index("Compétences à investiguer"))
        self.assertLess(page.index("Compétences à investiguer"), page.index("Indice du modèle historique"))
        self.assertLess(page.index("Indice du modèle historique"), page.index("Note personnelle"))
        self.assertLess(page.index("Note personnelle"), page.index("profil transmis au modèle"))

    def test_missing_or_invalid_sheet_returns_to_the_explorer(self):
        missing = self.client.get(reverse("occupation_sheet"), follow=True)
        self.assertContains(missing, "Aucune recommandation")
        session = self.client.session
        session[PATH_KEY] = {"goal": "studies", "education_comparison": 9}
        session.save()
        invalid = self.client.get(reverse("occupation_sheet"), follow=True)
        self.assertContains(invalid, "Aucune recommandation")
        self.assertNotIn(PATH_KEY, self.client.session)

    def test_removed_occupation_routes_are_not_registered(self):
        for name in (
            "occupation_challenge",
            "occupation_evaluation",
            "occupation_lab",
            "occupation_api",
            "occupation_mosaic_api",
        ):
            with self.assertRaises(NoReverseMatch):
                reverse(name)
        self.assertEqual(reverse("occupation"), "/prediction-profession/")
        self.assertEqual(reverse("occupation_sheet"), "/prediction-profession/fiche/")
        self.assertEqual(reverse("occupation_login"), "/prediction-profession/connexion/")
        self.assertEqual(reverse("occupation_register"), "/prediction-profession/inscription/")
        self.assertEqual(reverse("occupation_logout"), "/prediction-profession/deconnexion/")
        self.assertEqual(reverse("income_login"), "/prediction-revenu/connexion/")
