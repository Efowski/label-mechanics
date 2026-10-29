from rest_framework import serializers

from apps.campaigns.models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()

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