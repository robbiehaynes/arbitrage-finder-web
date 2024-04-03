"""Application Models"""
import bson, os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('.env.local')

client = MongoClient(os.getenv('MONGO_DB_URI'), tls=True, tlsCAFile=certifi.where())
db = client.arbitrages

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