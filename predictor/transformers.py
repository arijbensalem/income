"""Préparation des variables pour la cible occupation.

Le transformer est dans le pipeline sauvegardé : au chargement, joblib doit
pouvoir l'importer depuis ce module.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

RAW_FEATURES = [
    "age",
    "workclass",
    "education-num",
    "marital-status",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]

ENGINEERED_COLUMNS = [
    "age",
    "workclass",
    "education-num",
    "marital-status",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
    "age-bin",
    "hours-bin",
    "has-capital-gain",
    "has-capital-loss",
    "edu-x-hours",
    "is-us",
]

COLLAR_GROUPS = {
    "Prof-specialty": "White-collar",
    "Exec-managerial": "White-collar",
    "Tech-support": "White-collar",
    "Adm-clerical": "White-collar",
    "Sales": "White-collar",
    "Craft-repair": "Blue-collar",
    "Machine-op-inspct": "Blue-collar",
    "Transport-moving": "Blue-collar",
    "Handlers-cleaners": "Blue-collar",
    "Farming-fishing": "Blue-collar",
    "Other-service": "Service",
    "Priv-house-serv": "Service",
    "Protective-serv": "Service",
}

LABELS_FR = {
    "White-collar": "Col blanc",
    "Blue-collar": "Col bleu",
    "Service": "Services",
}


class OccupationFeatures(BaseEstimator, TransformerMixin):
    """Reproduit le nettoyage utilisé à l'entraînement, à partir des champs bruts."""

    def __init__(self, rare_min=100):
        self.rare_min = rare_min

    def fit(self, X, y=None):
        counts = pd.Series(X["native-country"]).value_counts()
        self.kept_countries_ = sorted(counts[counts >= self.rare_min].index.tolist())
        return self

    def transform(self, X):
        df = pd.DataFrame(X).copy()
        df["capital-gain"] = np.log1p(df["capital-gain"].astype(float))
        df["capital-loss"] = np.log1p(df["capital-loss"].astype(float))
        kept = set(self.kept_countries_)
        df["native-country"] = df["native-country"].where(
            df["native-country"].isin(kept), "Other"
        )
        df["age-bin"] = pd.cut(
            df["age"].astype(float),
            bins=[0, 25, 35, 45, 55, 65, 100],
            labels=False,
        ).astype(int)
        df["hours-bin"] = pd.cut(
            df["hours-per-week"].astype(float),
            bins=[0, 20, 35, 40, 50, 99],
            labels=False,
        ).astype(int)
        df["has-capital-gain"] = (df["capital-gain"] > 0).astype(int)
        df["has-capital-loss"] = (df["capital-loss"] > 0).astype(int)
        df["edu-x-hours"] = (
            df["education-num"].astype(float) * df["hours-per-week"].astype(float)
        )
        df["is-us"] = (df["native-country"] == "United-States").astype(int)
        return df[ENGINEERED_COLUMNS]

    def get_feature_names_out(self, input_features=None):
        return np.asarray(ENGINEERED_COLUMNS, dtype=object)
