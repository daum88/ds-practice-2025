# locustfile.py
from locust import HttpUser, task, between

class NonFraudulentUser(HttpUser):
    """Simulate non-fraudulent orders for distinct books."""
    wait_time = between(3, 5)

    @task
    def order_a(self):
        order_data = {
            "orderId": "order1",
            "user": {
                "name": "Alice",
                "contact": "123 Main St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book A", "quantity": 1}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)

    @task
    def order_b(self):
        order_data = {
            "orderId": "order2",
            "user": {
                "name": "Bob",
                "contact": "456 Market St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book B", "quantity": 2}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)

    @task
    def order_c(self):
        order_data = {
            "orderId": "order3",
            "user": {
                "name": "Charlie",
                "contact": "789 Elm St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book C", "quantity": 3}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)


class MixedOrderUser(HttpUser):
    """Simulate mixed orders: some fraudulent, some valid."""
    wait_time = between(1, 3)

    @task
    def order_d(self):
        # user James: valid payment but maybe flagged by fraud rules
        order_data = {
            "orderId": "order4",
            "user": {
                "name": "James",
                "contact": "101 Maple St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book D", "quantity": 1}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)

    @task
    def order_e(self):
        # user Eve: invalid CVV triggers fraud
        order_data = {
            "orderId": "order5",
            "user": {
                "name": "Eve",
                "contact": "202 Oak St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "123"  # wrong CVV
            },
            "items": [
                {"name": "Book E", "quantity": 1}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)

    @task
    def order_f(self):
        # re-use order1 (should be idempotent or rejected as duplicate)
        order_data = {
            "orderId": "order1",
            "user": {
                "name": "Alice",
                "contact": "123 Main St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book F", "quantity": 1}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)


class ConflictingOrderUser(HttpUser):
    """Simulate two users racing for the same book concurrently."""
    wait_time = between(1, 3)

    @task
    def order_g1(self):
        order_data = {
            "orderId": "order6",
            "user": {
                "name": "Frank",
                "contact": "303 Pine St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book G", "quantity": 1}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)

    @task
    def order_g2(self):
        order_data = {
            "orderId": "order7",
            "user": {
                "name": "Grace",
                "contact": "404 Cedar St"
            },
            "creditCard": {
                "number": "4111111111111111",
                "expirationDate": "12/25",
                "cvv": "456"
            },
            "items": [
                {"name": "Book G", "quantity": 1}
            ],
            "billingAddress": {
                "street": "Raatuse 22",
                "city": "Tartu",
                "state": "Tartumaa",
                "zip": "12345",
                "country": "Estonia"
            },
        }
        self.client.post("/checkout", json=order_data)
