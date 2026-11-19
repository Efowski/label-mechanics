from django.shortcuts import render
from django.db import transaction
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers



from .serializer import (LabelSerializer,
                          MembershipSerializer, ReleaseSerializer, ReleaseFormatSerializer, TrackSerializer,
                          ContactSerializer, OrderSerializer, OrderItemSerializer)
from .models import Label, Membership, UserRole, Release, ReleaseFormat, Track, Contact, Order, OrderItem
from .permissions import IsLabelOwnerOrReadOnly




class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    permission_classes = [
        IsAuthenticated,
        IsLabelOwnerOrReadOnly,
    ]

    def get_queryset(self):
        return Label.objects.filter(
            memberships__user=self.request.user
        ).distinct()

    @transaction.atomic
    def perform_create(self, serializer):
        label = serializer.save()

        Membership.objects.create(
            user=self.request.user,
            label=label,
            role=UserRole.LABEL_OWNER,
        )

class ReleaseViewSet(viewsets.ModelViewSet):
    serializer_class = ReleaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Release.objects.filter(label__memberships__user=self.request.user).distinct()


class ReleaseFormatViewSet(viewsets.ModelViewSet):
    serializer_class = ReleaseFormatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReleaseFormat.objects.filter(release__label__memberships__user=self.request.user).distinct()


class TrackViewSet(viewsets.ModelViewSet):
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Track.objects.filter(release__label__memberships__user=self.request.user).distinct()


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(
            label__memberships__user=self.request.user
        ).distinct()


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(label__memberships__user=self.request.user).distinct()



LOCKED_ORDER_STATUSES = {
    "paid",
    "shipped",
    "completed",
}

class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(
            order__label__memberships__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        order = serializer.validated_data["order"]

        if order.status in LOCKED_ORDER_STATUSES:
            raise serializers.ValidationError({
                "order": (
                    "Cannot add items to a paid, shipped "
                    "or completed order."
                )
            })

        serializer.save()

    def perform_update(self, serializer):
        order = serializer.instance.order

        # Nie pozwalamy edytować pozycji zamówienia,
        # które zostało już opłacone lub zrealizowane.
        if order.status in LOCKED_ORDER_STATUSES:
            raise serializers.ValidationError({
                "order": (
                    "Cannot modify items of a paid, shipped "
                    "or completed order."
                )
            })

        # Nie pozwalamy również przenosić pozycji
        # do zamówienia o zablokowanym statusie.
        new_order = serializer.validated_data.get("order")

        if (
            new_order
            and new_order.status in LOCKED_ORDER_STATUSES
        ):
            raise serializers.ValidationError({
                "order": (
                    "Cannot move items to a paid, shipped "
                    "or completed order."
                )
            })

        serializer.save()

    def perform_destroy(self, instance):
        # Nie pozwalamy usuwać pozycji zamówienia,
        # które zostało już opłacone lub zrealizowane.
        if instance.order.status in LOCKED_ORDER_STATUSES:
            raise serializers.ValidationError({
                "order": (
                    "Cannot delete items from a paid, shipped "
                    "or completed order."
                )
            })

        instance.delete()