from main.models import Game


def get_value(all_participants, participant):
    index = None
    for i, p in enumerate(all_participants):
        if p == participant:
            index = i
            break
    return (len(all_participants) * 3) / 2 - index

def get_scores_after_rounds(round_results, old_scores):
        sorted_players = sorted(old_scores.items(), key=lambda x: x[1], reverse=True)
        player_values = {}
        v = (len(sorted_players) * 3) / 2
        for name, _ in sorted_players:
            player_values[name] = v
            v -= 1

        scores = {}
        for name, _ in player_values.items():
            scores[name] = player_values[name]

            games_by_player = round_results.filter(white_player__name=name)
            if (games_by_player.exists()):
                for game in games_by_player:
                    if (game.result == Game.Result.WHITE_WIN):
                        valueOponent = player_values[game.black_player.name]
                        scores[name] += valueOponent
                    elif (game.result == Game.Result.DRAW):
                        valueOponent = player_values[game.black_player.name]
                        scores[name] += valueOponent * 0.5

            games_by_player = round_results.filter(black_player__name=name)
            if (games_by_player.exists()):
                for game in games_by_player:
                    if (game.result == Game.Result.BLACK_WIN):
                        valueOponent = player_values[game.white_player.name]
                        scores[name] += valueOponent
                    elif (game.result == Game.Result.DRAW):
                        valueOponent = player_values[game.white_player.name]
                        scores[name] += valueOponent * 0.5

        return scores

def add_new_players_to_scores(scores, tournament, round_number):
    all_participants = tournament.participants.filter(joined_before_round__lte=round_number).order_by('-player__rating')
    for participant in all_participants:
        if participant.joined_before_round == round_number:
            v = get_value(all_participants, participant)
            scores[participant.player.name] = v


def get_scores_before_round(tournament, round_number):
    scores = {}
    add_new_players_to_scores(scores, tournament, 1)

    for r in range(1, round_number):
        add_new_players_to_scores(scores, tournament, r + 1)
        passed_rounds = tournament.games.filter(round__lte=r)
        scores = get_scores_after_rounds(passed_rounds, scores)

    # Add players that joined in the current round
    if tournament.round_is_playing:
        add_new_players_to_scores(scores, tournament, round_number + 1)

    return scores

def append_wins_and_total(sorted_list, tournament):
    finished_round = tournament.round_finished
    for i in range(0, len(sorted_list)):
        el = sorted_list[i]
        wins = Game.objects.filter(
            tournament=tournament,
            round__lte=finished_round,
            white_player__name=el[0],
            result=Game.Result.WHITE_WIN
        ).count() + Game.objects.filter(
            tournament=tournament,
            round__lte=finished_round,
            black_player__name=el[0],
            result=Game.Result.BLACK_WIN
        ).count() + Game.objects.filter(
            tournament=tournament,
            round__lte=finished_round,
            white_player__name=el[0],
            result=Game.Result.DRAW
        ).count() * 0.5 + Game.objects.filter(
            tournament=tournament,
            round__lte=finished_round,
            black_player__name=el[0],
            result=Game.Result.DRAW
        ).count() * 0.5

        total_games = Game.objects.filter(
            tournament=tournament,
            round__lte=finished_round
        ).filter(
            white_player__name=el[0]
        ).count() + Game.objects.filter(
            tournament=tournament,
            round__lte=finished_round
        ).filter(
            black_player__name=el[0]
        ).count()

        sorted_list[i] = (sorted_list[i][0], sorted_list[i][1], f"{wins}/{total_games}")