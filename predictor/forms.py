from django import forms

from .ml import load

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
        opts = load()[1]["options"]
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
