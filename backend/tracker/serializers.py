from rest_framework import serializers

from .models import (
    Product,
    PriceHistory,
    StockHistory,
    ScrapeAttempt,
)


class ProductSerializer(serializers.ModelSerializer):

    price = serializers.DecimalField(
        source="current_price",
        max_digits=10,
        decimal_places=2,
        allow_null=True,
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "store_product_id",
            "name",
            "brand",
            "category",
            "sku",
            "url",
            "image",
            "seller",
            "price",
            "original_price",
            "deal_price",
            "discount",
            "stock",
            "delivery",
            "description",
            "about",
            "specifications",
            "is_tracked",
            "last_scraped_at",
        ]


class PriceHistorySerializer(
    serializers.ModelSerializer
):
    date = serializers.DateTimeField(
        source="scraped_at",
        format="%Y-%m-%d %H:%M:%S",
    )

    class Meta:
        model = PriceHistory

        fields = [
            "date",
            "price",
        ]


class StockHistorySerializer(
    serializers.ModelSerializer
):
    time = serializers.DateTimeField(
        source="scraped_at",
        format="%Y-%m-%d %H:%M:%S",
    )

    status = serializers.CharField(
        source="stock"
    )

    class Meta:
        model = StockHistory

        fields = [
            "time",
            "status",
            "note",
        ]


class ScrapeAttemptSerializer(
    serializers.ModelSerializer
):
    time = serializers.DateTimeField(
        source="created_at",
        format="%Y-%m-%d %H:%M:%S",
    )

    attempt = serializers.IntegerField(
        source="attempt_number"
    )

    product = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    productId = serializers.IntegerField(
        source="product.id",
        read_only=True,
    )

    duration = serializers.SerializerMethodField()

    class Meta:
        model = ScrapeAttempt

        fields = [
            "id",
            "productId",
            "product",
            "time",
            "attempt",
            "status",
            "details",
            "duration",
        ]

    def get_duration(self, obj):

        if obj.duration_ms is None:
            return None

        return f"{obj.duration_ms}ms"
