from django.urls import path
from . import views
from .views import MenuItemsView, add_to_cart, view_cart, place_order, view_user_orders, assign_to_delivery_crew, update_item_of_the_day

urlpatterns = [  
    # Throttle check
    path('throttle', views.throttle_check),
    
    # Category endpoints
    path('category', views.category, name='category'),
    path('category/<int:id>', views.category_single),

    # Menu-items endpoints
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:id>', views.menuitems_single),
    path('all-menu-items', views.all_menu_items, name='all-menu-items'),
    path('menu-items/<int:item_id>/feature/', update_item_of_the_day, name='update-item-of-the-day'),

    # User group management endpoints
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('groups/manager/users', views.manager_set),
    path('groups/manager/users/<int:pk>', views.manager_delete),
    path('groups/delivery-crew/users', views.delivery_set),
    path('groups/delivery-crew/<int:pk>', views.delivery_delete),
    path('assign-to-delivery-crew/<int:user_id>/', assign_to_delivery_crew, name='assign-to-delivery-crew'),

    # Cart management endpoints 
    path('cart/menu-items', views.cart),
    path('add-to-cart/', add_to_cart, name='add-to-cart'),
    path('view-cart/', view_cart, name='view-cart'),

    # Order management endpoints
    path('orders', views.order),
    path('orders/<int:id>', views.order_single),
    path('place-order/', place_order, name='place-order'),
    path('user-orders/', view_user_orders, name='user-orders'),
    path('orders/<int:order_id>/assign-delivery/', views.assign_order_to_delivery, name='assign-order-to-delivery'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update-order-status'),
    
    # Test for admin access
    path('admin/users', views.manager_admin),
    
    # Test for serialization of Group
    path('admin/group', views.group_view),
]