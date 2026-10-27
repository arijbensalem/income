from django import forms
import json
from pathlib import Path

from .ml import load, load_hours, load_occupation, load_sous_evalue

EDUCATION = [
    (1, "Préscolaire"), (2, "1re–4e année"), (3, "5e–6e année"), (4, "7e–8e année"),
    (5, "9e année"), (6, "10e année"), (7, "11e année"), (8, "12e année (sans diplôme)"),
    (9, "Baccalauréat / HS-grad"), (10, "Études supérieures non terminées"),
    (11, "Diplôme professionnel (Assoc-voc)"), (12, "Diplôme académique (Assoc-acdm)"),
    (13, "Licence (Bachelors)"), (14, "Master"), (15, "École professionnelle (Prof-school)"),
    (16, "Doctorat"),
]


class IncomeForm(forms.Form):
    age = forms.IntegerField(label="Âge", min_value=17, max_value=90)
    hours_per_week = forms.IntegerField(label="Heures travaillées / semaine", min_value=1, max_value=99)
    education_num = forms.TypedChoiceField(label="Niveau d'études", choices=EDUCATION, coerce=int)
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=99999, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=4356, initial=0)
    workclass = forms.ChoiceField(label="Secteur d'emploi")
    occupation = forms.ChoiceField(label="Profession")
    marital_status = forms.ChoiceField(label="Situation maritale")
    relationship = forms.ChoiceField(label="Rôle dans le foyer")
    sex = forms.ChoiceField(label="Sexe")
    race = forms.ChoiceField(label="Origine (catégorie UCI)")
    native_country = forms.ChoiceField(label="Pays d'origine")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = load("income")[1]["options"]
        mapping = {"workclass": "workclass", "occupation": "occupation",
                   "marital_status": "marital-status", "relationship": "relationship",
                   "sex": "sex", "race": "race", "native_country": "native-country"}
        for field, key in mapping.items():
            # la valeur envoyée au modèle reste la valeur brute du dataset
            self.fields[field].choices = [("", "Choisir…")] + [(v, v.replace("-", " ")) for v in opts[key]]
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"], "workclass": d["workclass"], "education-num": d["education_num"],
            "marital-status": d["marital_status"], "occupation": d["occupation"],
            "relationship": d["relationship"], "race": d["race"], "sex": d["sex"],
            "capital-gain": d["capital_gain"], "capital-loss": d["capital_loss"],
            "hours-per-week": d["hours_per_week"], "native-country": d["native_country"],
        }


# ----------------------------------------------------------------------
# MARRIED
# ----------------------------------------------------------------------
# Charger la configuration pour récupérer les options dynamiques du modèle married
CONFIG_PATH = Path(__file__).resolve().parent.parent / "ml_models" / "married" / "config.json"
options = {}
if CONFIG_PATH.exists():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    options = config.get("options", {})

