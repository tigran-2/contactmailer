from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=255, blank=True)
    tags = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"
