from django.db import transaction
from django.contrib.auth import logout
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import SellerPickupLocation
from .serializers import SellerPickupLocationSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from seller.models import Product,ProductVariant, ProductImage

def get_variant_stock(variant):
    try:
        return variant.inventory.quantity
    except ProductVariant.inventory.RelatedObjectDoesNotExist:
        return 0


def get_product_stock(product):
    try:
        return product.inventory.quantity
    except Product.inventory.RelatedObjectDoesNotExist:
        return 0


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

from .models import (
        CustomUser,
        Seller,
        DeliveryPartner,
    )

from .utils import (
        send_otp,
        verify_otp,
    )

    # ==========================================================
    # HOME PAGE API
    # ==========================================================
class HomePageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        products = Product.objects.filter(
            status="approved"
        ).prefetch_related("variants", "images")

        data = []

        for product in products:

            variants = []

            total_stock = 0

            for variant in product.variants.all():

                #total_stock += variant.stock_quantity or 0
                try:
                    total_stock += variant.inventory.quantity
                except ProductVariant.inventory.RelatedObjectDoesNotExist:
                    total_stock += 0
                

                variants.append({
                    "id": variant.id,
                    "capacity": variant.capacity,
                    "price": str(variant.price),
                    "discount_price": (
                        str(variant.discount_price)
                        if variant.discount_price is not None
                        else None
                    ),
                   # "stock_quantity": variant.stock_quantity,
                   "stock_quantity": (
                        variant.inventory.quantity
                        if hasattr(variant, "inventory")
                        else 0
                    ),
                })

            images = []

            for image in product.images.all():

                images.append({
                    "id": image.id,
                    "image": request.build_absolute_uri(
                        image.image.url
                    )
                })

            main_image = images[0]["image"] if images else None

            data.append({

                "id": product.id,

                "productname": product.productname,

                "description": product.description,

                "price": str(product.price),

                "discount_price": (
                    str(product.discount_price)
                    if product.discount_price is not None
                    else None
                ),

                # Stock comes from variants
                "stock_quantity": total_stock,

                "weight": product.weight,

                "capacity": product.capacity,

                "category": product.category,

                "seller": product.seller.shop_name,

                "image": main_image,

                "images": images,

                "variants": variants,
            })

        return Response(
            {
                "total_products": products.count(),
                "products": data,
            },
            status=status.HTTP_200_OK,
        )

        
    # ==========================================================
    # PRODUCT DETAILS
    # ==========================================================
class ProductDetailsAPI(APIView):

    permission_classes = [AllowAny]

    def get(self, request, id):

        try:
            product = (
                Product.objects
                .prefetch_related(
                    "variants__inventory",
                    "images"
                )
                .select_related(
                    "seller__user"
                )
                .get(
                    id=id,
                    status="approved"
                )
            )

        except Product.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Product not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==========================
        # Product Images
        # ==========================

        images = []

        for image in product.images.all():

            images.append(
                request.build_absolute_uri(
                    image.image.url
                )
            )

        # ==========================
        # Variants
        # ==========================

        variants = []

        total_stock = 0

        for variant in product.variants.all():

            try:
                stock = variant.inventory.quantity

            except ProductVariant.inventory.RelatedObjectDoesNotExist:
                stock = 0

            total_stock += stock

            variants.append({

                "id": variant.id,

                "capacity": variant.capacity,

                "price": str(
                    variant.price
                ),

                "discount_price": (
                    str(variant.discount_price)
                    if variant.discount_price is not None
                    else None
                ),

                "stock_quantity": stock,

            })

        # ==========================
        # Product Inventory
        # ==========================

        if not variants:

            try:
                total_stock = product.inventory.quantity

            except Product.inventory.RelatedObjectDoesNotExist:
                total_stock = 0

        # ==========================
        # Seller
        # ==========================

        seller_name = None

        if product.seller:

            seller_name = (
                product.seller.shop_name
            )

        # ==========================
        # Product Data
        # ==========================

        data = {

            "id": product.id,

            "productname":
                product.productname,

            "description":
                product.description,

            "price":
                str(product.price),

            "discount_price": (
                str(product.discount_price)
                if product.discount_price is not None
                else None
            ),

            "stock_quantity":
                total_stock,

            "weight":
                product.weight,

            "capacity":
                product.capacity,

            "category":
                product.category,

            "seller":
                seller_name,

            "images":
                images,

            "variants":
                variants,

        }

        return Response(
            data,
            status=status.HTTP_200_OK
        )

    
    # ==========================================================
    # CHECK PHONE
    # ==========================================================

