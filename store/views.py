from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.db.models import Count, Q, Sum

from .models import Product, Category, OrderItem, WishlistItem
from .forms import CartAddForm, CheckoutForm, RegistrationForm, \
    PersonalDetailsChangeForm


def index(request):
    """
    Food store home page.
    """
    top_product_list = Product.objects.filter(is_enabled=True) \
                                      .prefetch_related('productimage_set', 'inventory_set') \
                                      .annotate(num_images=Count('productimage'),
                                                total_inv=Sum('inventory__units_in_stock')) \
                                      .filter(total_inv__gt=0)[:5]
    context = {'top_product_list': top_product_list}
    return render(request, 'store/index.html', context)


def products(request, category__slug=None):
    """
    Products listing. Filters by category.
    If no category is given, all products will be listed.
    """
    # Fetch categories
    category_list = Category.objects.all()
    # Fetch products
    product_list = Product.objects.filter(is_enabled=True) \
                                  .prefetch_related('productimage_set', 'inventory_set') \
                                  .annotate(num_images=Count('productimage'),
                                            total_inv=Sum('inventory__units_in_stock')) \
                                  .filter(total_inv__gt=0)
    # TODO: Dummy top rated and recently added products
    top_product_list = product_list[:3]
    recent_product_list = product_list.order_by('-stock_keeping_unit')[:3]
    # Selected category
    selected_category = None

    if category__slug:
        selected_category = Category.objects.get(slug=category__slug)
        product_list = product_list.filter(category=selected_category)

    else:
        try:
            product_list = product_list.filter(
                title__icontains=request.GET['search'])
        except KeyError:
            pass

    context = {
        'category_list': category_list,
        'selected_category': selected_category,
        'product_list': product_list,
        'top_product_list': top_product_list,
        'recent_product_list': recent_product_list
    }
    return render(request, 'store/products.html', context)


def add_to_cart(request, stock_keeping_unit):
    """
    Endpoint for adding a product to cart.
    """
    # Fetch product
    product = Product.objects.select_related('category') \
                             .prefetch_related('inventory_set',
                                               'productimage_set') \
                             .annotate(num_images=Count('productimage')) \
                             .get(stock_keeping_unit=stock_keeping_unit)
    related_product_list = Product.objects.filter(~Q(stock_keeping_unit=stock_keeping_unit) &
                                                  Q(category=product.category)) \
                                          .prefetch_related('productimage_set', 'inventory_set') \
                                          .annotate(num_images=Count('productimage'),
                                                    total_inv=Sum('inventory__units_in_stock')) \
                                          .filter(total_inv__gt=0)[:4]

    if request.method == 'POST':
        add_to_cart_form = CartAddForm(request.POST, product=product)
        if add_to_cart_form.is_valid():
            # add item to cart in session
            cart = request.session['cart']
            cart[stock_keeping_unit] = \
                add_to_cart_form.cleaned_data['quantity']
            request.session['cart'] = cart

            # redirect back to store in product's category
            return HttpResponseRedirect(reverse('store:products'))

    else:
        # If the item is already in cart, use its current quantity.
        try:
            add_to_cart_form = CartAddForm({
                'quantity': request.session['cart'][stock_keeping_unit]})
        except KeyError:
            add_to_cart_form = CartAddForm()

    context = {'product': product,
               'add_to_cart_form': add_to_cart_form,
               'related_product_list': related_product_list}
    return render(request, 'store/product.html', context)


def remove_from_cart(request, stock_keeping_unit):
    """
    Endpoint for removing an item from the cart.
    """
    cart = request.session['cart']
    del cart[stock_keeping_unit]
    request.session['cart'] = cart
    return HttpResponseRedirect(reverse('store:view_cart'))


def view_cart(request):
    """
    Customer's cart view.
    """
    # Just render the page. The context processor for cart
    # will place everything in the context.
    return render(request, 'store/cart.html', {})


@login_required
def wishlist(request):
    """
    Customer's wishlist view.
    """
    wishlistitem_list = WishlistItem.objects.filter(wished_by=request.user)
    context = {'wishlistitem_list': wishlistitem_list}
    return render(request, 'store/wishlist.html', context)


@login_required
def add_to_wishlist(request, stock_keeping_unit):
    """
    Endpoint for adding an item to the user's wishlist.
    """
    product = Product.objects.get(pk=stock_keeping_unit)
    wishlistitem = WishlistItem(wished_by=request.user,
                                product=product)
    wishlistitem.save()
    return HttpResponseRedirect(reverse('store:products'))


@login_required
def remove_from_wishlist(request, stock_keeping_unit):
    """
    Endpoint for removing an item from the user's wishlist.
    """
    product = Product.objects.get(pk=stock_keeping_unit)
    wishlistitem = WishlistItem.objects.get(wished_by=request.user,
                                            product=product)
    wishlistitem.delete()
    return HttpResponseRedirect(reverse('store:wishlist'))


def checkout(request):
    """
    Endpoint for placing an order.
    """
    cart = request.session['cart']

    # If there are contents in cart, proceed to processing of checkout form
    if len(cart) > 0:
        if request.method == 'POST':
            checkout_form = CheckoutForm(request.POST)
            if checkout_form.is_valid():
                # Construct the order instance from:
                # 1 - The submitted checkout form
                order = checkout_form.instance
                order.status = 'NW'
                # 2 - The current logged-in user, if there is
                if request.user.is_authenticated:
                    order.placed_by = request.user
                # 3 - Delivery Fee
                order.delivery_fee = settings.DELIVERY_FEE
                order.save()
                # 4 - The order items from the cart
                for stock_keeping_unit, quantity in cart.items():
                    product = Product.objects.get(pk=stock_keeping_unit)
                    order_item = OrderItem(order=order,
                                           product=product,
                                           unit_price=product.unit_price,
                                           quantity=quantity)
                    order_item.save()
                    # Deduct from product inventory
                    available_inventory = product.inventory_set.filter(units_in_stock__gt=0)[0]
                    available_inventory.units_in_stock -= quantity
                    available_inventory.save()
                del request.session['cart']

                return HttpResponseRedirect(reverse('store:checkout_done'))

        else:
            checkout_form = CheckoutForm()

        context = {'checkout_form': checkout_form}
        return render(request, 'store/checkout.html', context)

    # If there are no contents in cart
    return render(request, 'store/checkout_cart_empty.html', {})


def checkout_done(request):
    """
    Thank you page.
    """
    return render(request, 'store/checkout_done.html', {})


def register(request):
    """
    Registration page.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.instance
            User.objects.create_user(first_name=user.first_name,
                                     last_name=user.last_name,
                                     email=user.email,
                                     username=user.username,
                                     password=user.password)
            return HttpResponseRedirect(reverse('store:login'))

    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'store/register.html', context)


@login_required
def personal_details_change(request):
    """
    Endpoint for changing a user's personal details.
    """
    if request.method == 'POST':
        form = PersonalDetailsChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse('store:personal_details_change'))

    else:
        form = PersonalDetailsChangeForm(instance=request.user)

    context = {'form': form}
    return render(request, 'store/personal_details_change.html', context)
