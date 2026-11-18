from rest_framework import serializers
from .models import Label, Membership, Release, ReleaseFormat, Track, Contact, Order, OrderItem
from django.db import transaction

from collections import defaultdict
from decimal import Decimal

from django.db.models import F

class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = '__all__'



class MembershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Membership
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):

    total_cost = serializers.SerializerMethodField()
    cost_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Release
        fields = '__all__'

    def validate_label(self, value):
        if not Membership.objects.filter(user=self.context['request'].user, label=value,).exists():
            raise serializers.ValidationError('You do not have access to this label.')

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


    def get_cost_breakdown(self, obj):
        expenses = obj.transactions.filter(
        transaction_type="expense"
        )
        breakdown = {}


        for transaction in expenses:
            category = transaction.category
            currency = transaction.currency

            if category not in breakdown:
                breakdown[category] = {}

            if currency not in breakdown[category]:
                breakdown[category][currency] = 0

            breakdown[category][currency] += transaction.amount     

        return breakdown 

class ReleaseFormatSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReleaseFormat
        fields = '__all__'

    def validate_release(self, value):
        if not Membership.objects.filter(user=self.context['request'].user, label=value.label,).exists():
            raise serializers.ValidationError('You do not have access to this release')


        return value


class TrackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Track
        fields = '__all__'


    def validate_release(self, value):
        if not Membership.objects.filter(user=self.context['request'].user, label=value.label).exists():
            raise serializers.ValidationError('You do not have access to this release.')

        return value


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = '__all__'

    def validate_label(self, value):
        if not Membership.objects.filter(
            user=self.context["request"].user,
            label=value,
        ).exists():
            raise serializers.ValidationError(
                "You do not have access to this label."
            )

        return value


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    def validate_label(self, value):
            if not Membership.objects.filter(
                user=self.context["request"].user,
                label=value,
            ).exists():
                raise serializers.ValidationError(
                    "You do not have access to this label."
                )
    
            return value

    def validate(self, attrs):
        instance = self.instance

        label = attrs.get(
            "label",
            instance.label if instance else None
        )
        contact = attrs.get(
            "contact",
            instance.contact if instance else None
        )

        # Kontakt musi należeć do tego samego wydawnictwa.
        if contact and contact.label != label:
            raise serializers.ValidationError({
                "contact": "This contact does not belong to this label."
            })

        # Po opłaceniu zamówienia blokujemy zmianę
        # danych finansowych i identyfikacyjnych.
        if instance and instance.status == "paid":
            protected_fields = [
                "label",
                "contact",
                "order_date",
                "currency",
                "sales_channel",
                "external_id",
            ]

            for field in protected_fields:
                if field in attrs:
                    current_value = getattr(instance, field)
                    new_value = attrs[field]

                    if current_value != new_value:
                        raise serializers.ValidationError({
                            field: (
                                "This field cannot be changed "
                                "after the order has been paid."
                            )
                        })

        return attrs

    
    def update(self, instance, validated_data):
        from apps.economics.models import Transaction

        new_status = validated_data.get("status", instance.status)

        # Zwykłe aktualizacje obsługujemy bez księgowania sprzedaży.
        if new_status != "paid":
            return super().update(instance, validated_data)

        # Cały proces płatności musi być atomowy.
        with transaction.atomic():

            # Pobieramy aktualny Order i blokujemy go na czas operacji.
            order = Order.objects.select_for_update().get(
                pk=instance.pk
            )

            # Zamówienie już opłacone - bez ponownego księgowania.
            if order.status == "paid":
                return super().update(order, validated_data)

            # Zachowujemy dotychczasowe zabezpieczenie przed
            # ponownym odjęciem towaru i zaksięgowaniem sprzedaży.
            transaction_exists = Transaction.objects.filter(
                order=order
            ).exists()

            if transaction_exists:
                return super().update(order, validated_data)

            items = list(order.items.all())

            if not items:
                raise serializers.ValidationError({
                    "items": (
                        "Order must contain at least one item "
                        "before it can be paid."
                    )
                })

            required_stock = defaultdict(int)
            total_amount = Decimal("0.00")

            for item in items:
                if item.release_format_id is None:
                    raise serializers.ValidationError({
                        "stock": "Order item has no assigned release format."
                    })

                required_stock[item.release_format_id] += item.quantity
                total_amount += item.quantity * item.unit_price

            # Blokujemy formaty w stałej kolejności, aby ograniczyć
            # ryzyko zakleszczeń przy równoczesnych zamówieniach.
            formats = {
                release_format.pk: release_format
                for release_format in ReleaseFormat.objects
                    .select_for_update()
                    .filter(pk__in=required_stock.keys())
                    .order_by("pk")
            }

            # Kontrola całkowitego zapotrzebowania.
            for format_id, quantity in required_stock.items():
                release_format = formats.get(format_id)

                if release_format is None:
                    raise serializers.ValidationError({
                        "stock": "Release format no longer exists."
                    })

                if release_format.stock_quantity < quantity:
                    raise serializers.ValidationError({
                        "stock": (
                            f"Not enough stock for {release_format}. "
                            f"Available: {release_format.stock_quantity}, "
                            f"required: {quantity}."
                        )
                    })

            # Atomowe odejmowanie z dodatkowym warunkiem dostępności.
            for format_id, quantity in required_stock.items():
                updated = ReleaseFormat.objects.filter(
                    pk=format_id,
                    stock_quantity__gte=quantity,
                ).update(
                    stock_quantity=F("stock_quantity") - quantity
                )

                if updated != 1:
                    raise serializers.ValidationError({
                        "stock": (
                            "Stock changed during payment processing. "
                            "Please try again."
                        )
                    })

            # Zmieniamy status zamówienia.
            order = super().update(order, validated_data)

            # Tworzymy przychód tylko po udanym odjęciu towaru.
            Transaction.objects.create(
                label=order.label,
                order=order,
                transaction_type="income",
                category="sales",
                amount=total_amount,
                currency=order.currency,
                date=order.order_date,
                description=f"Sale from order #{order.id}",
            )

            return order


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = '__all__'
        extra_kwargs = {
        "unit_price": {"required": False},
    }

    def validate_order(self, value):
        if not Membership.objects.filter(
            user=self.context["request"].user,
            label=value.label,
        ).exists():
            raise serializers.ValidationError(
                "You do not have access to this order."
            )

        return value

    def validate(self, attrs):
        order = attrs.get("order")
        release_format = attrs.get("release_format")
         

        if order and release_format:
            if release_format.release.label != order.label:
                raise serializers.ValidationError(
                    {
                        "release_format":
                            "This release format does not belong to this order's label."
                    }
                )

        return attrs

    def create(self, validated_data):
        if 'unit_price' not in validated_data:
            release_format = validated_data['release_format']
            validated_data['unit_price'] = release_format.price
        return super().create(validated_data)