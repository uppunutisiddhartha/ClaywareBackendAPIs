from rest_framework import serializers

from .models import CustomUser, Seller, DeliveryPartner


# ---------------------------------------------------------
# Register Serializer
# ---------------------------------------------------------

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:

        model = CustomUser

        fields = [

            'email',
            'phone_number',
            'password',
            'role',

            'profile_image',


            # Seller Fields
            'shop_name',
            'shop_address',
            'gst_number',
            'id_proof',

            # Delivery Partner Fields
            'vehicle_type',
            'vehicle_number',
            'license_number',
            'RcImage',
            'licenseImage',
        ]

        extra_kwargs = {
            'password': {'write_only': True}
        }

    # -----------------------------------------------------
    # Extra Fields
    # -----------------------------------------------------

    shop_name = serializers.CharField(required=False)

    shop_address = serializers.CharField(required=False)

    gst_number = serializers.CharField(required=False)

    id_proof = serializers.ImageField(required=False)

    vehicle_type = serializers.CharField(required=False)

    vehicle_number = serializers.CharField(required=False)

    license_number = serializers.CharField(required=False)

    RcImage = serializers.ImageField(required=False)

    licenseImage = serializers.ImageField(required=False)

    # -----------------------------------------------------
    # Create User
    # -----------------------------------------------------

    def create(self, validated_data):

        role = validated_data.get('role')

        # -------------------------------------------------
        # Remove Extra Fields
        # -------------------------------------------------

        seller_data = {

            'shop_name': validated_data.pop('shop_name', None),

            'shop_address': validated_data.pop('shop_address', None),

            'gst_number': validated_data.pop('gst_number', None),

            'id_proof': validated_data.pop('id_proof', None),

        }

        delivery_data = {

            'vehicle_type': validated_data.pop('vehicle_type', None),

            'vehicle_number': validated_data.pop('vehicle_number', None),

            'license_number': validated_data.pop('license_number', None),

            'RcImage': validated_data.pop('RcImage', None),

            'licenseImage': validated_data.pop('licenseImage', None),

        }

        password = validated_data.pop('password')

        # -------------------------------------------------
        # Create User
        # -------------------------------------------------

        user = CustomUser(**validated_data)

        user.set_password(password)

        user.save()

        # -------------------------------------------------
        # Seller Profile
        # -------------------------------------------------

        if role == 'seller':

            Seller.objects.create(

                user=user,

                shop_name=seller_data['shop_name'],

                shop_address=seller_data['shop_address'],

                gst_number=seller_data['gst_number'],

                id_proof=seller_data['id_proof']

            )

        # -------------------------------------------------
        # Delivery Partner Profile
        # -------------------------------------------------

        elif role == 'delivery_partner':

            DeliveryPartner.objects.create(

                user=user,

                vehicle_type=delivery_data['vehicle_type'],

                vehicle_number=delivery_data['vehicle_number'],

                address=delivery_data['address'],

                license_number=delivery_data['license_number'],

                RcImage=delivery_data['RcImage'],

                licenseImage=delivery_data['licenseImage']

            )

        return user


# ---------------------------------------------------------
# Login Serializer
# ---------------------------------------------------------

class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()

    password = serializers.CharField(write_only=True)