class CheckPhoneAPIView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):

            phone_number = request.data.get("phone_number")

            if not phone_number:

                return Response(

                    {

                        "success": False,

                        "message": "Phone number is required."

                    },

                    status=status.HTTP_400_BAD_REQUEST

                )

            user = CustomUser.objects.filter(

                phone_number=phone_number,

                role="user"

            ).first()

            if user:

                return Response(

                    {

                        "success": True,

                        "is_new_user": False,

                        "message": "Existing user."

                    },

                    status=status.HTTP_200_OK

                )

            return Response(

                {

                    "success": True,

                    "is_new_user": True,

                    "message": "New user."

                },

                status=status.HTTP_200_OK

            )

    # ==========================================================
    # SEND OTP
    # ==========================================================

class SendOTPAPIView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):

            phone_number = request.data.get("phone_number")

            if not phone_number:

                return Response(

                    {

                        "success": False,

                        "message": "Phone number is required."

                    },

                    status=status.HTTP_400_BAD_REQUEST

                )

            try:

                result = send_otp(phone_number)

                if result == "pending":

                    return Response(

                        {

                            "success": True,

                            "message": "OTP sent successfully."

                        },

                        status=status.HTTP_200_OK

                    )

                return Response(

                    {

                        "success": False,

                        "message": "Unable to send OTP."

                    },

                    status=status.HTTP_400_BAD_REQUEST

                )

            except Exception as e:

                return Response(

                    {

                        "success": False,

                        "message": str(e)

                    },

                    status=status.HTTP_500_INTERNAL_SERVER_ERROR

                )
            
    # ==========================================================
    # VERIFY OTP
    # ==========================================================

