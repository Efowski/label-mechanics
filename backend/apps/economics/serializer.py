from rest_framework import serializers

from apps.core.models import Membership

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

    def validate_label(self, value):
        if not Membership.objects.filter(
            user=self.context["request"].user,
            label=value,
        ).exists():
            raise serializers.ValidationError(
                "You do not have access to this label."
            )

        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )

        return value


    def validate(self, attrs):
        label = attrs.get("label")
        release = attrs.get("release")
        campaign = attrs.get("campaign")

        if release and release.label != label:
            raise serializers.ValidationError(
                {
                    "release": "This release does not belong to this label."
                }
            )

        if campaign and campaign.release.label != label:
            raise serializers.ValidationError(
                {
                    "campaign": "This campaign does not belong to this label."
                }
            )

        if campaign and release and campaign.release != release:
            raise serializers.ValidationError(
                {
                    "campaign": "This campaign does not belong to this release."
                }
            )

        return attrs
        