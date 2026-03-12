from django.db import models

class Campaign(models.Model):
    subject = models.CharField(max_length=255)
    body_text = models.TextField()
    target_tag = models.CharField(max_length=255, blank=True, help_text="Leave blank to send to all contacts")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Draft")

    def __str__(self):
        return f"{self.subject} ({self.status})"
