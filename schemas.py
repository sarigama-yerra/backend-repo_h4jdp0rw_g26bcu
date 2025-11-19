"""
Database Schemas for Cafe Yakjaaah

Each Pydantic model corresponds to a MongoDB collection whose name is the lowercased class name.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Hashed password or credential secret")
    phone: Optional[str] = Field(None, description="Phone number")
    favorites: List[str] = Field(default_factory=list, description="Menu item IDs user has favorited")
    loyalty_points: int = Field(0, ge=0, description="Accumulated loyalty points")
    token: Optional[str] = Field(None, description="Session token for simple auth")

class MenuItem(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: Literal["breakfast", "mains", "snacks", "beverages", "desserts"]
    image_url: Optional[str] = None
    spicy: Optional[Literal["mild", "medium", "hot"]] = None
    add_ons: List[str] = Field(default_factory=list, description="List of available add-ons")
    toppings: List[str] = Field(default_factory=list, description="List of available toppings")

class CartItem(BaseModel):
    menu_item_id: str
    name: str
    price: float
    quantity: int = Field(1, ge=1)
    add_ons: List[str] = Field(default_factory=list)
    toppings: List[str] = Field(default_factory=list)
    spice_level: Optional[Literal["mild", "medium", "hot"]] = None
    notes: Optional[str] = None

class Order(BaseModel):
    user_email: str
    items: List[CartItem]
    subtotal: float = Field(..., ge=0)
    tax: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    fulfillment: Literal["pickup", "delivery"]
    status: Literal["received", "preparing", "ready", "out_for_delivery", "completed", "cancelled"] = "received"
    address: Optional[str] = None

class Reservation(BaseModel):
    user_email: str
    name: str
    phone: str
    party_size: int = Field(..., ge=1, le=20)
    date: str
    time: str
    notes: Optional[str] = None

class Review(BaseModel):
    user_email: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    menu_item_id: Optional[str] = Field(None, description="If provided, review is for a specific menu item")

class Announcement(BaseModel):
    title: str
    message: str
    image_url: Optional[str] = None
    tag: Optional[str] = Field(None, description="e.g., event, deal, seasonal")

class Special(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    image_url: Optional[str] = None
