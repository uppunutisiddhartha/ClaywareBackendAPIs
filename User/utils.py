from datetime import timedelta
from django.utils import timezone


def current_location(status):

    locations = {
        "PLACED": "Order Confirmed",
        "PACKED": "ClayWare Warehouse",
        "SHIPPED": "Regional Hub",
        "OUT_FOR_DELIVERY": "Out for Delivery",
        "DELIVERED": "Delivered",
        "CANCELLED": "Order Cancelled",
        "RETURNED": "Returned",
    }

    return locations.get(status, "Processing")


def expected_delivery(order):

    if order.status == "DELIVERED":
        return order.created_at.strftime("%d %b %Y")

    expected = order.created_at + timedelta(days=5)

    return expected.strftime("%d %b %Y")


def get_tracking(status):

    stages = [
        ("PLACED", "Order Placed"),
        ("PACKED", "Packed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out For Delivery"),
        ("DELIVERED", "Delivered"),
    ]

    completed = {
        "PLACED": 1,
        "PACKED": 2,
        "SHIPPED": 3,
        "OUT_FOR_DELIVERY": 4,
        "DELIVERED": 5,
    }

    current = completed.get(status, 0)

    tracking = []

    for index, (_, title) in enumerate(stages, start=1):

        tracking.append({

            "stage": title,

            "done": index <= current,

            "current": index == current,

            "date": (
                timezone.localtime().strftime("%d %b %Y")
                if index <= current else None
            )

        })

    return tracking