from django.urls import path
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView

app_name = 'auth'

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]