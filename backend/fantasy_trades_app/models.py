from django.db import models

class Players(models.Model):
    player_id = models.AutoField(primary_key=True)
    player_name = models.CharField(max_length=255)

    def __str__(self):
        return self.player_name

class PlayerValues(models.Model):
    player = models.ForeignKey(Players, on_delete=models.CASCADE)  # Use 'player' instead of 'player_id'
    ktc_value = models.IntegerField()
    date = models.DateField()

    class Meta:
        unique_together = (('player', 'date'),)  # Ensure consistency in the unique constraint

    def __str__(self):
        return f"{self.player} - {self.ktc_value} on {self.date}"
