from django.db import models
from apps.core.models import Release


class Campaign(models.Model):
    class CampaignType(models.TextChoices):
        SOCIAL = "social", "Social media"
        PAID_ADS = "paid_ads", "Paid advertising"
        OUTREACH = "outreach", "Promo outreach"
        OTHER = "other", "Other"
    campaign_type = models.CharField(max_length=40, choices=CampaignType.choices, default=CampaignType.OTHER)
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


class CampaignMetric(models.Model):
    class MetricType(models.TextChoices):
        VIEWS = "views", "Views"
        CLICKS = "clicks", "Clicks"
        REACH = "reach", "Reach"
        PROMOS_SENT = "promos_sent", "Promos sent"
        RESPONSES = "responses", "Responses"
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="metrics",)
    metric_type = models.CharField(max_length=50, choices=MetricType.choices,)

    value = models.DecimalField(max_digits=12, decimal_places=2,)


    def __str__(self):
        return f"{self.campaign.name} - {self.metric_type}: {self.value}"



class Coverage(models.Model):
    class CoverageType(models.TextChoices):
        ONLINE_REVIEW = "online_review", "Online review"
        PRINT_REVIEW = "print_review", "Print review"
        INTERVIEW = "interview", "Interview"
        FEATURE = "feature", "Feature"
        OTHER = "other", "Other"
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='coverage')
    coverage_type = models.CharField(max_length=30, choices=CoverageType.choices)
    publication = models.CharField(max_length=200)
    title = models.CharField(max_length=250, blank=True)
    url = models.URLField()
    published_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.publication} - {self.campaign.name}"