# Libellés français ; la valeur envoyée au modèle reste la valeur brute du dataset.
MARRIED_LABELS = {
    "workclass": {
        "Private": "Secteur privé", "Self-emp-not-inc": "Indépendant", "Self-emp-inc": "Chef d'entreprise",
        "Federal-gov": "Fonction publique (État)", "State-gov": "Fonction publique (région)",
        "Local-gov": "Fonction publique (commune)", "Without-pay": "Non rémunéré",
        "Never-worked": "N'a jamais travaillé",
    },
    "occupation": {
        "Adm-clerical": "Employé administratif", "Armed-Forces": "Armée", "Craft-repair": "Artisan / réparation",
        "Exec-managerial": "Cadre / manager", "Farming-fishing": "Agriculture / pêche",
        "Handlers-cleaners": "Manutention / nettoyage", "Machine-op-inspct": "Opérateur machine",
        "Other-service": "Services (restauration, aide…)", "Priv-house-serv": "Employé de maison",
        "Prof-specialty": "Profession intellectuelle", "Protective-serv": "Sécurité / protection",
        "Sales": "Commerce / vente", "Tech-support": "Support technique", "Transport-moving": "Transport / livraison",
    },
    "sex": {"Male": "Homme", "Female": "Femme"},
    "race": {
        "White": "Blanc", "Black": "Noir", "Asian-Pac-Islander": "Asiatique / Îlien du Pacifique",
        "Amer-Indian-Eskimo": "Amérindien / Esquimau", "Other": "Autre",
    },
    "native-country": {
        "United-States": "États-Unis", "Cambodia": "Cambodge", "Canada": "Canada", "China": "Chine",
        "Columbia": "Colombie", "Cuba": "Cuba", "Dominican-Republic": "République dominicaine",
        "Ecuador": "Équateur", "El-Salvador": "Salvador", "England": "Angleterre", "France": "France",
        "Germany": "Allemagne", "Greece": "Grèce", "Guatemala": "Guatemala", "Haiti": "Haïti",
        "Hong": "Hong Kong", "Hungary": "Hongrie", "India": "Inde", "Iran": "Iran", "Ireland": "Irlande",
        "Italy": "Italie", "Jamaica": "Jamaïque", "Japan": "Japon", "Mexico": "Mexique",
        "Nicaragua": "Nicaragua", "Poland": "Pologne", "Portugal": "Portugal", "Puerto-Rico": "Porto Rico",
        "Scotland": "Écosse", "South": "Corée du Sud", "Taiwan": "Taïwan", "Thailand": "Thaïlande",
        "Trinadad&Tobago": "Trinité-et-Tobago", "Vietnam": "Viêt Nam", "Other": "Autre",
    },
}


class MarriedForm(forms.Form):
    age = forms.IntegerField(label="Âge", min_value=17, max_value=90)
    hours_per_week = forms.IntegerField(label="Heures travaillées / semaine", min_value=1, max_value=99)
    education_num = forms.TypedChoiceField(label="Niveau d'études", choices=EDUCATION, coerce=int)
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=99999, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=4356, initial=0)

    workclass = forms.ChoiceField(label="Secteur d'emploi")
    occupation = forms.ChoiceField(label="Profession")
    race = forms.ChoiceField(label="Origine")
    sex = forms.ChoiceField(label="Sexe")
    native_country = forms.ChoiceField(label="Pays d'origine")
    income = forms.ChoiceField(
        label="Revenu annuel", initial="<=50K",
        choices=[("<=50K", "50 000 $ ou moins par an"), (">50K", "Plus de 50 000 $ par an")])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        married_opts = options  # chargé depuis config.json
        mapping = {
            "workclass": "workclass",
            "occupation": "occupation",
            "race": "race",
            "sex": "sex",
            "native_country": "native-country",
        }
        for field, key in mapping.items():
            if key in married_opts:
                labels = MARRIED_LABELS.get(key, {})
                choices = [(v, labels.get(v, str(v).replace("-", " "))) for v in married_opts[key]]
                choices.sort(key=lambda c: c[1])
                self.fields[field].choices = [("", "Choisir…")] + choices
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"],
            "workclass": d["workclass"],
            "education-num": d["education_num"],
            "occupation": d["occupation"],
            "race": d["race"],
            "sex": d["sex"],
            "capital-gain": d["capital_gain"],
            "capital-loss": d["capital_loss"],
            "hours-per-week": d["hours_per_week"],
            "native-country": d["native_country"],
            "income": d["income"],
        }



