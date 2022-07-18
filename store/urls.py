
from django.urls.conf import path

from django.contrib.auth import views as auth_views

from . import views

app_name = 'store'
urlpatterns = [
    path('', views.index, name='index'),
    path('products/', views.products, name='products'),
    path('products/<slug:category__slug>/', views.products, name='products'),
    path('products/add-to-cart/<slug:stock_keeping_unit>/',
         views.add_to_cart, name='add_to_cart'),
    path('products/remove-from-cart/<slug:stock_keeping_unit>/',
         views.remove_from_cart, name='remove_from_cart'),
    path('my-cart/', views.view_cart, name='view_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<slug:stock_keeping_unit>/',
         views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<slug:stock_keeping_unit>/',
         views.remove_from_wishlist, name='remove_from_wishlist'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout-done/', views.checkout_done, name='checkout_done'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/',
         auth_views.LoginView.as_view(
             template_name='store/login.html',
             next_page='/'),
         name='login'),
    path('logout/',
         auth_views.LogoutView.as_view(
              template_name='store/logged_out.html'),
         name='logout'),
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='store/password_change_form.html',
             success_url='/password-change/done/'),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='store/password_change_done.html'),
         name='password_change_done'),

    # Other account related
    path('personal-details-change/', views.personal_details_change,
         name='personal_details_change'),
]
