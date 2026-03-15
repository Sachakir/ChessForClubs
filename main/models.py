from django.db import models
from django.db.models import Q, F

class Player(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rating = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Tournament(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField()

    round_finished = models.IntegerField(default=0)
    allow_inscriptions = models.BooleanField(default=True)
    round_is_playing = models.BooleanField(default=False)

    #end_date = models.DateTimeField(null=True, blank=True)
    
    players = models.ManyToManyField(
        Player,
        through='TournamentParticipant',
        related_name="tournaments"
    )

    def __str__(self):
        return self.name


class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="participants"
    )
    
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE
    )
    
    joined_before_round = models.IntegerField(default=1)

    class Meta:
        unique_together = ("tournament", "player")

    def __str__(self):
        return f"{self.player.name} joined {self.tournament.name} before round {self.joined_before_round}"

class Game(models.Model):

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="games",
        null=False
        )

    round = models.IntegerField()

    class Result(models.TextChoices):
        WHITE_WIN = "1-0", "White wins"
        BLACK_WIN = "0-1", "Black wins"
        DRAW = "1/2-1/2", "Draw"

    white_player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="games_as_white"
    )

    black_player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="games_as_black"
    )

    result = models.CharField(
        max_length=7,
        choices=Result.choices,
        blank=True
    )

    played_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.white_player} vs {self.black_player} ({self.result}) round {self.round}"
    


    
