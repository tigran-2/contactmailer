from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('create/', views.campaign_create, name='campaign_create'),
    path('<int:pk>/trigger/', views.campaign_trigger, name='campaign_trigger'),
    path('<int:pk>/progress/', views.campaign_progress_view, name='campaign_progress'),
]