# ----------------------------------------------------------------------
# JEUNE ACTIF (banque / assurance)
# ----------------------------------------------------------------------
# Libellés en français ; la valeur envoyée au modèle reste la valeur brute du dataset.
FR_LABELS = {
    "workclass": {
        "Private": "Secteur privé", "Self-emp-not-inc": "Indépendant", "Self-emp-inc": "Chef d'entreprise",
        "Federal-gov": "Fonction publique (État)", "State-gov": "Fonction publique (région)",
        "Local-gov": "Fonction publique (commune)", "Without-pay": "Non rémunéré",
    },
    "marital-status": {
        "Never-married": "Célibataire", "Married-civ-spouse": "Marié(e)", "Married-AF-spouse": "Marié(e) (conjoint militaire)",
        "Married-spouse-absent": "Marié(e), conjoint absent", "Divorced": "Divorcé(e)",
        "Separated": "Séparé(e)", "Widowed": "Veuf / veuve",
    },
    "occupation": {
        "Adm-clerical": "Employé administratif", "Armed-Forces": "Armée", "Craft-repair": "Artisan / réparation",
        "Exec-managerial": "Cadre / manager", "Farming-fishing": "Agriculture / pêche",
        "Handlers-cleaners": "Manutention / nettoyage", "Machine-op-inspct": "Opérateur machine",
        "Other-service": "Services (restauration, aide…)", "Priv-house-serv": "Employé de maison",
        "Prof-specialty": "Profession intellectuelle", "Protective-serv": "Sécurité / protection",
        "Sales": "Commerce / vente", "Tech-support": "Support technique", "Transport-moving": "Transport / livraison",
    },
    "relationship": {
        "Own-child": "Vit chez ses parents", "Not-in-family": "Vit seul(e) / colocation",
        "Husband": "Époux", "Wife": "Épouse", "Unmarried": "Parent seul / non marié(e)",
        "Other-relative": "Vit chez un autre proche",
    },
}


class JeuneForm(forms.Form):
    occupation = forms.ChoiceField(label="Profession")
    workclass = forms.ChoiceField(label="Type d'employeur")
    hours_per_week = forms.IntegerField(label="Heures travaillées / semaine", min_value=1, max_value=99)
    education_num = forms.TypedChoiceField(label="Niveau d'études", choices=EDUCATION, coerce=int)
    income_gt50k = forms.TypedChoiceField(
        label="Revenu annuel", coerce=int,
        choices=[(0, "Jusqu'à 50 000 $"), (1, "Plus de 50 000 $")])
    marital_status = forms.ChoiceField(label="Situation familiale")
    relationship = forms.ChoiceField(label="Logement / foyer")

    MAPPING = {"workclass": "workclass", "occupation": "occupation",
               "marital_status": "marital-status", "relationship": "relationship"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = load("jeune")[1]["options"]
        for field, key in self.MAPPING.items():
            labels = FR_LABELS[key]
            choices = sorted(((v, labels.get(v, v)) for v in opts[key]), key=lambda c: c[1])
            self.fields[field].choices = [("", "Choisir…")] + choices
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "education-num": d["education_num"], "hours-per-week": d["hours_per_week"],
            "income_gt50k": d["income_gt50k"], "workclass": d["workclass"],
            "marital-status": d["marital_status"], "occupation": d["occupation"],
            "relationship": d["relationship"],
        }


# ----------------------------------------------------------------------
# DIPLÔMÉ SOUS-ÉVALUÉ
# ----------------------------------------------------------------------
class SousEvalueForm(forms.Form):
    """Profil d'un diplômé (Licence ou plus). Le niveau d'études et le revenu
    définissent la cible : ils ne sont pas demandés."""
    age = forms.IntegerField(label="Âge", min_value=17, max_value=90)
    hours_per_week = forms.IntegerField(label="Heures travaillées / semaine", min_value=1, max_value=99)
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=99999, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=4356, initial=0)
    workclass = forms.ChoiceField(label="Secteur d'emploi")
    occupation = forms.ChoiceField(label="Profession")
    marital_status = forms.ChoiceField(label="Situation maritale")
    relationship = forms.ChoiceField(label="Rôle dans le foyer")
    sex = forms.ChoiceField(label="Sexe")
    race = forms.ChoiceField(label="Origine (catégorie UCI)")
    native_country = forms.ChoiceField(label="Pays d'origine")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = load_sous_evalue()[1]["options"]
        mapping = {"workclass": "workclass", "occupation": "occupation",
                   "marital_status": "marital-status", "relationship": "relationship",
                   "sex": "sex", "race": "race", "native_country": "native-country"}
        for field, key in mapping.items():
            self.fields[field].choices = [("", "Choisir…")] + [(v, v.replace("-", " ")) for v in opts[key]]
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"], "workclass": d["workclass"],
            "marital-status": d["marital_status"], "occupation": d["occupation"],
            "relationship": d["relationship"], "race": d["race"], "sex": d["sex"],
            "capital-gain": d["capital_gain"], "capital-loss": d["capital_loss"],
            "hours-per-week": d["hours_per_week"], "native-country": d["native_country"],
        }