class VerifyOTPAPIView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):

            phone_number = request.data.get("phone_number")
            otp = request.data.get("otp")

            if not phone_number or not otp:
                return Response(
                    {
                        "success": False,
                        "message": "Phone number and OTP are required."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:

                status_result = verify_otp(phone_number, otp)

                if status_result != "approved":

                    return Response(
                        {
                            "success": False,
                            "message": "Invalid OTP."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Existing user
                user = CustomUser.objects.filter(
                    phone_number=phone_number
                ).first()

                if user:

                    # Seller / Delivery Partner Approval Check
                    if (
                        user.role in ["seller", "delivery_partner"]
                        and user.account_status == "pending"
                    ):
                        return Response(
                            {
                                "success": False,
                                "message": "Your account is under review.",
                                "role": user.role
                            },
                            status=status.HTTP_403_FORBIDDEN
                        )

                    if user.account_status == "suspended":
                        return Response(
                            {
                                "success": False,
                                "message": "Your account has been suspended."
                            },
                            status=status.HTTP_403_FORBIDDEN
                        )

                    tokens = get_tokens_for_user(user)

                    return Response(
                    {
                        "success": True,
                        "message": "Login successful.",

                        "access": tokens["access"],
                        "refresh": tokens["refresh"],

                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "role": user.role,
                        "account_status": user.account_status,
                    },
                    status=status.HTTP_200_OK
                )

                                # New user
                return Response(
                    {
                        "success": True,
                        "registered": False,
                        "message": "OTP verified. Complete registration."
                    },
                    status=status.HTTP_200_OK
                )

            except Exception as e:

                return Response(
                    {
                        "success": False,
                        "message": str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    # ==========================================================
    # COMPLETE REGISTRATION
    # ==========================================================

class CompleteRegistrationAPIView(APIView):
        permission_classes = [AllowAny]

        @transaction.atomic
        def post(self, request):

            name = request.data.get("name")
            phone_number = request.data.get("phone_number")
            password = request.data.get("password")
            email = request.data.get("email")

            if not name:
                return Response(
                    {
                        "success": False,
                        "message": "Name is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not phone_number:
                return Response(
                    {
                        "success": False,
                        "message": "Phone number is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not password:
                return Response(
                    {
                        "success": False,
                        "message": "Password is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():

                return Response(
                    {
                        "success": False,
                        "message": "Phone number already registered."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Optional Email
            if email:

                if CustomUser.objects.filter(email=email).exists():

                    return Response(
                        {
                            "success": False,
                            "message": "Email already exists."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            else:

                # Required because email field is unique
                email = f"{phone_number}@clayware.local"

            user = CustomUser.objects.create(

                name=name,

                email=email,

                phone_number=phone_number,

                role="user",

                account_status="active",

            )

            user.set_password(password)

            user.save()

            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "success": True,
                    "message": "Registration completed successfully.",
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                    "role": user.role,
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                },
                status=status.HTTP_201_CREATED
            )
        

    # ==========================================================
    # SELLER REGISTRATION
    # ==========================================================
class SellerRegisterAPIView(APIView):

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):

        data = request.data

        # ======================================================
        # GET DATA
        # ======================================================

        name = data.get("name")
        email = data.get("email")
        phone_number = data.get("phone_number")
        password = data.get("password")

        shop_name = data.get("shop_name")
        shop_address = data.get("shop_address")
        gst_number = data.get("gst_number")
        id_proof = data.get("id_proof")

        # ======================================================
        # VALIDATION
        # ======================================================

        if not name:
            return Response(
                {
                    "success": False,
                    "field": "name",
                    "message": "Full name is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not email:
            return Response(
                {
                    "success": False,
                    "field": "email",
                    "message": "Email is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not phone_number:
            return Response(
                {
                    "success": False,
                    "field": "phone_number",
                    "message": "Phone number is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not password:
            return Response(
                {
                    "success": False,
                    "field": "password",
                    "message": "Password is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 8:
            return Response(
                {
                    "success": False,
                    "field": "password",
                    "message": "Password must contain at least 8 characters."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not shop_name:
            return Response(
                {
                    "success": False,
                    "field": "shop_name",
                    "message": "Shop name is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not shop_address:
            return Response(
                {
                    "success": False,
                    "field": "shop_address",
                    "message": "Shop address is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not id_proof:
            return Response(
                {
                    "success": False,
                    "field": "id_proof",
                    "message": "ID proof is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ======================================================
        # DUPLICATE EMAIL
        # ======================================================

        if CustomUser.objects.filter(email=email).exists():

            return Response(
                {
                    "success": False,
                    "field": "email",
                    "message": "This email is already registered."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ======================================================
        # DUPLICATE PHONE
        # ======================================================

        if CustomUser.objects.filter(
            phone_number=phone_number
        ).exists():

            return Response(
                {
                    "success": False,
                    "field": "phone_number",
                    "message": "This phone number is already registered."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ======================================================
        # DUPLICATE GST
        # ======================================================

        if gst_number:

            if Seller.objects.filter(
                gst_number=gst_number
            ).exists():

                return Response(
                    {
                        "success": False,
                        "field": "gst_number",
                        "message": "This GST number is already registered."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ======================================================
        # CREATE USER
        # ======================================================

        try:

            user = CustomUser.objects.create(
                name=name,
                email=email,
                phone_number=phone_number,
                role="seller",
                account_status="pending"
            )

            user.set_password(password)
            user.save()

            # ==================================================
            # CREATE SELLER PROFILE
            # ==================================================

            seller = Seller.objects.create(
                user=user,
                shop_name=shop_name,
                shop_address=shop_address,
                gst_number=gst_number or None,
                id_proof=id_proof
            )

        except Exception as e:

            # This will appear in Django console
            print(
                "SELLER REGISTRATION ERROR:",
                str(e)
            )

            return Response(
                {
                    "success": False,
                    "message": "Unable to create seller account.",
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ======================================================
        # SUCCESS
        # ======================================================

        return Response(
            {
                "success": True,

                "message":
                    "Seller registration submitted successfully.",

                "status":
                    "pending",

                "role":
                    "seller",

                "note":
                    "Your account is under verification. "
                    "Please wait for admin approval."
            },
            status=status.HTTP_201_CREATED
        )



class SellerPickupLocationAPI(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]

    # ======================================================
    # GET PICKUP LOCATION
    # ======================================================

    def get(self, request):

        try:

            seller = request.user.seller_profile

        except AttributeError:

            return Response(
                {
                    "message": "Seller profile not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            location = SellerPickupLocation.objects.get(
                seller=seller
            )

        except SellerPickupLocation.DoesNotExist:

            return Response(
                {
                    "exists": False,
                    "message": "Pickup location not configured."
                },
                status=status.HTTP_200_OK
            )

        serializer = SellerPickupLocationSerializer(
            location
        )

        return Response(
            {
                "exists": True,
                "location": serializer.data
            },
            status=status.HTTP_200_OK
        )

    # ======================================================
    # CREATE / UPDATE PICKUP LOCATION
    # ======================================================

    def post(self, request):

        try:

            seller = request.user.seller_profile

        except AttributeError:

            return Response(
                {
                    "message": "Seller profile not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        location = (
            SellerPickupLocation.objects
            .filter(seller=seller)
            .first()
        )

        if location:

            serializer = SellerPickupLocationSerializer(
                location,
                data=request.data,
                partial=True
            )

        else:

            serializer = SellerPickupLocationSerializer(
                data=request.data
            )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        location = serializer.save(
            seller=seller
        )

        return Response(
            {
                "message":
                    "Pickup location saved successfully.",

                "location":
                    SellerPickupLocationSerializer(
                        location
                    ).data
            },
            status=status.HTTP_200_OK
        )

     # ==========================================================
    # DELIVERY PARTNER REGISTRATION
    # ==========================================================

class DeliveryPartnerRegisterAPIView(APIView):
        permission_classes = [AllowAny]

        @transaction.atomic
        def post(self, request):

            data = request.data

            name = data.get("name")
            email = data.get("email")
            phone_number = data.get("phone_number")
            password = data.get("password")

            vehicle_type = data.get("vehicle_type")
            vehicle_number = data.get("vehicle_number")
            address = data.get("address")
            license_number = data.get("license_number")
            RcImage = data.get("RcImage")
            licenseImage = data.get("licenseImage")

            # ------------------------------------
            # Validation
            # ------------------------------------

            if not name:
                return Response(
                    {"message": "Name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not email:
                return Response(
                    {"message": "Email is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not phone_number:
                return Response(
                    {"message": "Phone number is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not password:
                return Response(
                    {"message": "Password is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {"message": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "Phone number already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if DeliveryPartner.objects.filter(vehicle_number=vehicle_number).exists():
                return Response(
                    {"message": "Vehicle number already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if DeliveryPartner.objects.filter(license_number=license_number).exists():
                return Response(
                    {"message": "License number already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------
            # Create User
            # ------------------------------------

            user = CustomUser.objects.create(

                name=name,

                email=email,

                phone_number=phone_number,

                role="delivery_partner",

                account_status="pending"

            )

            user.set_password(password)

            user.save()

            # ------------------------------------
            # Delivery Profile
            # ------------------------------------

            DeliveryPartner.objects.create(

                user=user,

                vehicle_type=vehicle_type,

                vehicle_number=vehicle_number,

                address=address,

                license_number=license_number,

                RcImage=RcImage,

                licenseImage=licenseImage

            )

            return Response(

                {

                    "success": True,

                    "message": "Delivery Partner registration submitted successfully.",

                    "status": "pending",

                    "note": "Wait for admin approval before login."

                },

                status=status.HTTP_201_CREATED

            )
        

    # ==========================================================
    # MARKETING REGISTRATION
    # ==========================================================

class MarketingRegisterAPIView(APIView):
        permission_classes = [AllowAny]

        @transaction.atomic
        def post(self, request):

            data = request.data

            name = data.get("name")
            email = data.get("email")
            phone_number = data.get("phone_number")
            password = data.get("password")

            if not name:
                return Response(
                    {"message": "Name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not email:
                return Response(
                    {"message": "Email is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not phone_number:
                return Response(
                    {"message": "Phone number is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not password:
                return Response(
                    {"message": "Password is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {"message": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "Phone number already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = CustomUser.objects.create(

                name=name,

                email=email,

                phone_number=phone_number,

                role="marketing",

                account_status="pending"

            )

            user.set_password(password)

            user.save()

            return Response(

                {

                    "success": True,

                    "message": "Marketing registration submitted successfully.",

                    "status": "pending",

                    "note": "Wait for admin approval before login."

                },

                status=status.HTTP_201_CREATED

            )


    # ==========================================================
    # ADMIN REGISTRATION
    # ==========================================================

class AdminRegisterAPIView(APIView):
        permission_classes = [AllowAny]

        @transaction.atomic
        def post(self, request):

            data = request.data

            name = data.get("name")
            email = data.get("email")
            phone_number = data.get("phone_number")
            password = data.get("password")

            if not name:
                return Response(
                    {"message": "Name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not email:
                return Response(
                    {"message": "Email is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not phone_number:
                return Response(
                    {"message": "Phone number is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not password:
                return Response(
                    {"message": "Password is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {"message": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "Phone number already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = CustomUser.objects.create(

                name=name,

                email=email,

                phone_number=phone_number,

                role="admin",

                account_status="active",

                is_staff=True,

                is_superuser=True

            )

            user.set_password(password)

            user.save()

            tokens = get_tokens_for_user(user)
            return Response(

                {

                    "success": True,

                    "message": "Admin registered successfully.",

                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                    "role": user.role,

                    "name": user.name,

                    "email": user.email,

                    "phone_number": user.phone_number

                },

                status=status.HTTP_201_CREATED

            )
        



    # ==========================================================
    # LOGIN
    # Seller / Delivery / Marketing / Admin
    # (Email OR Phone + Password)
    # ==========================================================

class LoginAPIView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):

            identifier = (
                request.data.get("email")
                or request.data.get("phone_number")
            )

            password = request.data.get("password")

            if not identifier or not password:

                return Response(
                    {
                        "success": False,
                        "message": "Email/Phone number and password are required."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------
            # Find User
            # ------------------------------------

            if "@" in identifier:

                user = CustomUser.objects.filter(
                    email=identifier
                ).first()

            else:

                user = CustomUser.objects.filter(
                    phone_number=identifier
                ).first()

            if not user:

                return Response(
                    {
                        "success": False,
                        "message": "User not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # ------------------------------------
            # Customer uses OTP Login
            # ------------------------------------

            if user.role == "user":

                return Response(
                    {
                        "success": False,
                        "message": "Customers must login using OTP."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # ------------------------------------
            # Password Check
            # ------------------------------------

            if not user.check_password(password):

                return Response(
                    {
                        "success": False,
                        "message": "Invalid password."
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # ------------------------------------
            # Pending Approval
            # ------------------------------------

            if user.account_status == "pending":

                return Response(
                    {
                        "success": False,
                        "message": "Your account is under review. Please wait for admin approval.",
                        "status": user.account_status
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # ------------------------------------
            # Suspended
            # ------------------------------------

            if user.account_status == "suspended":

                return Response(
                    {
                        "success": False,
                        "message": "Your account has been suspended."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # ------------------------------------
            # Login Success
            # ------------------------------------
# Login Success

            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "success": True,
                    "message": "Login successful.",

                    "access": tokens["access"],
                    "refresh": tokens["refresh"],

                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "account_status": user.account_status,
                },
                status=status.HTTP_200_OK
            )

    # ==========================================================
    # LOGOUT
    # ==========================================================
class LogoutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {
                "success": True,
                "message": "Logged out successfully."
            },
            status=status.HTTP_200_OK
        )

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "account_status": user.account_status,
        })