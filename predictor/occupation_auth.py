from functools import wraps
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import OccupationAccount

SESSION_KEY = "occupation_account_id"
PATH_KEY = "occupation_pathway"


class OccupationRegisterForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150, min_length=3)
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if OccupationAccount.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris pour la profession.")
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        account = OccupationAccount(username=self.cleaned_data["username"])
        account.set_password(self.cleaned_data["password1"])
        account.save()
        return account


class OccupationLoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = None
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username", "").strip()
        password = cleaned.get("password", "")
        if not username or not password:
            return cleaned
        try:
            account = OccupationAccount.objects.get(username__iexact=username)
        except OccupationAccount.DoesNotExist:
            raise forms.ValidationError("Nom d'utilisateur ou mot de passe incorrect.")
        if not account.check_password(password):
            raise forms.ValidationError("Nom d'utilisateur ou mot de passe incorrect.")
        self.account = account
        return cleaned


def get_occupation_account(request):
    account_id = request.session.get(SESSION_KEY)
    if not account_id:
        return None
    try:
        return OccupationAccount.objects.get(pk=account_id)
    except OccupationAccount.DoesNotExist:
        request.session.pop(SESSION_KEY, None)
        return None


def login_occupation_account(request, account):
    request.session[SESSION_KEY] = account.pk
    request.session.modified = True


def logout_occupation_account(request):
    request.session.pop(SESSION_KEY, None)
    request.session.pop(PATH_KEY, None)
    request.session.modified = True


def occupation_account_required(view):
    @login_not_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        account = get_occupation_account(request)
        if account is None:
            login_url = reverse("occupation_login")
            next_url = request.get_full_path()
            return redirect(f"{login_url}?{urlencode({'next': next_url})}")
        request.occupation_account = account
        return view(request, *args, **kwargs)

    return wrapped


def _safe_next(raw, fallback_name="occupation"):
    if isinstance(raw, str) and raw.startswith("/prediction-profession/") and not raw.startswith("//"):
        return raw
    return reverse(fallback_name)


@login_not_required
@require_http_methods(["GET", "POST"])
def occupation_login(request):
    account = get_occupation_account(request)
    next_url = _safe_next(request.POST.get("next") or request.GET.get("next"))
    if account is not None and request.method == "GET":
        return redirect(next_url)
    form = OccupationLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login_occupation_account(request, form.account)
        return redirect(next_url)
    return render(request, "predictor/occupation_account_login.html", {
        "form": form,
        "next": next_url,
        "site_user": request.user if request.user.is_authenticated else None,
    })


@login_not_required
@require_http_methods(["GET", "POST"])
def occupation_register(request):
    if get_occupation_account(request) is not None and request.method == "GET":
        return redirect("occupation")
    next_url = _safe_next(request.POST.get("next") or request.GET.get("next"))
    form = OccupationRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        account = form.save()
        login_occupation_account(request, account)
        messages.success(request, "Compte profession créé. Vous pouvez explorer un parcours.")
        return redirect(next_url)
    return render(request, "predictor/occupation_account_register.html", {
        "form": form,
        "next": next_url,
        "site_user": request.user if request.user.is_authenticated else None,
    })


@login_not_required
@require_http_methods(["POST"])
def occupation_logout(request):
    logout_occupation_account(request)
    messages.info(request, "Vous êtes déconnecté du site profession.")
    return redirect("occupation_login")
