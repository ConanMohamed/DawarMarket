from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem, Order

@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """ تحديث السعر الكلي بعد إضافة أو حذف عنصر من الطلب """
    order = instance.order
    order.total_price = sum(item.quantity * item.unit_price for item in order.items.all())
    order.save(update_fields=['total_price'])
