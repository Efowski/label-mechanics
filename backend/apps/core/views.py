from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from .serializer import (LabelSerializer,
                          MembershipSerializer, ReleaseSerializer, ReleaseFormatSerializer, TrackSerializer,
                          ContactSerializer, OrderSerializer, OrderItemSerializer)
from .models import Label, Membership, UserRole, Release, ReleaseFormat, Track, Contact, Order, OrderItem


class LabelViewSet(viewsets.ModelViewSet):
     
    serializer_class = LabelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return  Label.objects.filter(memberships__user=self.request.user).distinct()
 

    def perform_create(self, serializer):
        label = serializer.save()

        Membership.objects.create(user=self.request.user, label=label, role=UserRole.LABEL_OWNER)


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


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(
            order__label__memberships__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        order = serializer.validated_data["order"]

        if order.status == "paid":
            raise serializers.ValidationError({
                "order": "Cannot add items to a paid order."
            })

        serializer.save()

    def perform_update(self, serializer):
        order = serializer.instance.order

        if order.status == "paid":
            raise serializers.ValidationError({
                "order": "Cannot modify items of a paid order."
            })

        # Nie pozwalamy również przenosić pozycji
        # do już opłaconego zamówienia.
        new_order = serializer.validated_data.get("order")

        if new_order and new_order.status == "paid":
            raise serializers.ValidationError({
                "order": "Cannot move items to a paid order."
            })

        serializer.save()

    def perform_destroy(self, instance):
        if instance.order.status == "paid":
            raise serializers.ValidationError({
                "order": "Cannot delete items from a paid order."
            })

        instance.delete()


   