from django import forms
from django.contrib.auth.forms import AuthenticationForm

class EmailLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Invalid email or password. Please try again.',
        'inactive': 'Your account is inactive. Contact the administrator if you need access.',
    }

    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'autocomplete': 'email',
            'autofocus': 'autofocus',
        }),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        }),
        label="Password"
    )
