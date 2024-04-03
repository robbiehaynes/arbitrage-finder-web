import os
from dotenv import load_dotenv, find_dotenv

from flask import Flask, jsonify, request

from authlib.integrations.flask_oauth2 import ResourceProtector
from validator import Auth0JWTBearerTokenValidator

from models import Arbitrage

load_dotenv(find_dotenv('.env.local'))

require_auth = ResourceProtector()
validator = Auth0JWTBearerTokenValidator(
    os.getenv("AUTH0_DOMAIN"),
    os.getenv("AUTH0_AUDIENCE")
)
require_auth.register_token_validator(validator)

app = Flask(__name__)

# MongoDB connection information
DB_NAME = "arbitrages"
COLLECTION_NAME = "h2h"

@app.route('/api/home', methods=['GET'])
def home():
  return "Welcome to the Arbitrage API!"

@app.route('/api/arbitrages', methods=['GET'])
@require_auth(None)
def get_all_arbitrages():
  try:
    arbitrages = Arbitrage().get_all()
    
    return jsonify({
      "message": "successfully retrieved all arbitrages",
      "data": arbitrages
    }), 200
  except Exception as e:
    return jsonify({
      "message": "failed to retrieve all books",
      "error": str(e),
      "data": None
    }), 500
  
@app.route('/api/arbitrages/<id>', methods=['GET'])
@require_auth(None)
def get_arbitrage(id):
  try:
    arbitrage = Arbitrage().get_by_id(id)

    if arbitrage:
      return jsonify({
        "message": "successfully retrieved arbitrage",
        "data": arbitrage
      }), 200
    else:
      return jsonify({
        "message": "arbitrage not found",
        "data": None
      }), 404
  except Exception as e:
    return jsonify({
      "message": "failed to retrieve arbitrage",
      "error": str(e),
      "data": None
    }), 500
  
@app.route('/api/arbitrages/<sport>', methods=['GET'])
@require_auth(None)
def get_arbitrage_by_sport(sport):
  try:
    arbitrages = Arbitrage().get_by_sport(sport)

    if arbitrages:
      return jsonify({
        "message": "successfully retrieved arbitrages",
        "data": arbitrages
      }), 200
    else:
      return jsonify({
        "message": "no arbitrages found",
        "data": None
      }), 204
  except Exception as e:
    return jsonify({
      "message": "failed to retrieve arbitrages",
      "error": str(e),
      "data": None
    }), 500

@app.route('/api/arbitrages', methods=['POST'])
@require_auth(None)
def add_arbitrage():
  try:
    arbitrage_data = request.get_json()
    if not arbitrage_data:
      return jsonify({
        "message": "Invalid data, you need to give the book title, cover image, author id,",
        "data": None,
        "error": "Bad Request"
      }), 400
    
    arbitrage = Arbitrage().create(arbitrage_data)
    if not arbitrage:
      return jsonify({
        "message": "Arbitrage already exists",
        "data": None,
        "error": "Conflict"
      }), 409
    else:
      return jsonify({
        "message": "Arbitrage created successfully",
        "data": arbitrage
      }), 201
  except Exception as e:
    return jsonify({
      "message": "failed to create arbitrage",
      "error": str(e),
      "data": None
    }), 500
  
@app.route('/api/arbitrages/<id>', methods=['DELETE'])
@require_auth(None)
def delete_arbitrage(id):
  try:
    arbitrage = Arbitrage.get_by_id(id)

    if not arbitrage:
      return jsonify({
        "message": "arbitrage not found",
        "data": None,
        "error": "Not found"
      }), 404
    Arbitrage().delete(id)
    return jsonify({
      "message": "arbitrage deleted successfully",
      "data": None
    }), 200
  except Exception as e:
    return jsonify({
      "message": "failed to delete arbitrage",
      "error": str(e),
      "data": None
    }), 500
  
@app.route('/api/arbitrages/<id>', methods=['PUT'])
@require_auth(None)
def update_arbitrage(id):
  try:
    arbitrage_data = request.get_json()
    if not arbitrage_data:
      return jsonify({
        "message": "Invalid data, you need to give the book title, cover image, author id,",
        "data": None,
        "error": "Bad Request"
      }), 400
    
    arbitrage = Arbitrage().update(
      id,
      arbitrage_data["away_team"],
      arbitrage_data["away_stake"],
      arbitrage_data["home_team"],
      arbitrage_data["home_stake"],
      arbitrage_data["roi"]
    )
    if not arbitrage:
      return jsonify({
        "message": "arbitrage not found",
        "data": None,
        "error": "Not found"
      }), 404
    else:
      return jsonify({
        "message": "arbitrage updated successfully",
        "data": arbitrage
      }), 200
  except Exception as e:
    return jsonify({
      "message": "failed to update arbitrage",
      "error": str(e),
      "data": None
    }), 500

if __name__ == '__main__':

  app.run(debug=True)
