from django.db import models


class Players(models.Model):
    ktc_player_id = models.IntegerField(primary_key=True)
    player_name = models.CharField(max_length=255)
    sleeper_player_id = models.IntegerField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=32, null=True, blank=True)
    experience = models.CharField(max_length=32, null=True, blank=True)
    team = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.player_name


class KtcPlayerValues(models.Model):
    ktc_player_id = models.ForeignKey(Players, to_field='ktc_player_id', on_delete=models.CASCADE, db_column='ktc_player_id')
    ktc_value = models.IntegerField(db_column='ktc_value')
    date = models.DateField(db_column='date')

    class Meta:
        unique_together = (('ktc_player_id', 'date'),)

    def __str__(self):
        return f"{self.player} - {self.ktc_value} on {self.date}"
