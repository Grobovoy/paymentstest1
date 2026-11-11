from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("name", models.CharField(blank=True, default="", max_length=120)),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="TopUpOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("offer_id", models.CharField(blank=True, default="", max_length=64)),
                ("invoice_id", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("payment_url", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("created", "created"), ("pending", "pending"), ("paid", "paid"), ("failed", "failed")], default="created", max_length=16)),
                ("raw_response", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="orders", to="shop.profile")),
            ],
        ),
    ]
