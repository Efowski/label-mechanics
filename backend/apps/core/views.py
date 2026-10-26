from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
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