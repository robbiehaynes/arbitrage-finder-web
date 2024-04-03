import os
import certifi
import bson
import json
from dotenv import load_dotenv, find_dotenv

from flask import Flask, jsonify, request

from authlib.integrations.flask_oauth2 import ResourceProtector
from urllib.request import urlopen

from authlib.oauth2.rfc7523 import JWTBearerTokenValidator
from authlib.jose.rfc7517.jwk import JsonWebKey

from pymongo import MongoClient

load_dotenv(find_dotenv('.env.local'))

class Auth0JWTBearerTokenValidator(JWTBearerTokenValidator):
  def __init__(self, domain, audience):
      issuer = f"https://{domain}/"
      jsonurl = urlopen(f"{issuer}.well-known/jwks.json", cafile=certifi.where())
      public_key = JsonWebKey.import_key_set(
          json.loads(jsonurl.read())
      )
      super(Auth0JWTBearerTokenValidator, self).__init__(
          public_key
      )
      self.claims_options = {
          "exp": {"essential": True},
          "aud": {"essential": True, "value": audience},
          "iss": {"essential": True, "value": issuer},
      }
  
class Arbitrage:
  """Arbitrage Model"""
  def __init__(self):
    return

  def create(self, bet):
    """Create a new bet"""
    book = self.get_by_teams_and_time(bet["home_team"], bet["away_team"], bet["time"])
    if book:
      return
    new_book = db.h2h.insert_one(bet)
    return self.get_by_id(new_book.inserted_id)

  def get_all(self):
    """Get all arbs"""
    arbs = db.h2h.find()
    return [{**arb, "_id": str(arb["_id"])} for arb in arbs]
  
  def get_by_sport(self, sport):
    """Get all arbs by sport"""
    arbs = db.h2h.find({"sport": sport})
    return [{**arb, "_id": str(arb["_id"])} for arb in arbs]

  def get_by_id(self, id):
      """Get a arbitrage by id"""
      arb = db.h2h.find_one({"_id": bson.ObjectId(id)})
      if not arb:
          return
      arb["_id"] = str(arb["_id"])
      return arb

  def get_by_teams_and_time(self, home_team, away_team, time):
      """Get a arbitrage given its title and author"""
      arb = db.h2h.find_one({"home_team": home_team, "away_team": away_team, "time": time})
      if not arb:
          return
      arb["_id"] = str(arb["_id"])
      return arb

  def update(self, arb_id, away_team="", away_stake={}, home_team="", home_stake={}, roi=""):
      """Update a arbitrage"""
      data={}
      if away_team: data["away_team"]=away_team
      if away_stake: data["away_stake"]=away_stake
      if home_team: data["home_team"]=home_team
      if home_stake: data["home_stake"]=home_stake
      if roi: data["roi"]=roi

      book = db.h2h.update_one(
          {"_id": bson.ObjectId(arb_id)},
          {
              "$set": data
          }
      )
      book = self.get_by_id(arb_id)
      return book

  def delete(self, arb_id):
      """Delete a book"""
      arb = db.h2h.delete_one({"_id": bson.ObjectId(arb_id)})
      return arb


require_auth = ResourceProtector()
validator = Auth0JWTBearerTokenValidator(
    os.getenv("AUTH0_DOMAIN"),
    os.getenv("AUTH0_AUDIENCE")
)
require_auth.register_token_validator(validator)

app = Flask(__name__)

# MongoDB connection information
client = MongoClient(os.getenv('MONGO_DB_URI'), tls=True, tlsCAFile=certifi.where())
db = client.arbitrages
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
