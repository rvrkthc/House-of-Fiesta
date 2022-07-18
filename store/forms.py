from django import forms
from django.contrib.auth.models import User

from .models import Order


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        self.product = kwargs.get('product')
        if self.product:
            del kwargs['product']
        super(CartAddForm, self).__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        available_stock = self.product.available_stock()
        if quantity > available_stock:
            raise forms.ValidationError("""
                                        You may only order up to %d units of
                                        thisitem due to stock availability.
                                        """
                                        % available_stock)
        return quantity


class RegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()

        # Validate passwords
        password = cleaned_data['password']
        confirm_password = cleaned_data['confirm_password']
        if password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['billing_first_name', 'billing_last_name', 'billing_address',
                  'billing_city', 'billing_province', 'billing_region',
                  'billing_zip', 'billing_phone',
                  'shipping_first_name', 'shipping_last_name',
                  'shipping_address', 'shipping_city', 'shipping_province',
                  'shipping_region', 'shipping_phone', 'shipping_zip']


class PersonalDetailsChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
