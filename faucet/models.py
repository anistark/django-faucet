from django.db import models

class TransactionLog(models.Model):
    wallet_address = models.CharField(max_length=42)
    transaction_id = models.CharField(max_length=66, null=True, blank=True)
    status = models.CharField(max_length=10)  # success or failed
    timestamp = models.DateTimeField(auto_now_add=True)