# ----------------------------------------------------------------------
# TEMPS DE TRAVAIL
# ----------------------------------------------------------------------
class HoursForm(forms.Form):
    """Profil complet sauf les heures travaillées (la cible). Le revenu est une entrée."""
    age = forms.IntegerField(label="Âge", min_value=17, max_value=90)
    education_num = forms.TypedChoiceField(label="Niveau d'études", choices=EDUCATION, coerce=int)
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=99999, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=4356, initial=0)
    workclass = forms.ChoiceField(label="Secteur d'emploi")
    occupation = forms.ChoiceField(label="Profession")
    marital_status = forms.ChoiceField(label="Situation maritale")
    relationship = forms.ChoiceField(label="Rôle dans le foyer")
    sex = forms.ChoiceField(label="Sexe")
    race = forms.ChoiceField(label="Origine (catégorie UCI)")
    native_country = forms.ChoiceField(label="Pays d'origine")
    income = forms.ChoiceField(label="Revenu annuel")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = load_hours()[1]["options"]
        mapping = {"workclass": "workclass", "occupation": "occupation",
                   "marital_status": "marital-status", "relationship": "relationship",
                   "sex": "sex", "race": "race", "native_country": "native-country",
                   "income": "income"}
        income_labels = {"<=50K": "≤ 50 000 $", ">50K": "> 50 000 $"}
        for field, key in mapping.items():
            self.fields[field].choices = [("", "Choisir…")] + [
                (v, income_labels.get(v, v.replace("-", " "))) for v in opts[key]]
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"], "workclass": d["workclass"], "education-num": d["education_num"],
            "marital-status": d["marital_status"], "occupation": d["occupation"],
            "relationship": d["relationship"], "race": d["race"], "sex": d["sex"],
            "capital-gain": d["capital_gain"], "capital-loss": d["capital_loss"],
            "native-country": d["native_country"], "income": d["income"],
        }

# ----------------------------------------------------------------------
# PROFESSION (occupation)
# ----------------------------------------------------------------------
class OccupationForm(forms.Form):
    age = forms.IntegerField(label="Âge", min_value=17, max_value=90)
    hours_per_week = forms.IntegerField(label="Heures travaillées / semaine", min_value=1, max_value=99)
    education_num = forms.TypedChoiceField(label="Niveau d'études", choices=EDUCATION, coerce=int)
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=99999, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=4356, initial=0)
    workclass = forms.ChoiceField(label="Secteur d'emploi")
    marital_status = forms.ChoiceField(label="Situation maritale")
    relationship = forms.ChoiceField(label="Rôle dans le foyer")
    sex = forms.ChoiceField(label="Sexe")
    race = forms.ChoiceField(label="Origine (catégorie UCI)")
    native_country = forms.ChoiceField(label="Pays d'origine")
    income = forms.ChoiceField(label="Revenu annuel")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = load_occupation()[1]["options"]
        mapping = {
            "workclass": "workclass",
            "marital_status": "marital-status",
            "relationship": "relationship",
            "sex": "sex",
            "race": "race",
            "native_country": "native-country",
            "income": "income",
        }
        income_labels = {"<=50K": "≤ 50 000 $", ">50K": "> 50 000 $"}
        for field, key in mapping.items():
            choices = []
            for value in opts[key]:
                label = income_labels.get(value, value.replace("-", " "))
                choices.append((value, label))
            self.fields[field].choices = [("", "Choisir…")] + choices
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"],
            "workclass": d["workclass"],
            "education-num": d["education_num"],
            "marital-status": d["marital_status"],
            "relationship": d["relationship"],
            "race": d["race"],
            "sex": d["sex"],
            "capital-gain": d["capital_gain"],
            "capital-loss": d["capital_loss"],
            "hours-per-week": d["hours_per_week"],
            "native-country": d["native_country"],
            "income": d["income"],
        }
    # ----------------------------------------------------------------------
