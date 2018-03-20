from django.conf import settings
from django.db import models


class RemoteDesktopInfrastructure(models.Model):
    name = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    host = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    list_cmd = models.CharField(max_length=50)
    create_cmd = models.CharField(max_length=50)

    NOVNC = 'noVNC'
    RD_CHOICES = (
        (NOVNC, 'noVNC'),
    )
    rd_tool = models.CharField(
        max_length=5,
        choices=RD_CHOICES,
        default=NOVNC,
    )

    def __str__(self):
        return "{0}: Remote Desktop at {1} from {2}({3})".format(
            self.name,
            self.host,
            self.owner.username,
            self.user)
