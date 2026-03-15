from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.contrib import messages
from main.keizer_calculations import append_wins_and_total, get_scores_before_round
from main.models import Game, Player, Tournament, TournamentParticipant

class TournamentListView(ListView):
    """Homepage view listing all tournaments."""
    model = Tournament

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament_names'] = Tournament.objects.values_list('name', flat=True)
        return context


class TournamentDetailView(DetailView):
    """Detail view for a single tournament."""
    model = Tournament
    slug_field = 'name'  # Use the 'name' field for lookup
    slug_url_kwarg = 'name'  # Match the URL parameter name

    def post(self, request, *args, **kwargs):
        """Handle adding a player to the tournament or starting a new round."""
        tournament = self.get_object()
        
        action = request.POST.get('action')
        
        if action == 'start_round' and request.user.is_staff:
            # Start a new round
            tournament.round_finished += 1
            tournament.save()
            messages.success(request, f"Round {tournament.round_finished} has started!")
            return redirect('tournament_detail', name=tournament.name)
        
        elif action == 'add_player':
            # Handle adding a player
            if not tournament.allow_inscriptions:
                return redirect('tournament_detail', name=tournament.name)
            
            player_name = request.POST.get('player_name', '').strip()
            player_elo = request.POST.get('player_elo', '')
            
            if player_name and player_elo:
                # Create new player with optional ELO rating
                elo_value = None
                try:
                    elo_value = int(player_elo)
                except ValueError:
                    elo_value = None
                
                try:

                    player = Player.objects.filter(name=player_name)  # Check if player already exists
                    if (not player.exists()):

                        player = Player.objects.create(
                            name=player_name,
                            rating=elo_value
                        )
                    else:
                        player = player.first()

                    joined =tournament.round_finished + 1
                    if tournament.round_is_playing:
                        joined = joined + 1

                    # Create tournament participant
                    TournamentParticipant.objects.get_or_create(
                        tournament=tournament,
                        player=player,
                        joined_before_round=joined
                    )
                except Exception as e:
                    print(f"Error creating player or participant: {e}")

        elif action == 'register_results':
            for game in tournament.games.filter(round=tournament.round_finished + 1):
                result = request.POST.get(f'game_{game.id}_result')
                game.result = result
                game.save()

        return redirect('tournament_detail', name=tournament.name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_object()

        finished_round = tournament.round_finished
        standings = get_scores_before_round(tournament, finished_round + 1)
        sorted_list = sorted(standings.items(), key=lambda x: x[1], reverse=True)

        append_wins_and_total(sorted_list, tournament)

        context['games'] = Game.objects.filter(tournament=tournament, round__exact=finished_round+1)
        context['standings'] = sorted_list
        context['is_admin'] = self.request.user.is_staff or self.request.user.is_superuser
        context['rounds_count'] = range(1, tournament.round_finished + 1)
        context['tournament_names'] = Tournament.objects.values_list('name', flat=True)

        return context


def makePairings(request, name):
    """View to trigger pairing generation for the next round."""
    tournament = get_object_or_404(Tournament, name=name)
    if (tournament.round_is_playing == True):
        messages.error(request, "Current round is still playing. Please finish it before generating pairings for the next round.")
        return redirect('tournament_detail', name=name) 

    if request.method == 'POST':
        finished_round = tournament.round_finished
        standings = get_scores_before_round(tournament, finished_round + 1)

        all_players = []
        for name, _ in standings.items():
            all_players.append(name)
        
        players_names = request.POST.getlist('selected_players')

        diffs = list(set(all_players) - set(players_names))

        for diff in diffs:
            standings.pop(diff, None)

        sorted_list = sorted(standings.items(), key=lambda x: x[1], reverse=True)

        for i in range(0, int(sorted_list.__len__() / 2) * 2, 2):
            p0_white_count = Game.objects.filter(
                tournament=tournament,
                round__lt=finished_round,
                white_player__name=sorted_list[i][0]
            ).count()
            p1_white_count = Game.objects.filter(
                tournament=tournament,
                round__lt=finished_round,
                white_player__name=sorted_list[i+1][0]
            ).count()

            if p0_white_count < p1_white_count:
                Game.objects.create(
                    tournament=tournament,
                    round=finished_round + 1,
                    white_player=Player.objects.get(name=sorted_list[i][0]),
                    black_player=Player.objects.get(name=sorted_list[i+1][0])
                )
            else:
                Game.objects.create(
                    tournament=tournament,
                    round=finished_round + 1,
                    white_player=Player.objects.get(name=sorted_list[i+1][0]),
                    black_player=Player.objects.get(name=sorted_list[i][0])
                )

        if sorted_list.__len__() >= 2:
            tournament.round_is_playing = True
        
        tournament.allow_inscriptions = False
        tournament.save()

        return redirect('tournament_detail', name=tournament.name)

    # Check if user is admin
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to generate pairings.")
        return redirect('tournament_detail', name=name)
    
    participants = tournament.participants.filter(joined_before_round__lte=tournament.round_finished + 1)

    template = 'main/pairings.html'
    return render(request, template, {'tournament': tournament, 'participants': participants,
                                      'tournament_names': Tournament.objects.values_list('name', flat=True)})


def endRound(request, name):
    tournament = get_object_or_404(Tournament, name=name)

    # Check if user is admin
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to end the round.")
        return redirect('tournament_detail', name=name)
    
    not_finished_games = Game.objects.filter(tournament=tournament, round__exact=tournament.round_finished + 1, result__exact='').count()

    if not_finished_games == 0:
        tournament.round_is_playing = False
        tournament.round_finished += 1
        tournament.save()
        messages.success(request, f"Round {tournament.round_finished} has ended!")
    else:
        messages.error(request, f"There are still {not_finished_games} games not finished.")

    return redirect('tournament_detail', name=name)


def about(request):
    context = {'tournament_names': Tournament.objects.values_list('name', flat=True)}
    return render(request, 'main/about.html', context)


def roundPairings(request, name, round_number):
    tournament = get_object_or_404(Tournament, name=name)
    template = 'main/round_pairings.html'
    games = tournament.games.filter(round=round_number)
    return render(request, template, {'games': games, 'round_number': round_number, 
                                      'tournament_names': Tournament.objects.values_list('name', flat=True)})
