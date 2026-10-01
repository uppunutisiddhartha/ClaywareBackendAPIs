from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from User.models import Address, Cart, CartItem
from User.permissions import IsCustomer

from .serializer import *

from seller.models import Product, ProductVariant, Inventory

from .models import Order, OrderItem,Review
from payments.models import Payment

import uuid


class CheckoutAPI(APIView):

    #permission_classes =[JWTAuthentication]
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    @transaction.atomic
    def post(self, request):

        user = request.user

        address_id = request.data.get("address_id")
        payment_method = request.data.get("payment_method")

        # ==========================================================
        # BUY NOW DATA
        # ==========================================================

        buy_now = request.data.get("buy_now", False)
        buy_now_product = request.data.get("buy_now_product")

        product_id = None
        variant_id = None
        quantity = 1

        if buy_now and buy_now_product:

            product_id = buy_now_product.get("product_id")
            variant_id = buy_now_product.get("variant_id")
            quantity = int(
                buy_now_product.get("quantity", 1)
            )

        # ==========================================================
        # PAYMENT VALIDATION
        # ==========================================================

        if payment_method not in ["COD", "RAZORPAY"]:

            return Response(
                {
                    "success": False,
                    "message": "Invalid payment method."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==========================================================
        # ADDRESS VALIDATION
        # ==========================================================

        try:

            address = Address.objects.get(
                id=address_id,
                user=user
            )

        except Address.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Invalid delivery address."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==========================================================
        # BUILD ITEMS
        # ==========================================================

        items = []

        # ==========================================================
        # BUY NOW CHECKOUT
        # ==========================================================

        if buy_now:

            try:

                product = Product.objects.select_for_update().get(
                    id=product_id
                )

            except Product.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Product not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            variant = None

            if variant_id:

                try:

                    variant = ProductVariant.objects.select_for_update().get(
                        id=variant_id,
                        product=product
                    )

                except ProductVariant.DoesNotExist:

                    return Response(
                        {
                            "success": False,
                            "message": "Selected variant not found."
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

            items.append(
                {
                    "product": product,
                    "variant": variant,
                    "quantity": quantity,
                }
            )

        # ==========================================================
        # CART CHECKOUT
        # ==========================================================

        else:

            try:

                cart = Cart.objects.get(user=user)

            except Cart.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Your cart is empty."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_items = CartItem.objects.select_related(
                "product",
                "variant"
            ).filter(
                cart=cart
            )

            if not cart_items.exists():

                return Response(
                    {
                        "success": False,
                        "message": "Your cart is empty."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            for cart_item in cart_items:

                items.append(
                    {
                        "product": cart_item.product,
                        "variant": cart_item.variant,
                        "quantity": cart_item.quantity,
                    }
                )
       # ==========================================================
# STOCK VALIDATION
        # ==========================================================

        total_price = 0

        for item in items:

            qty = item["quantity"]

            if qty <= 0:
                return Response(
                    {
                        "success": False,
                        "message": "Invalid quantity."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ======================================================
            # VARIANT PRODUCT
            # ======================================================

            if item["variant"]:

                variant = (
                    ProductVariant.objects
                    .select_for_update()
                    .select_related("inventory", "product")
                    .get(id=item["variant"].id)
                )

                try:
                    inventory = variant.inventory
                except Inventory.DoesNotExist:
                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"Inventory not found for "
                                f"{variant.product.productname} "
                                f"({variant.capacity})."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if inventory.quantity < qty:
                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"{variant.product.productname} "
                                f"({variant.capacity}) has only "
                                f"{inventory.quantity} left."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                price = variant.discount_price or variant.price

            # ======================================================
            # NORMAL PRODUCT
            # ======================================================

            else:

                product = (
                    Product.objects
                    .select_for_update()
                    .select_related("inventory")
                    .get(id=item["product"].id)
                )

                try:
                    inventory = product.inventory
                except Inventory.DoesNotExist:
                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"Inventory not found for "
                                f"{product.productname}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if inventory.quantity < qty:
                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"{product.productname} has only "
                                f"{inventory.quantity} left."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                price = product.discount_price or product.price

            total_price += price * qty
        # ==========================================================
        # CREATE ORDER
        # ==========================================================

        order = Order.objects.create(
            user=user,
            address=address,
            payment_method=payment_method,
            payment_status="PENDING",
            status="PENDING",
            total_price=total_price,
            is_buy_now=buy_now,
        )

        # ==========================================================
        # CREATE ORDER ITEMS
        # ==========================================================

        for item in items:

            if item["variant"]:

                variant = ProductVariant.objects.get(
                    id=item["variant"].id
                )

                price = variant.discount_price or variant.price

                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    variant=variant,
                    quantity=item["quantity"],
                    price=price
                )

            else:

                product = Product.objects.get(
                    id=item["product"].id
                )

                price = product.discount_price or product.price

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price=price
                )

        # ==========================================================
        # CREATE PAYMENT RECORD
        # ==========================================================

        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            payment_status="PENDING",
            transaction_id=str(uuid.uuid4())
        )
                # ==========================================================
        # CASH ON DELIVERY
        # ==========================================================

        if payment_method == "COD":

            # Deduct Stock

            for item in items:

                if item["variant"]:

                    variant = ProductVariant.objects.select_for_update().get(
                        id=item["variant"].id
                    )

                    variant.stock_quantity -= item["quantity"]

                    variant.save(
                        update_fields=["stock_quantity"]
                    )

                else:

                    inventory = Inventory.objects.select_for_update().get(
                    product_id=item["product"].id
                )

                inventory.quantity -= item["quantity"]

                inventory.save(
                    update_fields=["quantity"]
)

            # ==========================================
            # CLEAR CART (ONLY CART CHECKOUT)
            # ==========================================

            if not buy_now:

                CartItem.objects.filter(
                    cart__user=user
                ).delete()

            # ==========================================
            # UPDATE PAYMENT
            # ==========================================

            payment.payment_status = "SUCCESS"

            payment.save(
                update_fields=["payment_status"]
            )

            order.payment_status = "SUCCESS"
            order.status = "PLACED"

            order.save(
                update_fields=[
                    "payment_status",
                    "status",
                ]
            )

            return Response(
                {
                    "success": True,
                    "message": "Order placed successfully.",
                    "order_id": order.id,
                    "payment_status": "SUCCESS",
                    "payment_method": payment_method,
                    "total": order.total_price,
                },
                status=status.HTTP_201_CREATED,
            )

        # ==========================================================
        # RAZORPAY PAYMENT
        # ==========================================================

        return Response(
            {
                "success": True,
                "message": "Proceed to Razorpay payment.",
                "order_id": order.id,
                "transaction_id": payment.transaction_id,
                "payment_method": payment.payment_method,
                "payment_status": payment.payment_status,
                "total": order.total_price,
                "is_buy_now": buy_now,
            },
            status=status.HTTP_200_OK,
        )





class CancelOrderAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):

        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {
                    "success": False,
                    "message": "Order ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.select_for_update().get(
                id=order_id,
                user=request.user
            )

        except Order.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Already Cancelled

        if order.status == "CANCELLED":
            return Response(
                {
                    "success": False,
                    "message": "Order already cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delivered orders cannot be cancelled

        if order.status == "DELIVERED":
            return Response(
                {
                    "success": False,
                    "message": "Delivered orders cannot be cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = Payment.objects.get(order=order)

        # ==========================================================
        # RESTORE STOCK
        # ==========================================================

        for item in order.items.select_related(
            "product",
            "variant"
        ):

            if item.variant:

                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant.id
                )

                variant.stock_quantity += item.quantity

                variant.save(update_fields=["stock_quantity"])

            else:

                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )

                product.stock_quantity += item.quantity

                product.save(update_fields=["stock_quantity"])

        # ==========================================================
        # UPDATE ORDER STATUS
        # ==========================================================

        order.status = "CANCELLED"

        # ==========================================================
        # REFUND STATUS
        # ==========================================================

        if payment.payment_method == "COD":

            order.refund_status = "NOT_REQUIRED"

        else:

            order.refund_status = "INITIATED"

            payment.payment_status = "REFUND_PENDING"

            payment.save(update_fields=["payment_status"])

        order.save(
            update_fields=[
                "status",
                "refund_status"
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Order cancelled successfully.",
                "refund_status": order.refund_status,
            },
            status=status.HTTP_200_OK
        )
    


class OrderSuccessAPIView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsCustomer]

    def get(self, request, order_id):

        try:
            order = (
                Order.objects
                .select_related("address")
                .prefetch_related("items__product", "items__variant")
                .get(id=order_id, user=request.user)
            )

        except Order.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        items = []

        for item in order.items.all():

            items.append({

                "product_id": item.product.id,
                "product_name": item.product.productname,
                "quantity": item.quantity,
                "price": float(item.price),

                "variant": (
                    item.variant.capacity
                    if item.variant else None
                ),

                "subtotal": float(item.price) * item.quantity,
            })

        return Response(
            {
                "success": True,

                "order": {

                    "id": order.id,

                    "status": order.status,

                    "payment_method": order.payment_method,

                    "payment_status": order.payment_status,

                    "total_price": float(order.total_price),

                    "date": order.created_at,

                    "address": {

                        "full_name": (
                            order.address.full_name
                            if order.address else ""
                        ),

                        "phone_number": (
                            order.address.phone_number
                            if order.address else ""
                        ),

                        "address_line": (
                            order.address.address_line
                            if order.address else ""
                        ),

                        "city": (
                            order.address.city
                            if order.address else ""
                        ),

                        "state": (
                            order.address.state
                            if order.address else ""
                        ),

                        "pincode": (
                            order.address.pincode
                            if order.address else ""
                        ),

                        "address_type": (
                            order.address.address_type
                            if order.address else ""
                        ),
                    },

                    "items": items,
                }
            },
            status=status.HTTP_200_OK
        )
    

# ==========================================
# ADD REVIEW
# ==========================================

class AddReviewAPIView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):

        product = get_object_or_404(Product, id=product_id)

        # Check purchase
        purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status="DELIVERED"
        ).exists()

        if not purchased:
            return Response(
                {
                    "message":
                    "You can review only purchased products."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if Review.objects.filter(
            user=request.user,
            product=product
        ).exists():

            return Response(
                {
                    "message":
                    "You already reviewed this product."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save(
                user=request.user,
                product=product
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==========================================
# PRODUCT REVIEWS
# ==========================================

class ProductReviewsAPIView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):

        product = get_object_or_404(
            Product,
            id=product_id
        )

        reviews = Review.objects.filter(
            product=product
        ).select_related("user").order_by("-created_at")

        serializer = ReviewSerializer(
            reviews,
            many=True
        )

        return Response(serializer.data)
    
    