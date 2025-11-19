import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import User, MenuItem, Order, Reservation, Review, Announcement, Special

app = FastAPI(title="Cafe Yakjaaah API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Cafe Yakjaaah API is running"}

# Simple auth models
class AuthRequest(BaseModel):
    name: Optional[str] = None
    email: str
    password: str

class AuthResponse(BaseModel):
    name: str
    email: str
    token: str
    loyalty_points: int

# Utility

def collection(name: str):
    return db[name]

# Auth endpoints (simple token management for demo)
@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(req: AuthRequest):
    user_col = collection("user")
    if user_col.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    token = os.urandom(12).hex()
    user = User(name=req.name or req.email.split("@")[0], email=req.email, password=req.password, token=token)
    create_document("user", user)
    return AuthResponse(name=user.name, email=user.email, token=token, loyalty_points=0)

@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: AuthRequest):
    user = collection("user").find_one({"email": req.email, "password": req.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = os.urandom(12).hex()
    collection("user").update_one({"_id": user["_id"]}, {"$set": {"token": token}})
    return AuthResponse(name=user["name"], email=user["email"], token=token, loyalty_points=user.get("loyalty_points", 0))

# Menu endpoints
@app.get("/api/menu")
def get_menu(category: Optional[str] = None):
    query = {"category": category} if category else {}
    items = get_documents("menuitem", query)
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items

@app.post("/api/menu")
def add_menu_item(item: MenuItem):
    item_id = create_document("menuitem", item)
    return {"id": item_id}

# Specials & announcements
@app.get("/api/specials")
def list_specials():
    specials = get_documents("special", {})
    for s in specials:
        s["id"] = str(s.pop("_id"))
    return specials

@app.post("/api/specials")
def add_special(s: Special):
    sid = create_document("special", s)
    return {"id": sid}

@app.get("/api/announcements")
def list_announcements():
    anns = get_documents("announcement", {})
    for a in anns:
        a["id"] = str(a.pop("_id"))
    return anns

@app.post("/api/announcements")
def add_announcement(a: Announcement):
    aid = create_document("announcement", a)
    return {"id": aid}

# Favorites
class FavoriteRequest(BaseModel):
    email: str
    item_id: str

@app.post("/api/favorites/toggle")
def toggle_favorite(req: FavoriteRequest):
    user = collection("user").find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    favs = user.get("favorites", [])
    if req.item_id in favs:
        favs.remove(req.item_id)
    else:
        favs.append(req.item_id)
    collection("user").update_one({"_id": user["_id"]}, {"$set": {"favorites": favs}})
    return {"favorites": favs}

@app.get("/api/favorites")
def get_favorites(email: str):
    user = collection("user").find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"favorites": user.get("favorites", [])}

# Orders
@app.post("/api/orders")
def create_order(order: Order):
    oid = create_document("order", order)
    # loyalty: +1 point per $10 spent
    user = collection("user").find_one({"email": order.user_email})
    if user:
        add_points = int(order.total // 10)
        collection("user").update_one({"_id": user["_id"]}, {"$inc": {"loyalty_points": add_points}})
    return {"order_id": oid, "status": "received"}

@app.get("/api/orders/status")
def order_status(order_id: str):
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")
    order = collection("order").find_one({"_id": obj_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"status": order.get("status", "received")}

# Reservations
@app.post("/api/reservations")
def create_reservation(res: Reservation):
    rid = create_document("reservation", res)
    return {"reservation_id": rid}

# Reviews
@app.get("/api/reviews")
def list_reviews(menu_item_id: Optional[str] = None):
    q = {"menu_item_id": menu_item_id} if menu_item_id else {}
    reviews = get_documents("review", q)
    for r in reviews:
        r["id"] = str(r.pop("_id"))
    return reviews

@app.post("/api/reviews")
def add_review(review: Review):
    rid = create_document("review", review)
    return {"id": rid}

# Contact info (static for now)
@app.get("/api/contact")
def contact_info():
    return {
        "phone": "+1 (555) 012-3456",
        "email": "hello@cafeyakjaaah.com",
        "address": "123 Cozy Lane, Brewtown",
        "maps_url": "https://maps.google.com/?q=123+Cozy+Lane+Brewtown"
    }

# Test endpoint remains
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
