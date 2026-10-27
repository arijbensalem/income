from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render


class StyledAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Nom d'utilisateur ou mot de passe incorrect.",
        "inactive": "Ce compte est désactivé.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["password"].label = "Mot de passe"
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"


class RelationshipAuthForm(AuthenticationForm):
    """Formulaire de login dédié à Relation Familiale"""
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Identifiants incorrect.",
        "inactive": "Compte désactivé.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["password"].label = "Mot de passe"
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"


class RelationshipRegisterForm(UserCreationForm):
    """Formulaire d'inscription dédié à Relation Familiale"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["password1"].label = "Mot de passe"
        self.fields["password2"].label = "Confirmer le mot de passe"
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["password1"].label = "Mot de passe"
        self.fields["password2"].label = "Confirmer le mot de passe"
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"


@login_not_required
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(request, "predictor/register.html", {"form": form})