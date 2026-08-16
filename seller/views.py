import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.authentication import JWTAuthentication

from orders.models import Order
from .models import Product, ProductVariant, ProductImage
from .permissions import IsSeller


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
                    "message": "Seller profile does not exist for this account."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        product = Product.objects.create(
            seller=seller,
            productname=request.data.get("productname"),
            description=request.data.get("description"),
            price=request.data.get("price"),
            category=request.data.get("category"),
            discount_price=request.data.get("discount_price"),
            stock_quantity=request.data.get("stock_quantity"),
            weight=request.data.get("weight"),
            capacity=request.data.get("capacity"),
        )

        variants = request.data.get("variants", [])

        if isinstance(variants, str):
            try:
                variants = json.loads(variants)
            except json.JSONDecodeError:
                variants = []

        for variant in variants:
            ProductVariant.objects.create(
                product=product,
                price=variant.get("price"),
                stock_quantity=variant.get("stock_quantity")
            )

        images = request.FILES.getlist("images")

        for image in images:
            ProductImage.objects.create(
                product=product,
                image=image
            )

        return Response(
            {
                "message": "Product Added Successfully",
                "product_id": product.id
            },
            status=status.HTTP_201_CREATED
        )
# ==========================================================
# EDIT PRODUCT
# ==========================================================

class EditProductApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSeller]

    def put(self, request, id):

        try:

            product = Product.objects.get(
                id=id,
                seller=request.user.seller_profile
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message": "Product not found or not yours"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data

        product.productname = data.get(
            "productname",
            product.productname
        )

        product.description = data.get(
            "description",
            product.description
        )

        product.price = data.get(
            "price",
            product.price
        )

        product.discount_price = data.get(
            "discount_price",
            product.discount_price
        )

        product.stock_quantity = data.get(
            "stock_quantity",
            product.stock_quantity
        )

        product.weight = data.get(
            "weight",
            product.weight
        )

        product.capacity = data.get(
            "capacity",
            product.capacity
        )

        product.save()

        return Response(
            {
                "message": "Product updated successfully",
                "product_id": product.id
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# DELETE PRODUCT
# ==========================================================

class DeleteProductAPI(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSeller]

    def delete(self, request, id):

        try:

            product = Product.objects.get(
                id=id,
                seller=request.user.seller_profile
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message": "Product not found or not yours"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        product.delete()

        return Response(
            {
                "message": "Product deleted successfully",
                "product_id": id
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER PRODUCT LIST
# ==========================================================

class SellerProductListAPI(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSeller]

    def get(self, request):

        seller = request.user.seller_profile

        products = Product.objects.filter(
            seller=seller
        ).order_by("-id")

        data = []

        for p in products:

            data.append(
                {
                    "id": p.id,
                    "productname": p.productname,
                    "description": p.description,
                    "price": str(p.price),
                    "discount_price": (
                        str(p.discount_price)
                        if p.discount_price is not None
                        else None
                    ),
                    "stock_quantity": p.stock_quantity,
                    "weight": p.weight,
                    "capacity": p.capacity,
                    "category": p.category,
                }
            )

        return Response(
            {
                "message": "Seller Products",
                "total_products": len(data),
                "products": data
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER DASHBOARD
# ==========================================================

class SellerDashboard(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSeller]

    def get(self, request):

        # Product.seller is Seller profile
        seller = request.user.seller_profile

        total_products = Product.objects.filter(
            seller=seller
        ).count()

        available_products = Product.objects.filter(
            seller=seller,
            stock_quantity__gt=0
        ).count()

        out_of_stock_products = Product.objects.filter(
            seller=seller,
            stock_quantity=0
        ).count()

        total_orders = Order.objects.filter(
            product__seller=seller
        ).count()

        return Response(
            {
                "total_products": total_products,
                "available_products": available_products,
                "out_of_stock_products": out_of_stock_products,
                "total_orders": total_orders
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# SELLER ORDERS
# ==========================================================

class SellerOrdersListAPI(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSeller]

    def get(self, request):

        seller = request.user.seller_profile

        # Get orders belonging to this seller
        orders = Order.objects.filter(
            product__seller=seller
        ).select_related(
            "user",
            "product",
            "payment",
            "address"
        ).order_by("-id")

        data = []

        for order in orders:

            data.append(
                {
                    "order_id": order.id,

                    # CUSTOMER
                    "customer": order.user.name,

                    # PRODUCT
                    "product": order.product.productname,
                    "quantity": order.quantity,
                    "total_price": str(order.total_price),

                    # ORDER STATUS
                    "order_status": order.status,

                    # PAYMENT
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

                    # DELIVERY ADDRESS
                    "delivery_address": {
                        "full_name": order.address.full_name,
                        "phone_number": order.address.phone_number,
                        "address_line": order.address.address_line,
                        "city": order.address.city,
                        "state": order.address.state,
                        "pincode": order.address.pincode
                    } if order.address else None,

                    "ordered_at": order.ordered_at
                }
            )

        return Response(
            {
                "total_orders_received": orders.count(),
                "orders": data
            },
            status=status.HTTP_200_OK
        )