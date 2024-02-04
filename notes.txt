# LittlelemonAPI project

#install packages:
pip install djangorestframework
pip install djangorestframework-simplejwt

#Keys:
Username: admin
Password: 123
Token: 633434be6216dac89d4a48b27f2a50e9fdd04eeb

Manager:
Username: manager1
Password: )D;12Xe2
Token: d8e18aa289f0958919ba47fd526dadf2439d9d60

Delivery crew:
Username: delivery1
Password: YzQ267:g
Token: 1bfd779974cfa9e11ea40dea463089bbbaccadb7

Customer:
Username: customer1
Password: 42Bu£5+K
Token: 20a23e2acdcbdbafd6c037dbe6fca357a40c9c7f

## endpoints tested in Insomnia (please ensure that you added appropriate Bearer Token):

1.	The admin can assign users to the manager group
POST http://127.0.0.1:8000/api/groups/manager/users
JSON:
{
  "username": "newuser"
}

2.	You can access the manager group with an admin token
GET http://127.0.0.1:8000/api/groups/manager/users

3.	The admin can add menu items
POST http://127.0.0.1:8000/api/menu-items
JSON:
{
    "title": "Leftovers",
    "price": 9.99,
    "featured": false,
    "category_id": 6
}

4.	The admin can add categories
POST http://127.0.0.1:8000/api/category
JSON:
{
    "slug": "very-new-category",
    "title": "Very New Category"
}

5/12.	Managers/Customers can log in using their username and password and get access tokens
POST http://127.0.0.1:8000/api/login/
JSON:
{
    "username": "customer1",
    "password": "42Bu£5+K"
}

6.	Managers can update the item of the day
PATCH http://127.0.0.1:8000/api/menu-items/12/feature/

7.	Managers can assign users to the delivery crew
PATCH http://127.0.0.1:8000/api/assign-to-delivery-crew/5/

8.	Managers can assign orders to the delivery crew
PATCH http://127.0.0.1:8000/api/orders/5/assign-delivery/
JSON:
{
    "delivery_crew_id": 4
}

9.	The delivery crew can access orders assigned to them
GET http://127.0.0.1:8000/api/orders

10.	The delivery crew can update an order as delivered
PATCH http://127.0.0.1:8000/api/orders/6/update-status/
{
    "is_delivered": true
}

11.	Customers can register
POST http://127.0.0.1:8000/api/register/
JSON:
{
    "username": "newuser2",
    "email": "newuser@example.com",
    "password": "SecurePassword123"
}

13.	Customers can browse all categories
GET http://127.0.0.1:8000/api/category

14.	Customers can browse all the menu items at once
GET http://127.0.0.1:8000/api/all-menu-items

15.	Customers can browse menu items by category
GET http://127.0.0.1:8000/api/menu-items?category=9

16.	Customers can paginate menu items
GET http://127.0.0.1:8000/api/menu-items?page=2&perpage=5

17.	Customers can sort menu items by price
GET http://127.0.0.1:8000/api/menu-items?ordering=price
GET http://127.0.0.1:8000/api/menu-items?ordering=-price

18.	Customers can add menu items to the cart
POST http://127.0.0.1:8000/api/add-to-cart/
JSON:
{
    "menu_item_id": 1,
    "quantity": 2
}

19.	Customers can access previously added items in the cart
GET http://127.0.0.1:8000/api/view-cart/

20.	Customers can place orders
POST http://127.0.0.1:8000/api/place-order/

21.	Customers can browse their own orders
GET http://127.0.0.1:8000/api/user-orders/