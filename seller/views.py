from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from orders.models import Order
from .models import Product,ProductVariant,ProductImage
from .permissions import IsSeller


# Add Product

class AddProductAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSeller]

    def post(self, request):

        seller = request.user.seller_profile

        product = Product.objects.create(
            seller=seller,
            productname=request.data.get('productname'),
            description=request.data.get('description'),
            price=request.data.get('price'),
            category = request.data.get(' category'),
            discount_price=request.data.get('discount_price'),
            stock_quantity=request.data.get('stock_quantity'),
            weight=request.data.get('weight')
        )

        variants = request.data.get('variants', [])

        if variants:
            for variant in variants:
                ProductVariant.objects.create(
                    product=product,
                    #variant_name=variant.get('variant_name'),
                    price=variant.get('price'),
                    stock_quantity=variant.get('stock_quantity')
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

# Edit Product
class EditProductApi(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSeller]

    def put(self, request, id):

        try:
            product = Product.objects.get(
                id=id,
                seller=request.user.seller_profile
            )

        except Product.DoesNotExist:

            return Response(
                {'message': 'Product not found or not yours'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data

        product.productname = data.get('productname', product.productname)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.discount_price = data.get('discount_price', product.discount_price)
        product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
        product.weight = data.get('weight', product.weight)
        product.capacity = data.get('capacity', product.capacity)

        product.save()

        return Response(
            {
                'message': 'Product updated successfully',
                'product_id': product.id
            },
            status=status.HTTP_200_OK
        )


# Delete Product
class DeleteProductAPI(APIView):

    authentication_classes = [TokenAuthentication]
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
                    'message': 'Product not found or not yours'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        product.delete()

        return Response(
            {
                'message': 'Product deleted successfully',
                'product_id': id
            },
            status=status.HTTP_200_OK
        )


# Seller Product List
class SellerProductListAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSeller]

    def get(self, request):

        seller = request.user.seller_profile

        products = Product.objects.filter(seller=seller)

        data = []

        for p in products:

            data.append({
                "id": p.id,
                "productname": p.productname,
                "description": p.description,
                "price": p.price,
                "discount_price": p.discount_price,
                "stock_quantity": p.stock_quantity,
            })

        return Response(
            {
                "message": "Seller Products",
                "products": data
            },
            status=status.HTTP_200_OK
        )
    


class SellerDashboard(APIView):
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsSeller]

    def get(self,request):

        seller=request.user

        total_products=Product.objects.filter(seller=seller).count()

        available_products=Product.objects.filter(seller=seller,stock_quantity__gt=0).count()

        out_of_stock_products=Product.objects.filter(seller=seller,stock_quantity=0).count()

        total_orders=Order.objects.filter(product__seller=seller).count()

        return Response({
            "total_products":total_products,
            "available_products":available_products,
            "out_of_stock_products":out_of_stock_products,
            "total_orders":total_orders
        })



# SellerOrdersAPI



class SellerOrdersListAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSeller]

    def get(self, request):

        # Get orders for seller products
        orders = Order.objects.filter(seller=request.user).select_related(
            'user',
            'product',
            'payment',
            'address'
        ).order_by('-id')

        data = []

        for order in orders:

            data.append({

                "order_id": order.id,

                # CUSTOMER DETAILS
                "customer": order.user.name,

                # PRODUCT DETAILS
                "product": order.product.productname,

                "quantity": order.quantity,

                "total_price": order.total_price,

                # ORDER STATUS
                "order_status": order.status,

                # PAYMENT DETAILS
                "payment_method": order.payment.payment_method,

                "payment_status": order.payment.payment_status,

                # DELIVERY ADDRESS
                "delivery_address": {
                    "full_name": order.address.full_name,
                    "phone_number": order.address.phone_number,
                    "address_line": order.address.address_line,
                    "city": order.address.city,
                    "state": order.address.state,
                    "pincode": order.address.pincode
                },

                "ordered_at": order.ordered_at
            })

        return Response(
            {
                "total_orders_received": orders.count(),
                "orders": data
            },
            status=status.HTTP_200_OK
        )
    


