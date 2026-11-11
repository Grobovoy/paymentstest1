from django.db import models


class Profile(models.Model):
    GENDER_CHOICES = [(1, "Мужской"), (2, "Женский")]
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True, default="")
    password = models.CharField(max_length=128, blank=True, default="")  # demo only
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gender = models.IntegerField(choices=GENDER_CHOICES, default=2)
    age = models.PositiveSmallIntegerField(default=25)
    city = models.CharField(max_length=80, blank=True, default="Москва")
    about = models.TextField(blank=True, default="")
    title = models.CharField(max_length=160, blank=True, default="Ищу общение")
    is_public = models.BooleanField(default=True)
    online = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or self.email}"


class TopUpOrder(models.Model):
    STATUS_CHOICES = [
        ("created", "created"),
        ("pending", "pending"),
        ("paid", "paid"),
        ("failed", "failed"),
        ("expired", "expired"),
    ]
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="orders")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")
    offer_id = models.CharField(max_length=64, blank=True, default="")
    invoice_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    payment_url = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="created")
    raw_response = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.profile_id} {self.amount} {self.status}"
