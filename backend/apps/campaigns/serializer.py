from rest_framework import serializers

from apps.campaigns.models import Campaign, CampaignMetric, Coverage



class CampaignMetricSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CampaignMetric
        fields = '__all__'

    def validate_campaign(self, value):
        user = self.context['request'].user

        if not value.release.label.memberships.filter(user=user).exists():
            raise serializers.ValidationError("You do not have access to this campaign.")

        return value


class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage
        fields = '__all__'

    def validate_campaign(self, value):
        user = self.context['request'].user

        if not value.release.label.memberships.filter(user=user).exists():
            raise serializers.ValidationError('You do not have access to this campaign.')

        return value


class CampaignSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()
    metrics = CampaignMetricSerializer(many=True, read_only=True,)
    coverage = CoverageSerializer(many=True, read_only=True,)

    class Meta:
        model = Campaign
        fields = "__all__"

    def validate_release(self, value):
        user = self.context["request"].user

        if not value.label.memberships.filter(user=user).exists():
            raise serializers.ValidationError(
                "You do not have access to this release."
            )

        return value

    def get_total_cost(self, obj):
        expenses = obj.transactions.filter(
            transaction_type="expense"
        )

        totals = {}

        for transaction in expenses:
            currency = transaction.currency

            if currency not in totals:
                totals[currency] = 0

            totals[currency] += transaction.amount

        return totals


