from decimal import Decimal
from django.db import transaction
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from User.models import Cart, CartItem
from orders.models import Order
from payments.models import Payment

from .services import client


class CreateRazorpayOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
            order = Order.objects.get(
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

        if order.payment_status == "SUCCESS":
            return Response(
                {
                    "success": False,
                    "message": "Order already paid."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = int(Decimal(order.total_price) * 100)

        razorpay_order = client.order.create({
            "amount": amount,
            "currency": settings.RAZORPAY_CURRENCY,
            "payment_capture": 1
        })

        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "payment_method": "RAZORPAY",
                "payment_status": "PENDING"
            }
        )

        payment.razorpay_order_id = razorpay_order["id"]
        payment.save()

        return Response({
            "success": True,
            "key": settings.RAZORPAY_KEY_ID,
            "amount": amount,
            "currency": settings.RAZORPAY_CURRENCY,
            "order_id": order.id,
            "razorpay_order_id": razorpay_order["id"]
        })


class VerifyRazorpayPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        ]):
            return Response(
                {
                    "success": False,
                    "message": "Missing payment details."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.select_related("order").get(
                razorpay_order_id=razorpay_order_id
            )

        except Payment.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if payment.payment_status == "SUCCESS":
            return Response(
                {
                    "success": True,
                    "message": "Payment already verified.",
                    "order_id": payment.order.id
                }
            )

        # ---------------------------------------
        # VERIFY RAZORPAY SIGNATURE
        # ---------------------------------------

        try:

            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })

        except Exception as e:

            print("=" * 60)
            print("RAZORPAY VERIFY ERROR")
            print(str(e))
            print("Order ID :", razorpay_order_id)
            print("Payment ID :", razorpay_payment_id)
            print("Signature :", razorpay_signature)
            print("=" * 60)

            payment.payment_status = "FAILED"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

            order = payment.order
            order.payment_status = "FAILED"
            order.status = "CANCELLED"
            order.save()

            return Response(
                {
                    "success": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------
        # PAYMENT SUCCESS
        # ---------------------------------------

        payment.payment_status = "SUCCESS"
        payment.transaction_id = razorpay_payment_id
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.save()

        order = payment.order
        order.payment_status = "SUCCESS"
        order.status = "PLACED"
        order.save()

        # ---------------------------------------
        # DEDUCT STOCK
        # ---------------------------------------

        for item in order.items.select_related("product", "variant"):

            product = item.product

            if item.variant:

                variant = item.variant

                if variant.stock_quantity < item.quantity:
                    return Response(
                        {
                            "success": False,
                            "message": f"{product.productname} ({variant.capacity}) is out of stock."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                variant.stock_quantity -= item.quantity
                variant.save()

            else:

                if product.stock_quantity < item.quantity:
                    return Response(
                        {
                            "success": False,
                            "message": f"{product.productname} is out of stock."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                product.stock_quantity -= item.quantity
                product.save()

        # ---------------------------------------
        # CLEAR CART
        # ---------------------------------------

        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart).delete()

        except Cart.DoesNotExist:
            pass

        return Response(
            {
                "success": True,
                "message": "Payment verified successfully.",
                "order_id": order.id
            },
            status=status.HTTP_200_OK
        )


class PaymentFailedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        order_id = request.data.get("order_id")

        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user
            )

        except Order.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Order not found."
                },
                status=404
            )

        # Delete payment first
        Payment.objects.filter(order=order).delete()

        # Delete order items automatically if using CASCADE,
        # otherwise:
        # order.items.all().delete()

        order.delete()

        return Response(
            {
                "success": True,
                "message": "Cancelled successfully."
            }
        )

class RefundAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        order_id = request.data.get("order_id")

        order = Order.objects.get(
            id=order_id,
            user=request.user
        )

        payment = Payment.objects.get(order=order)

        refund = client.payment.refund(
            payment.razorpay_payment_id,
            {
                "amount": int(order.total_price * 100)
            }
        )

        order.refund_status = "PROCESSING"
        order.save()

        return Response(
            {
                "success": True,
                "refund_id": refund["id"]
            }
        )