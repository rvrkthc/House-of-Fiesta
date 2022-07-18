from django.conf import settings
from django.contrib import admin

from django.db.models import Count

from django_summernote import admin as summernote_admin

from .models import Category, Product, Location, Inventory, Order, OrderItem, ProductImage, WishlistItem

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ['name']}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class InventoryProductInline(admin.TabularInline):
    model = Inventory
    min_num = 1
    extra = 0


class ProductImageInline(admin.StackedInline):
    model = ProductImage
    min_num = 1
    extra = 0


@admin.register(Product)
class ProductAdmin(summernote_admin.SummernoteModelAdmin):
    list_display = ('stock_keeping_unit', 'image', 'title',
                    'is_enabled', 'available_stock',)
    list_filter = ('is_enabled',)
    search_fields = ('title', 'stock_keeping_unit',)
    fieldsets = (('Primary Details', {'fields': ('category', 'title',
                                                 'stock_keeping_unit',
                                                 'body',)}),
                 ('Pricing', {'fields': ('unit_cost', 'unit_price',
                                         'is_enabled',)}))
    summernote_fields = ('body',)
    prepopulated_fields = {'stock_keeping_unit': ['title', ]}
    inlines = (ProductImageInline, InventoryProductInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('inventory_set', 'productimage_set') \
                       .annotate(num_images=Count('productimage'))

    @admin.display
    def image(self, object):
        from django.utils.html import mark_safe
        if object.num_images > 0:
            return mark_safe('<img src="%s" height="50rem" width="50rem"/>' %
                             object.productimage_set.all()[0].image.url)
        return mark_safe('<img src="%s" height="50rem" width="50rem"/>' %
                         '/static/store/img/placeholder-200x200.jpg')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wished_by', 'product__title')
    search_fields = ('wished_by__last_name', 'wished_by__first_name',
                     'product__title')

    def get_queryset(self, request):
        queryset = super(WishlistItemAdmin, self).get_queryset(request)
        return queryset.select_related('wished_by', 'product')

    @admin.display(ordering='product__title', description='Product')
    def product__title(self, obj):
        return obj.product.title


class OrderItemOrderInline(admin.TabularInline):
    model = OrderItem
    min_num = 1
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'placed_by', 'status', 'total',)
    list_filter = ('status',)
    search_fields = ('id',)
    fieldsets = (('Primary Details', {'fields': ('placed_by', 'status')}),
                 ('Billing', {'fields': ('billing_first_name',
                                         'billing_last_name',
                                         'billing_address', 'billing_city',
                                         'billing_province', 'billing_region',
                                         'billing_zip', 'billing_phone',)}),
                 ('Shipping', {'fields': ('shipping_first_name',
                                          'shipping_last_name',
                                          'shipping_address', 'shipping_city',
                                          'shipping_province', 'shipping_region',
                                          'shipping_zip', 'shipping_phone',)}),
                 ('Delivery', {'fields': ('delivery_fee',)}))
    inlines = (OrderItemOrderInline,)

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        return queryset.select_related('placed_by') \
            .prefetch_related('orderitem_set')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(OrderAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['delivery_fee'].initial = settings.DELIVERY_FEE
        return form

    @admin.display(ordering='placed_by__last_name')
    def placed_by(self, object):
        return object.placed_by.last_name + ', ' + object.placed_by.first_name
