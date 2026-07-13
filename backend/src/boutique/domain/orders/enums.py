from enum import StrEnum


class OrderStatus(StrEnum):
    CREATED = "created"
    INVOICED = "invoiced"
    PROCESSING = "processing"
    PENDING = "pending"
    APPROVED = "approved"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    UNAVAILABLE = "unavailable"
    CANCELED = "canceled"
