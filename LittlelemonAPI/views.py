from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from . import models
from decimal import Decimal
import datetime

# Authentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

# Throttle
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.decorators import throttle_classes

# Determine whether the user is admin
from rest_framework.permissions import IsAdminUser

# Manage users and group
from django.contrib.auth.models import User, Group

# Serialization
from . import serializers

# Pagination
from django.core.paginator import Paginator, EmptyPage

#Filtering
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

#Cart operations
from rest_framework import status
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import CartSerializer, OrderSerializer, MenuItemSerializer

class MenuItemsView(generics.ListCreateAPIView):
    queryset = models.MenuItem.objects.all()
    serializer_class = serializers.MenuItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['title']
    ordering_fields = ['price']
    # pagination_class = None # Disable pagination

@api_view(['GET'])
def all_menu_items(request):
    menu_items = models.MenuItem.objects.all()
    serializer = serializers.MenuItemSerializer(menu_items, many=True)
    return Response(serializer.data)

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminUser]  # Only allow admins to post
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permission() for permission in self.permission_classes]
        return []

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    user = request.user
    menu_item_id = request.data.get('menu_item_id')
    quantity = request.data.get('quantity', 1)  # Default to 1 if not provided
    try:
        menu_item = MenuItem.objects.get(id=menu_item_id)
    except MenuItem.DoesNotExist:
        return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)
    # Using get_or_create with default values for both unit_price and price
    cart, created = Cart.objects.get_or_create(
        user=user, 
        menuitem=menu_item, 
        defaults={
            'unit_price': menu_item.price, 
            'price': menu_item.price * quantity,  # Initial total price
            'quantity': quantity  # Use the requested quantity
        }
    )
    if not created:
        # Update the existing cart item
        cart.quantity += int(quantity)
        cart.price = cart.quantity * cart.unit_price
    cart.save()
    return Response({'message': 'Item added to cart'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    serializer = CartSerializer(cart_items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    if not cart_items:
        return Response({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    # Create an order
    order = Order(user=user, total=0)
    order.save()
    total = 0
    for item in cart_items:
        order_item = OrderItem(
            order=order,
            menuitem=item.menuitem,
            quantity=item.quantity,
            price=item.price,  # Total price for this item
            unit_price=item.unit_price  # Unit price for one item
        )
        order_item.save()
        total += item.price * item.quantity
    order.total = total
    order.save()
    # Clear the cart
    cart_items.delete()
    return Response({'message': 'Order placed successfully'}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_user_orders(request):
    user = request.user
    user_orders = Order.objects.filter(user=user)
    serializer = OrderSerializer(user_orders, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    else:
        return Response({'error': 'Invalid Credentials'}, status=400)

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not username or not email or not password:
        return Response({'error': 'Please provide all required fields'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, email=email, password=password)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def assign_order_to_delivery(request, order_id):
    user = request.user
    if not user.groups.filter(name='Manager').exists():
        return Response({"message": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    order = get_object_or_404(Order, pk=order_id)
    delivery_crew_id = request.data.get('delivery_crew_id')
    try:
        delivery_crew_member = User.objects.get(pk=delivery_crew_id)
        order.delivery_crew = delivery_crew_member
        order.save()
        return Response(OrderSerializer(order).data)
    except User.DoesNotExist:
        return Response({"message": "Delivery crew member not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    # Check if the user is part of the delivery crew
    if not request.user.groups.filter(name='Delivery crew').exists():
        return Response({"message": "You are not authorized."}, status=status.HTTP_403_FORBIDDEN)
    # Get the order
    order = get_object_or_404(Order, pk=order_id)
    # Update the order status
    order.is_delivered = True  # or use any other logic for status update
    order.save()
    return Response({"message": "Order status updated successfully."})

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])  # Only allow admins to post
def category(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view()
def home(request):
    return Response('The home view.', status.HTTP_200_OK)

# Test: throttle test
@api_view()
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def throttle_check(request):
    return Response({"message": "Throttle check."})

# Test: Change user's group only by admin
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAdminUser])
def manager_admin(request):
    username = request.data['username']
    message = 'User ' + username + ' '
    if username:
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name="Manager")
        if request.method == 'POST':
            managers.user_set.add(user)
            message += 'is set as manager.'
        elif request.method == 'DELETE':
            managers.user_set.remove(user)
            message += 'is deleted from manager group.'
        elif request.method == 'GET':
            serialized_item = serializers.UserSerializer(managers, many=True)
            return Response(serialized_item.data)
        return Response({"message": message})
    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAdminUser])
def group_view(request):
    if request.method == 'GET':
        serialized_item = serializers.GroupSerializer(Group.objects.all(), many=True)
        return Response(serialized_item.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category(request):
    if request.method == 'GET':
        items = models.Category.objects.all()
        serialized_item = serializers.CategorySerializer(items, many=True)
        return Response(serialized_item.data, status.HTTP_200_OK)
    if request.method == 'POST' and request.user.groups.filter(name='Manager').exists():
        serialized_item = serializers.CategorySerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_201_CREATED)
    return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)


#some legacy below
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_single(request, id):
    item = get_object_or_404(models.Category, pk=id)
    if request.method == 'GET':
        serialized_item = serializers.CategorySerializer(item)
        return Response(serialized_item.data, status.HTTP_200_OK)
    elif request.method == 'POST':
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
    if request.method == 'PUT':
        serialized_item = serializers.CategorySerializer(item, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'PATCH':
        serialized_item = serializers.CategorySerializer(item, data=request.data, partial=True)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'DELETE':
        item.delete()
        return Response(status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menuitems(request):
    if request.method == 'GET':
        items = models.MenuItem.objects.all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            items = items.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(",")
            items = items.order_by(*ordering_fields)
        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        serialized_item = serializers.MenuItemSerializer(items, many=True)
        return Response(serialized_item.data, status.HTTP_200_OK)
    if request.method == 'POST' and request.user.groups.filter(name='Manager').exists():
        serialized_item = serializers.MenuItemSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_201_CREATED)
    return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menuitems_single(request, id):
    item = get_object_or_404(models.MenuItem, pk=id)
    if request.method == 'GET':
        serialized_item = serializers.MenuItemSerializer(item)
        return Response(serialized_item.data, status.HTTP_200_OK)
    elif request.method == 'POST' or not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
    if request.method == 'PUT':
        serialized_item = serializers.MenuItemSerializer(item, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'PATCH':
        serialized_item = serializers.MenuItemSerializer(item, data=request.data, partial=True)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'DELETE':
        item.delete()
        return Response(status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manager_set(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
        else:
            return Response({"message": "Username is incorrect or not existed."}, status.HTTP_400_BAD_REQUEST)
        managers = Group.objects.get(name="Manager")
        managers.user_set.add(user)
        message = 'User ' + username + ' ' 'is set as manager.'
        return Response({"message": message}, status.HTTP_201_CREATED) 
    elif request.method == 'GET':
        managers = User.objects.filter(groups = Group.objects.get(name="Manager"))
        serialized_item = serializers.UserSerializer(managers, many=True)
        return Response(serialized_item.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def manager_delete(request, id):
    if request.user.groups.filter(name='Manager').exists():
        if request.method != 'DELETE':
            return Response({"message": "This endpoint only supports DELETE."}, status.HTTP_400_BAD_REQUEST) 
        user = get_object_or_404(User, id=id)
        if user.groups.filter(name='Manager').exists():
            managers = Group.objects.get(name="Manager")
            managers.user_set.remove(user)
            message = 'User ' + user.get_username + ' ' + 'is not manager now.'
            return Response({"message": message}, status.HTTP_200_OK)
        else:
            return Response({"message": "This user is not a manager"}, status.HTTP_400_BAD_REQUEST) 
    else:
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def delivery_set(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
        else:
            return Response({"message": "Username is incorrect or not existed."}, status.HTTP_400_BAD_REQUEST)
        crews = Group.objects.get(name="Delivery crew")
        crews.user_set.add(user)
        message = 'User ' + username + ' ' 'is set as delivery crew.'
        return Response({"message": message}, status.HTTP_201_CREATED) 
    elif request.method == 'GET':
        crews = User.objects.filter(groups = Group.objects.get(name="Delivery crew"))
        serialized_item = serializers.UserSerializer(crews, many=True)
        return Response(serialized_item.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def delivery_delete(request, id):
    if request.user.groups.filter(name='Manager').exists():
        if request.method != 'DELETE':
            return Response({"message": "This endpoint only supports DELETE."}, status.HTTP_400_BAD_REQUEST) 
        user = get_object_or_404(User, id=id)
        if user.groups.filter(name='Delivery crew').exists():
            crews = Group.objects.get(name="Delivery crew")
            crews.user_set.remove(user)
            message = 'User ' + user.get_username + ' ' + 'is not delivery crew now.'
            return Response({"message": message}, status.HTTP_200_OK)
        else:
            return Response({"message": "This user is not a delivery crew"}, status.HTTP_400_BAD_REQUEST) 
    else:
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
    
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def cart(request):
    if request.method == 'GET':
        try:
            cart = models.Cart.objects.get(user=request.user)
        except:
            return Response({"message": "The cart is empty."}, status.HTTP_400_BAD_REQUEST)
        serialized_item = serializers.CartSerializer(cart)
        return Response(serialized_item.data, status.HTTP_200_OK)
    if request.method == 'POST':
        if models.Cart.objects.filter(user=request.user).exists():
            return Response({"message": "The user has already a cart."}, status.HTTP_400_BAD_REQUEST)
        menuitem = request.data["menuitem"]
        quantity = request.data["quantity"]
        unit_price = models.MenuItem.objects.get(pk=menuitem).price
        price = Decimal(quantity) * unit_price
        data = {"menuitem_id": menuitem, 
                "quantity": quantity,
                "unit_price": unit_price,
                "price": price,
                "user_id": request.user.id,
        }
        serialized_item = serializers.CartSerializer(data=data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        message = 'Cart is created.'
        return Response({"message": message}, status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        cart = get_object_or_404(models.Cart, user=request.user)
        cart.delete()
        return Response(status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order(request):
    user = request.user
    if user.groups.filter(name='Delivery crew').exists():
        # If the user is part of the delivery crew, return only orders assigned to them
        assigned_orders = Order.objects.filter(delivery_crew=user)
        serializer = OrderSerializer(assigned_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif user.groups.filter(name='Manager').exists():
        # If the user is a manager, return all orders
        all_orders = Order.objects.all()
        serializer = OrderSerializer(all_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        # For other users (like customers), return only their orders
        customer_orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(customer_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])  # Only admin users can access this
def update_item_of_the_day(request, item_id):
    try:
        item = MenuItem.objects.get(pk=item_id)
        # Set all items' featured field to False
        MenuItem.objects.update(featured=False)
        # Set the selected item's featured field to True
        item.featured = True
        item.save()
        serializer = MenuItemSerializer(item)
        return Response(serializer.data)
    except MenuItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=404)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])  # Ensure only authenticated admins (managers) can access
def assign_to_delivery_crew(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        delivery_crew_group, created = Group.objects.get_or_create(name='Delivery crew')
        delivery_crew_group.user_set.add(user)
        return Response({'message': f'User {user.username} assigned to delivery crew'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order(request):
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = models.Order.objects.all()
            to_price = request.query_params.get('to_price')
            search = request.query_params.get('search')
            ordering = request.query_params.get('ordering')
            perpage = request.query_params.get('perpage', default=2)
            page = request.query_params.get('page', default=1)
            if to_price:
                orders = orders.filter(total__lte=to_price)
            if search:
                orders = orders.filter(status__icontains=search)
            if ordering:
                ordering_fields = ordering.split(",")
                orders = orders.order_by(*ordering_fields)
            
            paginator = Paginator(orders, per_page=perpage)
            try:
                orders = paginator.page(number=page)
            except EmptyPage:
                orders = []
            serialized_order = serializers.OrderSerializer(orders, many=True)
            return Response(serialized_order.data, status.HTTP_200_OK)
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = models.Order.objects.filter(delivery_crew=request.user)
            serialized_order = serializers.OrderSerializer(orders, many=True)
            return Response(serialized_order.data, status.HTTP_200_OK)
        else: # customer view
            if models.Order.objects.filter(user=request.user).exists():
                order = models.Order.objects.filter(user=request.user)
                serialized_order = serializers.OrderSerializer(order)
                return Response(serialized_order.data, status.HTTP_200_OK)
            else:
                return Response(status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        cart = get_object_or_404(models.Cart, user=request.user)
        # create order and orderitem
        orderitem_data = {
            "user_id": cart.user_id,
            "menuitem_id": cart.menuitem_id,
            "quantity": cart.quantity,
            "unit_price": cart.unit_price,
            "price": cart.price
        }
        serialized_orderitem = serializers.OrderItemSerializer(data=orderitem_data)
        serialized_orderitem.is_valid(raise_exception=True)
        serialized_orderitem.save()
        orderitem = models.OrderItem.objects.get(user=request.user, menuitem=cart.menuitem)
        order_data = {
            "user_id": cart.user_id,
            "total": cart.price,
            "orderitem_id": orderitem.id,
        }
        serialized_order = serializers.OrderSerializer(data=order_data)
        serialized_order.is_valid(raise_exception=True)
        serialized_order.save()
        cart.delete()
        message = 'Order is created.'
        return Response({"message": message}, status.HTTP_201_CREATED)
    return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN) 

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order_single(request, id):
    order = get_object_or_404(models.Order, pk=id)
    if request.method == 'GET':
        if order.user != request.user:
            return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
        serialized_order = serializers.OrderSerializer(order)
        return Response(serialized_order.data, status.HTTP_200_OK)
    if request.method == 'PUT':
        # only manager could perform PUT action
        if not request.user.groups.filter(name='Manager').exists():
            return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN) 
        serialized_item = serializers.OrderSerializer(order, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'PATCH':
        if request.user.groups.filter(name='Delivery crew').exists(): 
            # delivery crew can only PATCH the order
            if order.delivery_crew != request.user:
                return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
            # only status of the order can be changed
            deliverystatus = request.data["status"]
            status_data = {"status": deliverystatus}
            serialized_item = serializers.OrderSerializer(order, data=status_data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
        if request.user.groups.filter(name='Manager').exists():
            serialized_item = serializers.OrderSerializer(order, data=request.data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN) 
    if request.method == 'DELETE':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
        order.delete()
        return Response(status.HTTP_204_NO_CONTENT)