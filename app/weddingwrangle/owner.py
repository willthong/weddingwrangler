from django.views.generic import (
    CreateView,
    UpdateView, 
    DeleteView, 
    ListView, 
    DetailView
)
from django.contrib.auth.mixins import LoginRequiredMixin


class OwnerListView(ListView):
    """
    Sub-class the ListView to pass the request to the form.
    """
