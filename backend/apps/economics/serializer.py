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
        instance = self.instance

        label = attrs.get(
            "label",
            instance.label if instance else None,
        )

        release = attrs.get(
            "release",
            instance.release if instance else None,
        )

        campaign = attrs.get(
            "campaign",
            instance.campaign if instance else None,
        )

        order = attrs.get(
            "order",
            instance.order if instance else None,
        )

        if label is None:
            raise serializers.ValidationError(
                {"label": "A label is required."}
            )

        if not Membership.objects.filter(
            user=self.context["request"].user,
            label=label,
        ).exists():
            raise serializers.ValidationError(
                {"label": "You do not have access to this label."}
            )

        if release and release.label_id != label.id:
            raise serializers.ValidationError(
                {"release": "This release does not belong to this label."}
            )

        if campaign:
            if campaign.release.label_id != label.id:
                raise serializers.ValidationError(
                    {"campaign": "This campaign does not belong to this label."}
                )

            if release and campaign.release_id != release.id:
                raise serializers.ValidationError(
                    {"campaign": "This campaign does not belong to this release."}
                )

        if order and order.label_id != label.id:
            raise serializers.ValidationError(
                {"order": "This order does not belong to this label."}
            )

        return attrs