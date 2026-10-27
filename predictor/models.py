from django.db import models
from django.utils import timezone


class RelationshipPrediction(models.Model):
    """Historique des prédictions de relation familiale"""
    RELATIONSHIP_CHOICES = [
        ("Husband", "Mari"),
        ("Wife", "Épouse"),
        ("Own-child", "Enfant propre"),
        ("Unmarried", "Non marié(e)"),
        ("Not-in-family", "Pas de lien de famille"),
        ("Other-relative", "Autre parent"),
    ]

    # Prédiction
    predicted_relationship = models.CharField(
        max_length=20, choices=RELATIONSHIP_CHOICES
    )
    probability = models.FloatField()  # 0-100
    
    # Revenu du client (pour calculs dynamiques)
    income = models.IntegerField(null=True, blank=True)
    
    # Profil utilisé pour la prédiction (stocké en JSON)
    profile_data = models.JSONField()
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["predicted_relationship"]),
        ]
    
    def __str__(self):
        return f"{self.predicted_relationship} - {self.probability}% ({self.created_at.strftime('%d/%m/%Y %H:%M')})"
