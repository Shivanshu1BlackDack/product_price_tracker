from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, unique=True)

    url = models.URLField()
    image = models.CharField(max_length=255, blank=True)

    seller = models.CharField(max_length=150, blank=True)

    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    store_product_id = models.PositiveIntegerField(
    unique=True,
    null=True,
    blank=True,
    )
    
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    deal_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    stock = models.CharField(max_length=50, blank=True)

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    rating_count = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    delivery = models.CharField(max_length=255, blank=True)

    description = models.TextField(blank=True)
    about = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)

    is_tracked = models.BooleanField(default=False)

    last_scraped_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_history",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.price}"


class StockHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_history",
    )

    stock = models.CharField(max_length=50)
    note = models.CharField(max_length=255, blank=True)

    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.stock}"


class ScrapeAttempt(models.Model):
    STATUS_CHOICES = [
        ("Success", "Success"),
        ("Retried", "Retried"),
        ("Failed", "Failed"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="scrape_attempts",
    )

    attempt_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
    )

    details = models.TextField(blank=True)

    duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - Attempt {self.attempt_number}"
