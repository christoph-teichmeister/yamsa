from django import forms


class LoginForm(forms.Form):
    """Validation only - account/login.html renders the fields itself."""

    email = forms.EmailField(label="Email address")
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    remember_me = forms.BooleanField(label="Stay signed in for longer", required=False)
