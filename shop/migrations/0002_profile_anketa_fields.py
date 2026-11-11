from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("shop", "0001_initial")]
    operations = [
        migrations.AddField(model_name="profile", name="password", field=models.CharField(blank=True, default="", max_length=128)),
        migrations.AddField(model_name="profile", name="gender", field=models.IntegerField(choices=[(1, "Мужской"), (2, "Женский")], default=2)),
        migrations.AddField(model_name="profile", name="age", field=models.PositiveSmallIntegerField(default=25)),
        migrations.AddField(model_name="profile", name="city", field=models.CharField(blank=True, default="Москва", max_length=80)),
        migrations.AddField(model_name="profile", name="about", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="profile", name="title", field=models.CharField(blank=True, default="Ищу общение", max_length=160)),
        migrations.AddField(model_name="profile", name="is_public", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="profile", name="online", field=models.BooleanField(default=True)),
        migrations.AlterField(
            model_name="topuporder",
            name="status",
            field=models.CharField(
                choices=[("created", "created"), ("pending", "pending"), ("paid", "paid"), ("failed", "failed"), ("expired", "expired")],
                default="created",
                max_length=16,
            ),
        ),
    ]
