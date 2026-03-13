from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0003_hotel_price_per_night'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='price_currency',
            field=models.CharField(
                choices=[('INR', 'Indian Rupee'), ('USD', 'US Dollar'), ('EUR', 'Euro'), ('ISK', 'Icelandic Króna'), ('CHF', 'Swiss Franc')],
                default='INR',
                max_length=3,
            ),
        ),
    ]
