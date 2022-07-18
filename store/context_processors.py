from django.conf import settings
from django.db.models import Count

from .models import Product


def store_settings(request):
    return {'DELIVERY_FEE': settings.DELIVERY_FEE}


def cart(request):
    """
    Returns a 'cart' including its products for the template context.
    If it does not exist, then the cart will be initialized in the session.
    """
    if 'cart' not in request.session:
        request.session['cart'] = {}

    context_cart = request.session['cart']
    subtotal = 0
    total_qty = 0

    if len(context_cart) > 0:
        # If there are items in the cart,
        # Fetch product objects referred in cart
        products_in_cart = Product.objects.filter(pk__in=context_cart.keys()) \
                                          .prefetch_related('productimage_set') \
                                          .annotate(num_images=Count('productimage'))
        products_in_cart = {
            product.stock_keeping_unit: product
            for product in products_in_cart}
        # Associate the product objecs to their cart entries
        context_cart = {
            stock_keeping_unit: {
                'quantity': context_cart[stock_keeping_unit],
                'product': products_in_cart[stock_keeping_unit]}
            for stock_keeping_unit in context_cart}
        # Calculate the total
        for stock_keeping_unit, item in context_cart.items():
            total_qty += item['quantity']
            subtotal += item['quantity'] * item['product'].unit_price

    return {'cart': context_cart,
            'cart_total_qty': total_qty,
            'cart_subtotal': subtotal,
            'cart_total': subtotal + settings.DELIVERY_FEE}
