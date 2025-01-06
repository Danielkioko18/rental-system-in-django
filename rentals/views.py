from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard'
        context['welcome_message'] = 'Welcome to the Dashboard!'
        return context


class HousesView(LoginRequiredMixin, TemplateView):
    template_name = 'houses.html'

    def get_context_data(self, **kwargs):
        # Add houses data to be displayed in the table
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Houses'
        context['houses'] = [
            {'number': '101', 'is_occupied': True},
            {'number': '102', 'is_occupied': False},
            {'number': '103', 'is_occupied': True},
            {'number': '104', 'is_occupied': False},
        ]
        return context
