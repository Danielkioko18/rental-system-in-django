from django.contrib.auth.views import LoginView
from .forms import EmailLoginForm

class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = EmailLoginForm

