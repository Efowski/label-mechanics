from rest_framework import serializers
from .models import Label, Membership, Release, ReleaseFormat, Track, Contact, Order, OrderItem
from django.db import transaction

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
        label = attrs.get('label')
        contact = attrs.get('contact')
        if contact and contact.label != label:
            raise serializers.ValidationError( {
                    "contact": "This contact does not belong to this label."
                })

        return attrs

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", instance.status)

        # Specjalna logika tylko przy przejściu na "paid"
        if old_status != "paid" and new_status == "paid":

            # Order nie może być pusty
            if not instance.items.exists():
                raise serializers.ValidationError({
                    "items": (
                        "Order must contain at least one item "
                        "before it can be paid."
                    )
                })

            # Sprawdzamy stock wszystkich pozycji
            for item in instance.items.all():
                if item.release_format.stock_quantity < item.quantity:
                    raise serializers.ValidationError({
                        "stock": (
                            f"Not enough stock for {item.release_format}. "
                            f"Available: "
                            f"{item.release_format.stock_quantity}, "
                            f"required: {item.quantity}."
                        )
                    })

            from apps.economics.models import Transaction

            # Order + stock + Transaction są jedną operacją
            with transaction.atomic():

                # Aktualizujemy Order
                order = super().update(instance, validated_data)

                transaction_exists = Transaction.objects.filter(
                    order=order
                ).exists()

                # Jeżeli Order nie był wcześniej zaksięgowany
                if not transaction_exists:

                    # Odejmujemy sprzedane egzemplarze ze stocku
                    for item in order.items.all():
                        release_format = item.release_format
                        release_format.stock_quantity -= item.quantity
                        release_format.save(
                            update_fields=["stock_quantity"]
                        )

                    # Liczymy wartość całego Ordera
                    total_amount = sum(
                        item.quantity * item.unit_price
                        for item in order.items.all()
                    )

                    # Tworzymy przychód
                    Transaction.objects.create(
                        label=order.label,
                        order=order,
                        transaction_type="income",
                        category="sales",
                        amount=total_amount,
                        currency=order.label.currency,
                        date=order.order_date,
                        description=f"Sale from order #{order.id}",
                    )

                return order

        # Wszystkie inne zmiany Ordera
        return super().update(instance, validated_data)


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