#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# GET /restaurants
class RestaurantsResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        response = [
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address,
            }
            for restaurant in restaurants
        ]
        return make_response(jsonify(response), 200)


# GET /restaurants/<int:id>
class RestaurantResource(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if restaurant:
            response = {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address,
                "restaurant_pizzas": [
                    {
                        "id": rp.id,
                        "price": rp.price,
                        "pizza_id": rp.pizza_id,
                        "restaurant_id": rp.restaurant_id,
                        "pizza": {
                            "id": rp.pizza.id,
                            "name": rp.pizza.name,
                            "ingredients": rp.pizza.ingredients,
                        },
                    }
                    for rp in restaurant.restaurant_pizzas
                ],
            }
            return make_response(jsonify(response), 200)
        return make_response(jsonify({"error": "Restaurant not found"}), 404)

    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)
        if restaurant:
            RestaurantPizza.query.filter_by(restaurant_id=id).delete()
            db.session.delete(restaurant)
            db.session.commit()
            return make_response("", 204)
        return make_response(jsonify({"error": "Restaurant not found"}), 404)


# GET /pizzas
class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        response = [
            {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients,
            }
            for pizza in pizzas
        ]
        return make_response(jsonify(response), 200)


# POST /restaurant_pizzas
class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()
        price = data.get("price")
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")

        # Validation check for price within 1 to 30
        if not (1 <= price <= 30):
            return make_response(
                jsonify({"errors": ["validation errors"]}), 400
            )

        if not (price and pizza_id and restaurant_id):
            return make_response(
                jsonify({"errors": ["Missing required fields"]}), 400
            )

        pizza = db.session.get(Pizza, pizza_id)
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not (pizza and restaurant):
            return make_response(
                jsonify({"errors": ["Invalid pizza_id or restaurant_id"]}), 400
            )

        try:
            restaurant_pizza = RestaurantPizza(
                price=price, pizza_id=pizza_id, restaurant_id=restaurant_id
            )
            db.session.add(restaurant_pizza)
            db.session.commit()
            response = {
                "id": restaurant_pizza.id,
                "price": restaurant_pizza.price,
                "pizza_id": restaurant_pizza.pizza_id,
                "restaurant_id": restaurant_pizza.restaurant_id,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients,
                },
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address,
                },
            }
            return make_response(jsonify(response), 201)
        except Exception as e:
            return make_response(jsonify({"errors": [str(e)]}), 400)


# Add routes
api.add_resource(RestaurantsResource, "/restaurants", endpoint="restaurant_list")
api.add_resource(
    RestaurantResource, "/restaurants/<int:id>", endpoint="restaurant_by_id"
)
api.add_resource(PizzasResource, "/pizzas")
api.add_resource(RestaurantPizzasResource, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