# RELATION FAMILIALE (relationship)
# ----------------------------------------------------------------------
class RelationshipForm(forms.Form):
    age = forms.IntegerField(label="Âge", min_value=1, max_value=120)
    fnlwgt = forms.IntegerField(label="Poids final (données UCI)", min_value=0, max_value=2000000)
    education = forms.ChoiceField(label="Éducation")
    education_num = forms.IntegerField(label="Années d'études", min_value=0, max_value=20)
    marital_status = forms.ChoiceField(label="Statut matrimonial")
    occupation = forms.ChoiceField(label="Profession")
    race = forms.ChoiceField(label="Origine ethnique")
    sex = forms.ChoiceField(label="Sexe")
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=200000, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=10000, initial=0)
    hours_per_week = forms.IntegerField(label="Heures travaillées par semaine", min_value=0, max_value=168)
    workclass = forms.ChoiceField(label="Classe de travail")
    native_country = forms.ChoiceField(label="Pays d'origine")
    income = forms.ChoiceField(label="Revenu annuel")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_field_choices()

    def _init_field_choices(self):
        """Initialiser les choix des champs catégoriques (valeur brute du dataset, libellé français)."""
        education_labels = {
            "Preschool": "Maternelle", "1st-4th": "1ère-4ème", "5th-6th": "5ème-6ème",
            "7th-8th": "7ème-8ème", "9th": "9ème", "10th": "10ème", "11th": "11ème",
            "12th": "12ème", "HS-grad": "Diplômé du secondaire",
            "Some-college": "Études supérieures partielles", "Assoc-voc": "Diplôme professionnel",
            "Assoc-acdm": "Diplôme académique", "Bachelors": "Licence", "Masters": "Master",
            "Prof-school": "École professionnelle", "Doctorate": "Doctorat",
        }
        workclass_labels = {
            "Private": "Secteur privé", "Self-emp-not-inc": "Indépendant",
            "Self-emp-inc": "Indépendant (Incorporé)", "Federal-gov": "Gouvernement fédéral",
            "Local-gov": "Gouvernement local", "State-gov": "Gouvernement d'État",
            "Without-pay": "Sans rémunération", "Never-worked": "N'a jamais travaillé",
        }
        marital_status_labels = {
            "Married-civ-spouse": "Marié(e)", "Married-spouse-absent": "Marié(e) - Conjoint absent",
            "Married-AF-spouse": "Marié(e) - Conjoint militaire", "Never-married": "Jamais marié(e)",
            "Separated": "Séparé(e)", "Divorced": "Divorcé(e)", "Widowed": "Veuf/Veuve",
        }
        occupation_labels = {
            "Tech-support": "Support technique", "Craft-repair": "Artisan/Réparation",
            "Other-service": "Autres services", "Sales": "Vente",
            "Exec-managerial": "Directeur/Gestionnaire", "Prof-specialty": "Profession spécialisée",
            "Machine-op-inspct": "Opérateur de machine", "Transport-moving": "Transport/Déménagement",
            "Handlers-cleaners": "Manutention/Nettoyage", "Farming-fishing": "Agriculture/Pêche",
            "Armed-Forces": "Forces armées", "Protective-serv": "Services de protection",
            "Priv-house-serv": "Service domestique", "Adm-clerical": "Administration",
        }
        race_labels = {
            "White": "Blanc", "Black": "Noir", "Asian-Pac-Islander": "Asiatique/Îlien du Pacifique",
            "Amer-Indian-Eskimo": "Amérindien/Esquimau", "Other": "Autre",
        }
        sex_labels = {"Male": "Homme", "Female": "Femme"}
        income_labels = {"<=50K": "≤ 50 000 $", ">50K": "> 50 000 $"}
        country_labels = {
            "United-States": "États-Unis", "Cambodia": "Cambodge", "Canada": "Canada", "China": "Chine",
            "Columbia": "Colombie", "Cuba": "Cuba", "Dominican-Republic": "République Dominicaine",
            "Ecuador": "Équateur", "El-Salvador": "El Salvador", "England": "Angleterre",
            "France": "France", "Germany": "Allemagne", "Greece": "Grèce", "Guatemala": "Guatemala",
            "Haiti": "Haïti", "Hong": "Hong Kong", "Hungary": "Hongrie", "India": "Inde",
            "Iran": "Iran", "Ireland": "Irlande", "Italy": "Italie", "Jamaica": "Jamaïque",
            "Japan": "Japon", "Mexico": "Mexique", "Nicaragua": "Nicaragua", "Poland": "Pologne",
            "Portugal": "Portugal", "Puerto-Rico": "Porto Rico", "Scotland": "Écosse",
            "South": "Afrique du Sud", "Taiwan": "Taiwan", "Thailand": "Thaïlande",
            "Trinadad&Tobago": "Trinité-et-Tobago", "Vietnam": "Vietnam",
        }

        cat_choices = {
            "workclass": ["Private", "Self-emp-not-inc", "Self-emp-inc", "Federal-gov", "Local-gov",
                          "State-gov", "Without-pay", "Never-worked"],
            "education": ["Preschool", "1st-4th", "5th-6th", "7th-8th", "9th", "10th", "11th", "12th",
                          "HS-grad", "Some-college", "Assoc-voc", "Assoc-acdm", "Bachelors", "Masters",
                          "Prof-school", "Doctorate"],
            "marital-status": ["Married-civ-spouse", "Married-spouse-absent", "Married-AF-spouse",
                               "Never-married", "Separated", "Divorced", "Widowed"],
            "occupation": ["Tech-support", "Craft-repair", "Other-service", "Sales", "Exec-managerial",
                           "Prof-specialty", "Machine-op-inspct", "Transport-moving", "Handlers-cleaners",
                           "Farming-fishing", "Armed-Forces", "Protective-serv", "Priv-house-serv",
                           "Adm-clerical"],
            "race": ["White", "Black", "Asian-Pac-Islander", "Amer-Indian-Eskimo", "Other"],
            "sex": ["Male", "Female"],
            "native-country": list(country_labels.keys()),
            "income": ["<=50K", ">50K"],
        }

        mapping = {
            "workclass": ("workclass", workclass_labels),
            "education": ("education", education_labels),
            "marital_status": ("marital-status", marital_status_labels),
            "occupation": ("occupation", occupation_labels),
            "race": ("race", race_labels),
            "sex": ("sex", sex_labels),
            "native_country": ("native-country", country_labels),
            "income": ("income", income_labels),
        }

        for field_name, (key, labels) in mapping.items():
            choices = [(v, labels.get(v, v.replace("-", " "))) for v in cat_choices[key]]
            self.fields[field_name].choices = [("", "Choisir…")] + choices

        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"],
            "workclass": d["workclass"],
            "fnlwgt": d["fnlwgt"],
            "education": d["education"],
            "education-num": d["education_num"],
            "marital-status": d["marital_status"],
            "occupation": d["occupation"],
            "race": d["race"],
            "sex": d["sex"],
            "capital-gain": d["capital_gain"],
            "capital-loss": d["capital_loss"],
            "hours-per-week": d["hours_per_week"],
            "native-country": d["native_country"],
            "income": d["income"],
        }