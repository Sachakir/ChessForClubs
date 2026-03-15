from django.urls import path

from . import views

urlpatterns = [
    path('', views.TournamentListView.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('tournament/<str:name>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
    path('tournament/<str:name>/make_pairings/', views.makePairings, name='make_pairings'),
    path('tournament/<str:name>/end_round/', views.endRound, name='end_round'),
    path('tournament/<str:name>/round_pairings/<int:round_number>/', views.roundPairings, name='round_pairings'),
]