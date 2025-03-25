# store/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def update_order_total(sender, instance, created, **kwargs):
    if created:
        instance.calculate_total_price(save=True)
