from django.conf import settings
from django.db import models


class HPCInfrastructure(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    host = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    time_zone = models.CharField(max_length=20)

    SLURM = 'SLURM'
    MANAGER_CHOICES = (
        (SLURM, 'Slurm'),
    )
    manager = models.CharField(
        max_length=5,
        choices=MANAGER_CHOICES,
        default=SLURM,
    )

    def __str__(self):
        return format("HPC at %s from %s(%s)",
                      self.host,
                      self.owner.name,
                      self.user)
