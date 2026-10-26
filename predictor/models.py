from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class OccupationAccount(models.Model):
    username = models.CharField("nom d'utilisateur", max_length=150, unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "compte profession"
        verbose_name_plural = "comptes profession"

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
