from django.db import models
from apps.core.models import Release


class Campaign(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=250)
    channel = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    goal = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


