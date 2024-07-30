from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(blank=False, null=False, unique=True)
    name = models.CharField(max_length=128, unique=False)
    username = models.CharField(max_length=128, unique=False)
    profile_type = models.CharField(max_length=20, null=True, blank=True, choices=[('user', 'user'), ('developer', 'developer')])
    about = models.TextField()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if self.username is None:
            self.username = (self.first_name[0] + self.last_name.replace(' ', '')).lower()
        super().save(*args, **kwargs)


class PluginChoices(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name


class ModelInference(models.Model):
    name = models.CharField(verbose_name='Name', max_length=100)
    description = models.TextField(verbose_name='Details of your AI Model and its capabilities')
    category = models.CharField(verbose_name='Which category does this AI model belong to?', max_length=20, choices=[('Medical', 'Medical'), ('Finance', 'Finance'), ('Image', 'Image')])
    status = models.CharField(verbose_name='Current Development Status', max_length=20, choices=[('Development', 'Development'), ('Staging', 'Staging'), ('Production', 'Production')])

    inference_endpoint = models.CharField(verbose_name='Provide inference endpoint at Theta EdgeCloud', max_length=512, blank=True, null=True)

    release_as_web_app = models.BooleanField(verbose_name='Do you want to release it as readymade web app?', default=False)
    web_app_access_url = models.CharField(verbose_name='Web App Access', max_length=512, blank=True, null=True)
    web_app_price_per_use = models.FloatField(verbose_name='Cost of plugin per call')

    release_as_binary = models.BooleanField(verbose_name='Do you want to release it as binary image that users can deploy themselves?', default=False)
    binary_image = models.CharField(verbose_name='Access URL or Repository of Binary Image', max_length=512, blank=True, null=True)
    binary_image_price = models.FloatField(verbose_name='One-time cost of binary image')

    release_as_plugin = models.BooleanField(verbose_name='Do you want to release it as different plugins?', default=False)
    list_of_plugins = models.ManyToManyField(PluginChoices, verbose_name='Which plateforms you want to distribute to?')
    plugin_price_per_use = models.FloatField(verbose_name='Cost of plugin per call', )

    release_as_api = models.BooleanField(verbose_name='Do you want to release it as REST API?', default=False)
    api_price_per_use = models.FloatField(verbose_name='Cost of API per call')

    terms = models.TextField(verbose_name='Terms & Conditions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ModelInferencePlugin(models.Model):
    file_path = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    model_inference = models.ForeignKey(ModelInference, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + " for " + self.model_inference.name


class PaymentAddress(models.Model):
    notes = models.TextField(verbose_name='My Notes')

    tfuel_address = models.CharField(verbose_name='TFUEL Address', max_length=512, blank=True, null=True)
    tfuel_balance = models.FloatField(default=0)

    bank_id = models.CharField(verbose_name='Bank ID', max_length=512, blank=True, null=True)
    bank_balance = models.FloatField(default=0)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class OrderTransaction(models.Model):
    model_inference = models.ForeignKey(ModelInference, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    payment_type = models.CharField(max_length=20, choices=[('TFUEL', 'TFUEL'), ('USD', 'USD')])
    service_name = models.CharField(verbose_name='Service Name', max_length=32)
    service_type = models.CharField(verbose_name='Service Type', max_length=32)
    description = models.TextField()

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.buyer.name + ' purchased ' + self.model_inference.name + ' from ' + self.seller.name


class RESTAPI(models.Model):
    order = models.ForeignKey(OrderTransaction, on_delete=models.CASCADE)
    api_endpoint = models.CharField(verbose_name='API Endpoint', max_length=512)
    api_key = models.CharField(verbose_name='API Key', max_length=512)
    api_secret = models.CharField(verbose_name='API Secret', max_length=512)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Blocked', 'Blocked')])
    description = models.TextField()

    def __str__(self):
        return  ' API for ' + self.order.buyer.name +  ' for ' + self.order.model_inference.name
