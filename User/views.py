from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .utils import (
    get_tracking,
    expected_delivery,
    current_location,
)
from payments.models import Payment
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Address
from orders.models import Order 

from accounts.models import CustomUser
from seller.models import Product, ProductVariant
from .permissions import *


class user_dashboard(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def get(self, request):
        pass



#addd to cart APAI

class AddToCartAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def post(self, request, id):

        try:
            customer = get_object_or_404(
                CustomUser,
                id=request.user.id
            )

            cart, _ = Cart.objects.get_or_create(user=customer)

            product = get_object_or_404(Product, id=id)

            quantity = int(request.data.get("quantity", 1))
            variant_id = request.data.get("variant_id")

            

            variant = None

            # Variant selected
            if variant_id:
                variant = get_object_or_404(
                    ProductVariant,
                    id=variant_id,
                    product=product
                )

                stock = variant.stock_quantity

            else:
                stock = product.stock_quantity

            if stock <= 0:
                return Response(
                    {
                        "message": "This product is currently out of stock."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant
            )

            if created:
                cart_item.quantity = quantity

            else:

                if cart_item.quantity + quantity > stock:
                    return Response(
                        {
                            "message": f"Only {stock} item(s) available."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                cart_item.quantity += quantity

            cart_item.save()
            

            return Response(
                {
                    "message": "Product added to cart successfully.",
                    "product_id": product.id,
                    "product_name": product.productname,
                    "variant": variant.capacity if variant else "Standard",
                    "cart_quantity": cart_item.quantity,
                    "available_stock": stock,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "message": "Unable to add product to cart.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        
        
# View Cart API
class ViewCartAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def get(self, request):

        customer = request.user

        # Get customer cart
        cart = get_object_or_404(Cart, user=customer)

        # Get cart items
        cart_items = (
            CartItem.objects
            .filter(cart=cart)
            .select_related(
                "product",
                "variant",
                "product__seller__user"
            )
            .prefetch_related("product__images")
        )

        data = []

        total_original_price = 0
        total_discount_price = 0
        total_savings = 0

        for item in cart_items:

            product = item.product
            variant = item.variant
            quantity = item.quantity

            # ==========================
            # Variant Details
            # ==========================

            if variant:
                price = variant.price
                discount_price = variant.discount_price
                stock = variant.stock_quantity
                capacity = variant.capacity
            else:
                price = product.price
                discount_price = product.discount_price
                stock = product.stock_quantity
                capacity = None

            subtotal_original = price * quantity
            subtotal_discount = discount_price * quantity
            savings = subtotal_original - subtotal_discount

            total_original_price += subtotal_original
            total_discount_price += subtotal_discount
            total_savings += savings

            # ==========================
            # Product Image
            # ==========================

            product_image = None

            first_image = product.images.first()

            if first_image:
                product_image = request.build_absolute_uri(
                    first_image.image.url
                )

            # ==========================
            # Seller Name
            # ==========================

            seller_name = None

            if product.seller:
                seller_name = (
                    product.seller.user.get_full_name()
                    or product.seller.user.username
                    or product.seller.user.email
                )

            # ==========================
            # Cart Data
            # ==========================

            data.append({

                "cart_item_id": item.id,

                "product_id": product.id,

                "product_name": product.productname,

                "product_image": product_image,

                "seller": seller_name,

                "variant_id": variant.id if variant else None,

                "capacity": capacity,

                "weight": product.weight,

                "stock": stock,

                "original_price": str(price),

                "discount_price": str(discount_price),

                "quantity": quantity,

                "subtotal_original_price": str(subtotal_original),

                "subtotal_discount_price": str(subtotal_discount),

                "you_save": str(savings)

            })

        return Response(
            {

                "message": "Cart fetched successfully",

                "total_items": cart_items.count(),

                "total_original_price": str(total_original_price),

                "total_discount_price": str(total_discount_price),

                "total_savings": str(total_savings),

                "cart_items": data

            },
            status=status.HTTP_200_OK
        )

# Remove Cart Item API
class RemoveCartItemAPI(APIView):

    authentication_classes = [TokenAuthentication]

    permission_classes = [IsCustomer]

    def delete(self, request, id):

        customer = request.user

        # Get customer cart
        cart = get_object_or_404(Cart,user=customer)

        # Get cart item
        cart_item = get_object_or_404(CartItem,id=id,cart=cart)

        product_name = cart_item.product.productname

        # If quantity greater than 1
        if cart_item.quantity > 1:

            cart_item.quantity -= 1

            cart_item.save()

            return Response(
                {
                    "message": "Product quantity decreased successfully",
                    "product_name": product_name,
                    "remaining_quantity": cart_item.quantity
                },
                status=status.HTTP_200_OK
            )

        # If quantity is 1 delete item
        cart_item.delete()

        return Response(
            {
                "message": "Cart item removed successfully",
                "removed_product": product_name
            },
            status=status.HTTP_200_OK
 
 
        )  



class UserOrderHistoryAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def get(self, request):

        orders = (
            Order.objects
            .filter(user=request.user)
            .select_related("address")
            .prefetch_related(
                "items__variant",
                "items__product__images",
            )
            .order_by("-created_at")
        )

        data = []

        for order in orders:

            payment = (
                Payment.objects
                .filter(order=order)
                .first()
            )

            items = []

            for item in order.items.all():

                product = item.product
                variant = item.variant

                image = None

                first_image = product.images.first()

                if first_image:
                    image = request.build_absolute_uri(
                        first_image.image.url
                    )

                items.append({

                    "product_id": product.id,

                    "product_name": product.productname,

                    "image": image,

                    "variant": (
                        variant.capacity
                        if variant else "Standard"
                    ),

                    "quantity": item.quantity,

                    "price": str(item.price),

                    "subtotal": str(
                        item.price * item.quantity
                    ),

                })

            address = None

            if order.address:

                address = {

                    "full_name": order.address.full_name,

                    "phone_number": order.address.phone_number,

                    "address_line": order.address.address_line,

                    "city": order.address.city,

                    "state": order.address.state,

                    "pincode": order.address.pincode,

                    "address_type": order.address.address_type,

                }

            transaction_id = None
            tracking_number = None

            if payment and payment.transaction_id:
                transaction_id = payment.transaction_id
                tracking_number = payment.transaction_id[:12]

            data.append({

                "order_id": order.id,

                "status": order.status,

                "payment_method": order.payment_method,

                "payment_status": order.payment_status,

                "refund_status": getattr(
                    order,
                    "refund_status",
                    None
                ),

                "transaction_id": transaction_id,

                "tracking_number": tracking_number,

                "total_price": str(order.total_price),

                "created_at": order.created_at,

                "delivery_partner": "ClayWare Logistics",

                "expected_delivery": expected_delivery(order),

                "current_location": current_location(
                    order.status
                ),

                "tracking": get_tracking(
                    order.status
                ),

                "address": address,

                "items": items,

                "can_cancel": (
                    order.status == "PLACED"
                ),

                "can_return": (
                    order.status == "DELIVERED"
                ),

                "can_download_invoice": (
                    order.status == "DELIVERED"
                ),

            })

        return Response(

            {

                "success": True,

                "total_orders": orders.count(),

                "orders": data,

            },

            status=status.HTTP_200_OK

        )

class OrderDetailsAPIView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def get(self, request, order_id):

        try:

            order = (
                Order.objects
                .select_related("address")
                .prefetch_related(
                    "items__variant",
                    "items__product__images",
                )
                .get(
                    id=order_id,
                    user=request.user
                )
            )

        except Order.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        payment = (
            Payment.objects
            .filter(order=order)
            .first()
        )

        items = []

        for item in order.items.all():

            product = item.product
            variant = item.variant

            image = None

            first_image = product.images.first()

            if first_image:
                image = request.build_absolute_uri(
                    first_image.image.url
                )

            items.append({

                "product_id": product.id,

                "product_name": product.productname,

                "image": image,

                "variant_id": (
                    variant.id if variant else None
                ),

                "variant": (
                    variant.capacity
                    if variant else "Standard"
                ),

                "quantity": item.quantity,

                "price": str(item.price),

                "subtotal": str(
                    item.price * item.quantity
                ),

            })

        address = None

        if order.address:

            address = {

                "full_name": order.address.full_name,

                "phone_number": order.address.phone_number,

                "address_line": order.address.address_line,

                "city": order.address.city,

                "state": order.address.state,

                "pincode": order.address.pincode,

                "address_type": order.address.address_type,

            }

        transaction_id = None
        tracking_number = None

        if payment:

            transaction_id = payment.transaction_id

            if payment.transaction_id:
                tracking_number = payment.transaction_id[:12]

        return Response(

            {

                "success": True,

                "order": {

                    "order_id": order.id,

                    "status": order.status,

                    "payment_method": order.payment_method,

                    "payment_status": order.payment_status,

                    "refund_status": getattr(
                        order,
                        "refund_status",
                        None
                    ),

                    "transaction_id": transaction_id,

                    "tracking_number": tracking_number,

                    "total_price": str(order.total_price),

                    "created_at": order.created_at,

                    "delivery_partner": "ClayWare Logistics",

                    "expected_delivery": expected_delivery(order),

                    "current_location": current_location(
                        order.status
                    ),

                    "tracking": get_tracking(
                        order.status
                    ),

                    "address": address,

                    "items": items,

                    "can_cancel": (
                        order.status == "PLACED"
                    ),

                    "can_return": (
                        order.status == "DELIVERED"
                    ),

                    "can_download_invoice": (
                        order.status == "DELIVERED"
                    ),

                }

            },

            status=status.HTTP_200_OK

        )
class AddAddressAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def post(self, request):

        address = Address.objects.create(
            user=request.user,
            full_name=request.data.get('full_name'),
            phone_number=request.data.get('phone_number'),
            address_line=request.data.get('address_line'),
            city=request.data.get('city'),
            state=request.data.get('state'),
            address_type = request.data.get('address_type',"Home"),
            pincode=request.data.get('pincode'),
            is_default=request.data.get('is_default', False)
        )

        return Response(
            {
                "message": "Address added successfully",
                "address_id": address.id
            },
            status=status.HTTP_201_CREATED
        )
    


class UserAddressesAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsCustomer]

    def get(self, request):

        addresses = Address.objects.filter(
            user=request.user
        )

        data = []

        for address in addresses:

            data.append({
                "address_id": address.id,
                "full_name": address.full_name,
                "phone_number": address.phone_number,
                "address_line": address.address_line,
                "city": address.city,
                "state": address.state,
                "address_type" : address.address_type,
                "pincode": address.pincode,
                "is_default": address.is_default
            })

        return Response(
            {
                "addresses": data
            },
            status=status.HTTP_200_OK
        )