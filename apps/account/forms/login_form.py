from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
                "autofocus": True,
                "placeholder": "name@example.com",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
                "placeholder": "••••••••",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label="Stay signed in for longer",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "rememberMe"}),
    )
