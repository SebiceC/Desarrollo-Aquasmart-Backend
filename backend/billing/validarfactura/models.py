from django.db import models

class InvoiceApi(models.Model):
    token = models.TextField()
    refresh = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True)
    def __str__(self): 
        return "Tokens" 
    
    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
         