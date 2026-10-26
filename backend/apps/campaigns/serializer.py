from rest_framework import serializers

from apps.campaigns.models import Campaign


class CampaignSerializer(serializers.ModelSerializer):

    class Meta:
        model = Campaign
        fields = '__all__'


    def validate_release(self, value):
        user = self.context['request'].user

        if not value.label.memberships.filter(user=user).exists():
            raise serializers.ValidationError('"You do not have access to this release."')


        return value