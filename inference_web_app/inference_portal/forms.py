from django import forms

from . import models

class LoginForm(forms.Form):
    email = forms.CharField(label="Email", max_length=100)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    about = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

    class Meta:
        model = models.User
        fields = ['email', 'password', 'name']
        labels = {
            'name': 'Name',
            'email': 'Email',
            'password': 'Password',
        }


class ModelInferenceAppForm(forms.ModelForm):
    class Meta:
        model = models.ModelInference
        fields = ['name', 'description', 'category', 'status', 'inference_endpoint',
                  'release_as_web_app', 'web_app_price_per_use', 
                  'release_as_binary', 'binary_image', 'binary_image_price', 
                  'release_as_plugin', 'list_of_plugins', 'plugin_price_per_use', 
                  'release_as_api', 'api_price_per_use', 
                  'terms']

    def __init__(self, *args, **kwargs):
        super(ModelInferenceAppForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        
        self.fields['release_as_web_app'].widget.attrs['class'] = 'form-check-input'
        self.fields['release_as_binary'].widget.attrs['class'] = 'form-check-input'
        self.fields['release_as_plugin'].widget.attrs['class'] = 'form-check-input'
        self.fields['release_as_api'].widget.attrs['class'] = 'form-check-input'


class PaymentAddressForm(forms.ModelForm):
    class Meta:
        model = models.PaymentAddress
        fields = ['tfuel_address', 'bank_id', 'notes']
    
    def __init__(self, *args, **kwargs):
        super(PaymentAddressForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
