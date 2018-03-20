from django.conf import settings
from django.db import models


class HPCInfrastructure(models.Model):
    name = models.CharField(max_length=50)

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
        return "{0}: HPC at {1} from {2}({3})".format(
            self.name,
            self.host,
            self.owner.username,
            self.user)

    def to_dict(self):
        return {
            'credentials': {
                'host': self.host,
                'user': self.user,
                'password': self.password,
            },
            'country_tz': self.time_zone,
            'workload_manager': self.manager
        }
