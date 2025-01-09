from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'
    
    email = models.EmailField(unique=True)

class DataFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    data_json = models.JSONField(default=dict, null=True)
    columns = models.JSONField(default=list, null=True)
    analysis_results = models.JSONField(default=dict, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
class MyModel(models.Model):
         name = models.CharField(max_length=100)
         description = models.TextField()