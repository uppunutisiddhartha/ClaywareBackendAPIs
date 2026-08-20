import json

from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from accounts.models import Seller
from orders.models import Order

from .models import (
    Product,
    ProductVariant,
    ProductImage,
    Inventory,
)

from .permissions import IsSeller
from seller.serializers import ProductSerializer

from product_reviews.services import assign_product_to_reviewer


# ==========================================================
# ADD PRODUCT
# ==========================================================

class AddProductAPI(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSeller]

    def post(self, request):

        try:
            seller = request.user.seller_profile

        except Seller.DoesNotExist:

            return Response(
                {
                    "message":
                        "Seller profile does not exist."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # --------------------------------------------------
        # CREATE PRODUCT
        # --------------------------------------------------

        product = Product.objects.create(
            seller=seller,
            productname=request.data.get(
                "productname"
            ),
            description=request.data.get(
                "description"
            ),
            price=request.data.get(
                "price"
            ),
            category=request.data.get(
                "category"
            ),
            discount_price=request.data.get(
                "discount_price"
            ),
            weight=request.data.get(
                "weight"
            ),
            capacity=request.data.get(
                "capacity"
            ),
        )

        # --------------------------------------------------
        # VARIANTS
        # --------------------------------------------------

        variants = request.data.get(
            "variants",
            []
        )

        if isinstance(variants, str):

            try:
                variants = json.loads(
                    variants
                )

            except json.JSONDecodeError:

                variants = []

        for variant in variants:

            ProductVariant.objects.create(
                product=product,

                capacity=variant.get(
                    "capacity"
                ),

                price=variant.get(
                    "price"
                ),

                discount_price=variant.get(
                    "discount_price"
                ),
            )

        # --------------------------------------------------
        # IMAGES
        # --------------------------------------------------

        images = request.FILES.getlist(
            "images"
        )

        for image in images:

            ProductImage.objects.create(
                product=product,
                image=image
            )

        return Response(
            {
                "message":
                    "Product added successfully.",

                "product_id":
                    product.id,

                "status":
                    product.status
            },
            status=status.HTTP_201_CREATED
        )


# ==========================================================
# EDIT PRODUCT
# ==========================================================

class EditProductApi(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        IsSeller
    ]

    # ------------------------------------------------------
    # GET
    # ------------------------------------------------------

    def get(self, request, id):

        try:

            product = Product.objects.get(
                id=id,
                seller=request.user.seller_profile
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message":
                        "Product not found or you "
                        "do not have permission."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(
            product,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # ------------------------------------------------------
    # PUT
    # ------------------------------------------------------

    def put(self, request, id):

        try:

            product = Product.objects.get(
                id=id,
                seller=request.user.seller_profile
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message":
                        "Product not found or not yours."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data

        # --------------------------------------------------
        # BASIC INFORMATION
        # --------------------------------------------------

        if "productname" in data:

            product.productname = data.get(
                "productname"
            )

        if "description" in data:

            product.description = data.get(
                "description"
            )

        # --------------------------------------------------
        # CATEGORY
        # --------------------------------------------------

        if "category" in data:

            product.category = data.get(
                "category"
            )

        # --------------------------------------------------
        # PRICE
        # --------------------------------------------------

        if "price" in data:

            product.price = data.get(
                "price"
            )

        if "discount_price" in data:

            product.discount_price = data.get(
                "discount_price"
            )

        # --------------------------------------------------
        # SPECIFICATIONS
        # --------------------------------------------------

        if "weight" in data:

            product.weight = data.get(
                "weight"
            )

        if "capacity" in data:

            product.capacity = data.get(
                "capacity"
            )

        # --------------------------------------------------
        # IMPORTANT
        #
        # NO STOCK HERE
        #
        # Inventory is handled separately.
        # --------------------------------------------------

        product.status = (
            "pending_verification"
        )

        product.save()

        # --------------------------------------------------
        # ASSIGN REVIEWER
        # --------------------------------------------------

        try:

            assign_product_to_reviewer(
                product
            )

        except Exception as e:

            print(
                "REVIEWER ASSIGNMENT ERROR:",
                e
            )

        serializer = ProductSerializer(
            product,
            context={
                "request": request
            }
        )

        return Response(
            {
                "message":
                    "Product updated and submitted "
                    "for verification.",

                "product_id":
                    product.id,

                "status":
                    product.status,

                "product":
                    serializer.data
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# DELETE PRODUCT
# ==========================================================

class DeleteProductAPI(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsSeller
    ]

    def delete(self, request, id):

        try:

            product = Product.objects.get(
                id=id,
                seller=request.user.seller_profile
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message":
                        "Product not found or not yours."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        product.delete()

        return Response(
            {
                "message":
                    "Product deleted successfully.",

                "product_id":
                    id
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER PRODUCT LIST
# ==========================================================

class SellerProductListAPI(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsSeller
    ]

    def get(self, request):

        seller = request.user.seller_profile

        products = (
            Product.objects
            .filter(
                seller=seller
            )
            .prefetch_related(
                "variants",
                "images"
            )
            .order_by("-id")
        )

        data = []

        for product in products:

            variants = []

            for variant in product.variants.all():

                inventory = getattr(
                    variant,
                    "inventory",
                    None
                )

                variants.append(
                    {
                        "id":
                            variant.id,

                        "capacity":
                            variant.capacity,

                        "price":
                            str(
                                variant.price
                            ),

                        "discount_price": (
                            str(
                                variant.discount_price
                            )
                            if variant.discount_price
                            is not None
                            else None
                        ),

                        "stock_quantity": (
                            inventory.quantity
                            if inventory
                            else 0
                        )
                    }
                )

            data.append(
                {
                    "id":
                        product.id,

                    "productname":
                        product.productname,

                    "description":
                        product.description,

                    "price":
                        str(product.price),

                    "discount_price": (
                        str(
                            product.discount_price
                        )
                        if product.discount_price
                        is not None
                        else None
                    ),

                    "capacity":
                        product.capacity,

                    "weight":
                        product.weight,

                    "category":
                        product.category,

                    "status":
                        product.status,

                    "variants":
                        variants
                }
            )

        return Response(
            {
                "message":
                    "Seller Products",

                "total_products":
                    len(data),

                "products":
                    data
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER DASHBOARD
# ==========================================================

class SellerDashboard(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsSeller
    ]

    def get(self, request):

        seller = request.user.seller_profile

        total_products = Product.objects.filter(
            seller=seller
        ).count()

        available_inventory = Inventory.objects.filter(
            quantity__gt=0,
            product__seller=seller,
            variant__product__seller=seller,
        ).count()

        out_of_stock = Inventory.objects.filter(
            quantity=0,
            product__seller=seller,
            variant__product__seller=seller,
        ).count()

        total_orders = Order.objects.filter(
            product__seller=seller
        ).count()

        return Response(
            {
                "total_products":
                    total_products,

                "available_products":
                    available_inventory,

                "out_of_stock_products":
                    out_of_stock,

                "total_orders":
                    total_orders
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER ORDERS
# ==========================================================

class SellerOrdersListAPI(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsSeller
    ]

    def get(self, request):

        seller = request.user.seller_profile

        orders = (
            Order.objects
            .filter(
                product__seller=seller
            )
            .select_related(
                "user",
                "product",
                "payment",
                "address"
            )
            .order_by("-id")
        )

        data = []

        for order in orders:

            data.append(
                {
                    "order_id":
                        order.id,

                    "customer":
                        order.user.name,

                    "product":
                        order.product.productname,

                    "quantity":
                        order.quantity,

                    "total_price":
                        str(
                            order.total_price
                        ),

                    "order_status":
                        order.status,

                    "payment_method": (
                        order.payment.payment_method
                        if order.payment
                        else None
                    ),

                    "payment_status": (
                        order.payment.payment_status
                        if order.payment
                        else None
                    ),

                    "delivery_address": (
                        {
                            "full_name":
                                order.address.full_name,

                            "phone_number":
                                order.address.phone_number,

                            "address_line":
                                order.address.address_line,

                            "city":
                                order.address.city,

                            "state":
                                order.address.state,

                            "pincode":
                                order.address.pincode
                        }
                        if order.address
                        else None
                    ),

                    "ordered_at":
                        order.ordered_at
                }
            )

        return Response(
            {
                "total_orders_received":
                    orders.count(),

                "orders":
                    data
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER PRODUCTS - FULL
# ==========================================================

class SellerProductsView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        IsSeller
    ]

    def get(self, request):

        seller = request.user.seller_profile

        products = (
            Product.objects
            .filter(
                seller=seller
            )
            .prefetch_related(
                "images",
                "variants__inventory"
            )
            .order_by("-created_at")
        )

        results = []

        for product in products:

            images = []

            for image in product.images.all():

                if image.image:

                    try:
                        url = image.image.url

                    except Exception:
                        url = str(
                            image.image
                        )

                    images.append(
                        {
                            "id":
                                image.id,

                            "image":
                                url
                        }
                    )

            variants = []

            for variant in product.variants.all():

                inventory = getattr(
                    variant,
                    "inventory",
                    None
                )

                variants.append(
                    {
                        "id":
                            variant.id,

                        "capacity":
                            variant.capacity,

                        "price":
                            str(
                                variant.price
                            ),

                        "discount_price": (
                            str(
                                variant.discount_price
                            )
                            if variant.discount_price
                            is not None
                            else None
                        ),

                        "stock_quantity": (
                            inventory.quantity
                            if inventory
                            else 0
                        )
                    }
                )

            results.append(
                {
                    "id":
                        product.id,

                    "productname":
                        product.productname,

                    "description":
                        product.description,

                    "price":
                        str(
                            product.price
                        ),

                    "discount_price": (
                        str(
                            product.discount_price
                        )
                        if product.discount_price
                        is not None
                        else None
                    ),

                    "capacity":
                        product.capacity,

                    "weight":
                        product.weight,

                    "category":
                        product.category,

                    "status":
                        product.status,

                    "sku":
                        product.sku,

                    "variants":
                        variants,

                    "images":
                        images,

                    "created_at":
                        product.created_at,

                    "updated_at":
                        product.updated_at,
                }
            )

        return Response(
            {
                "count":
                    len(results),

                "results":
                    results
            }
        )


# ==========================================================
# SELLER INVENTORY
# ==========================================================

class SellerInventoryAPI(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsSeller
    ]

    def get(self, request):

        seller = request.user.seller_profile

        products = (
            Product.objects
            .filter(
                seller=seller,
                status="approved"
            )
            .prefetch_related(
                "variants__inventory"
            )
            .order_by("-updated_at")
        )

        results = []

        for product in products:

            variants = product.variants.all()

            # ==================================================
            # PRODUCT WITH VARIANTS
            # ==================================================

            if variants.exists():

                for variant in variants:

                    inventory = getattr(
                        variant,
                        "inventory",
                        None
                    )

                    quantity = (
                        inventory.quantity
                        if inventory
                        else 0
                    )

                    threshold = (
                        inventory.low_stock_threshold
                        if inventory
                        else 10
                    )

                    if quantity == 0:

                        inventory_status = (
                            "out_of_stock"
                        )

                    elif quantity <= threshold:

                        inventory_status = (
                            "low_stock"
                        )

                    else:

                        inventory_status = (
                            "in_stock"
                        )

                    results.append(
                        {
                            "inventory_type":
                                "variant",

                            "inventory_id": (
                                inventory.id
                                if inventory
                                else None
                            ),

                            "product_id":
                                product.id,

                            "variant_id":
                                variant.id,

                            "productname":
                                product.productname,

                            "sku":
                                product.sku,

                            "capacity":
                                variant.capacity,

                            "price":
                                str(
                                    variant.price
                                ),

                            "discount_price": (
                                str(
                                    variant.discount_price
                                )
                                if variant.discount_price
                                is not None
                                else None
                            ),

                            "stock_quantity":
                                quantity,

                            "low_stock_threshold":
                                threshold,

                            "inventory_status":
                                inventory_status,

                            "updated_at": (
                                inventory.updated_at
                                if inventory
                                else product.updated_at
                            )
                        }
                    )

            # ==================================================
            # PRODUCT WITHOUT VARIANTS
            # ==================================================

            else:

                inventory = getattr(
                    product,
                    "inventory",
                    None
                )

                quantity = (
                    inventory.quantity
                    if inventory
                    else 0
                )

                threshold = (
                    inventory.low_stock_threshold
                    if inventory
                    else 10
                )

                if quantity == 0:

                    inventory_status = (
                        "out_of_stock"
                    )

                elif quantity <= threshold:

                    inventory_status = (
                        "low_stock"
                    )

                else:

                    inventory_status = (
                        "in_stock"
                    )

                results.append(
                    {
                        "inventory_type":
                            "product",

                        "inventory_id": (
                            inventory.id
                            if inventory
                            else None
                        ),

                        "product_id":
                            product.id,

                        "variant_id":
                            None,

                        "productname":
                            product.productname,

                        "sku":
                            product.sku,

                        "capacity":
                            product.capacity,

                        "price":
                            str(
                                product.price
                            ),

                        "discount_price": (
                            str(
                                product.discount_price
                            )
                            if product.discount_price
                            is not None
                            else None
                        ),

                        "stock_quantity":
                            quantity,

                        "low_stock_threshold":
                            threshold,

                        "inventory_status":
                            inventory_status,

                        "updated_at": (
                            inventory.updated_at
                            if inventory
                            else product.updated_at
                        )
                    }
                )

        return Response(
            {
                "count":
                    len(results),

                "results":
                    results
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# UPDATE INVENTORY
# ==========================================================

class UpdateInventoryAPI(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsSeller
    ]

    @transaction.atomic
    def put(self, request, product_id):

        seller = request.user.seller_profile

        # product_id = request.data.get(
        #     "product_id"
        # )

        variant_id = request.data.get(
            "variant_id"
        )

        # --------------------------------------------------
        # VALIDATE PRODUCT
        # --------------------------------------------------

        try:

            product = Product.objects.get(
                id=product_id,
                seller=seller
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message":
                        "Product not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # --------------------------------------------------
        # ONLY APPROVED
        # --------------------------------------------------

        if product.status != "approved":

            return Response(
                {
                    "message":
                        "Inventory can only be managed "
                        "for approved products."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # QUANTITY
        # --------------------------------------------------

        try:

            quantity = int(
                request.data.get(
                    "quantity"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return Response(
                {
                    "message":
                        "Stock quantity must be a valid number."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 0:

            return Response(
                {
                    "message":
                        "Stock quantity cannot be negative."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # VARIANT INVENTORY
        # ==================================================

        if variant_id:

            try:

                variant = (
                    ProductVariant.objects
                    .get(
                        id=variant_id,
                        product=product
                    )
                )

            except ProductVariant.DoesNotExist:

                return Response(
                    {
                        "message":
                            "Product variant not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            inventory, created = (
                Inventory.objects
                .get_or_create(
                    variant=variant,
                    defaults={
                        "quantity":
                            quantity,

                        "low_stock_threshold":
                            10
                    }
                )
            )

            if not created:

                inventory.quantity = quantity

                if (
                    "low_stock_threshold"
                    in request.data
                ):

                    try:

                        threshold = int(
                            request.data.get(
                                "low_stock_threshold"
                            )
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        return Response(
                            {
                                "message":
                                    "Low stock threshold "
                                    "must be valid."
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    if threshold < 0:

                        return Response(
                            {
                                "message":
                                    "Low stock threshold "
                                    "cannot be negative."
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    inventory.low_stock_threshold = (
                        threshold
                    )

                inventory.save()

            return Response(
                {
                    "message":
                        "Variant inventory updated successfully.",

                    "inventory_id":
                        inventory.id,

                    "product_id":
                        product.id,

                    "variant_id":
                        variant.id,

                    "productname":
                        product.productname,

                    "capacity":
                        variant.capacity,

                    "stock_quantity":
                        inventory.quantity,

                    "low_stock_threshold":
                        inventory.low_stock_threshold
                },
                status=status.HTTP_200_OK
            )

        # ==================================================
        # PRODUCT WITHOUT VARIANT
        # ==================================================

        # Safety check:
        # If product has variants, variant_id is required.

        if product.variants.exists():

            return Response(
                {
                    "message":
                        "This product has variants. "
                        "Please provide variant_id."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        inventory, created = (
            Inventory.objects
            .get_or_create(
                product=product,
                defaults={
                    "quantity":
                        quantity,

                    "low_stock_threshold":
                        10
                }
            )
        )

        if not created:

            inventory.quantity = quantity

            if (
                "low_stock_threshold"
                in request.data
            ):

                try:

                    threshold = int(
                        request.data.get(
                            "low_stock_threshold"
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return Response(
                        {
                            "message":
                                "Low stock threshold "
                                "must be valid."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if threshold < 0:

                    return Response(
                        {
                            "message":
                                "Low stock threshold "
                                "cannot be negative."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                inventory.low_stock_threshold = (
                    threshold
                )

            inventory.save()

        return Response(
            {
                "message":
                    "Inventory updated successfully.",

                "inventory_id":
                    inventory.id,

                "product_id":
                    product.id,

                "variant_id":
                    None,

                "productname":
                    product.productname,

                "capacity":
                    product.capacity,

                "stock_quantity":
                    inventory.quantity,

                "low_stock_threshold":
                    inventory.low_stock_threshold
            },
            status=status.HTTP_200_OK
        )