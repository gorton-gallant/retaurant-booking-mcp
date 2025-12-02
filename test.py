from fastmcp import FastMCP, Context
from fastmcp.server.middleware import (Middleware)
#from mcp_ui_server.core import UIResource
from pydantic import BaseModel, Field
from typing import List
import requests
import uvicorn
import logging

ASSETS_DIR = "http://localhost:3000"
OAUTH_URL = "https://tgallant-mcp-server.ngrok.app"
RESTAURANTS = [
    {
        "restaurant_id": "12345678",
        "name": "Pizzeria Bianca",
        "description": "Neapolitan-style pies from a wood-fired oven.",
        "cuisine": "Italian",
        "$$": "$$",
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1541745537413-b804b0c5fbbf",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "12121212",
        "name": "Desert Ramen Bar",
        "description": "Slow-simmered broths and hand-pulled noodles.",
        "cuisine": "Japanese",
        "$$": "$$",
        "rating": 4.7,
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzygiV20nmaFWTJ9co6URssOHtnldac2-aXpOnOkQVxObc-s0tOssLschUFeil9ipvSEXvUVu6tHXl8lKTMeOr1DQnR3i5Vf0ANu652nPq4P9KvZ--Fo56p618M7EpmONTodBCD=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2205': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "12341234",
        "name": "Full Moon Izakaya",
        "description": "Slow-simmered broths and hand-pulled noodles.",
        "cuisine": "Japanese",
        "$$": "$",
        "rating": 4.5,
        "image": "https://lh3.googleusercontent.com/p/AF1QipMlbfuVjNDV8xIK0BJ1Jx7K3gveKDjyoy5eF_eT=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "56785678",
        "name": "Sonoran Grill",
        "description": "Mesquite-grilled carne asada and street tacos.",
        "cuisine": "Mexican",
        "$$": "$$",
        "rating": 4.5,
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzG8T8b29Xme1ifE7ZxMcwz3A78gOhYf6AulUtDI2QMU9uiaAbVDsnRNxWsoAIPgd8f26knWN_Z3HFAhfARlDw1aG_i4-ClFW8S9--z-3jkxHZODqB3VEhkWts891esxM9xn6kA=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "22222222",
        "name": "Cactus & Curry",
        "description": "Modern Indian flavors with Southwest touches.",
        "cuisine": "Indian",
        "$$": "$$",
        "rating": 4.4,
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSy7qK-BBNrFDkXlbNNFxKQ0r14dh0SlwNZIoQ9kpzn4TiRsLjnJnj2-cjFqGLBYagR8cDW931vzuBxOmVbAcekxkf2XCdWOt9eLFGNwObW6COgiKSibD1xOv5zllKH-HIojHKlwhOaA5fbH=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }

    },
    {
        "restaurant_id": "33333333",
        "name": "Bayview Oyster House",
        "description": "Raw bar, chowders, and coastal classics.",
        "cuisine": "Seafood",
        "$$": "$$$",
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1553621042-f6e147245754",
        "street": "1234 W. Fifth Street",
        "city": "San Francisco",
        "state": "CA",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2205': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "44444444",
        "name": "Yutaka",
        "description": "Intimate Japanese restaurant with minimalist décor & sushi, sashimi & teriyaki on the long menu.",
        "cuisine": "Japanese",
        "$$": "$",
        "rating": 4.6,
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzEjknPVWPwpRJ9-0PXQiejefDUqe7YeA7JuHQAC4WMzrWsT7wl3KQ5SLbKOJ1m-uxJMe6Jpx3L3zgAKcBsLy1m3_Wsy9mCK5l-CjuoG9ku1D0wzcgWQiqHy-Si_AgPuHyvT045vw=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "12345678",
        "name": "Uchi",
        "description": "Fresh Sushi. Bold Flavors. Creative Menus",
        "cuisine": "Japanese",
        "$$": "$$",
        "rating": 4.5,
        "image": "https://lh3.googleusercontent.com/p/AF1QipP-M5aFNy9yCsyTGwiRwBu2M9iBwff0ByF2uYDe=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "Phoenix",
        "state": "AZ",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "66666666",
        "name": "Trattoria del Mare",
        "description": "Homemade pasta and coastal Italian plates.",
        "cuisine": "Italian",
        "$$": "$$$",
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1521389508051-d7ffb5dc8bbf",
        "street": "1234 W. Fifth Street",
        "city": "San Francisco",
        "state": "CA",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }

    },
    {
        "restaurant_id": "77777777",
        "name": "Brooklyn Slice Co.",
        "description": "Thin-crust pies with classic NYC toppings.",
        "cuisine": "Italian",
        "$$": "$",
        "rating": 4.3,
        "image": "https://images.unsplash.com/photo-1548365328-9f547fb0953c",
        "street": "1234 W. Fifth Street",
        "city": "New York",
        "state": "NY",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2205': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "88888888",
        "name": "Hanami Izakaya",
        "description": "Yakitori, sashimi, and sake flights.",
        "cuisine": "Japanese",
        "$$": "$$$",
        "rating": 4.8,
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzygiV20nmaFWTJ9co6URssOHtnldac2-aXpOnOkQVxObc-s0tOssLschUFeil9ipvSEXvUVu6tHXl8lKTMeOr1DQnR3i5Vf0ANu652nPq4P9KvZ--Fo56p618M7EpmONTodBCD=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "New York",
        "state": "NY",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "99999999",
        "name": "Hanami Izakaya",
        "description": "Yakitor, sashim",
        "cuisine": "Japanese",
        "$$": "$",
        "rating": 4.1,
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzygiV20nmaFWTJ9co6URssOHtnldac2-aXpOnOkQVxObc-s0tOssLschUFeil9ipvSEXvUVu6tHXl8lKTMeOr1DQnR3i5Vf0ANu652nPq4P9KvZ--Fo56p618M7EpmONTodBCD=s1360-w1360-h1020-rw",
        "street": "1234 W. Fifth Street",
        "city": "New York",
        "state": "NY",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "87654321",
        "name": "Bombay Junction",
        "description": "Regional Indian thalis and tandoori specialties.",
        "cuisine": "Indian",
        "$$": "$$",
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d0",
        "street": "1234 W. Fifth Street",
        "city": "New York",
        "state": "NY",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "56565656",
        "name": "Taco Alley",
        "description": "Birria tacos and consomé, made daily.",
        "cuisine": "Mexican",
        "$$": "$",
        "rating": 4.4,
        "image": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b",
        "street": "1234 W. Fifth Street",
        "city": "Austin",
        "state": "TX",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2205': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "67676767",
        "name": "Hill Country Smokehouse",
        "description": "Offset-smoked brisket and ribs by the pound.",
        "cuisine": "Barbecue",
        "$$": "$$",
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1552332386-9c6a7a44d6cf",
        "street": "1234 W. Fifth Street",
        "city": "Austin",
        "state": "TX",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "78787878",
        "name": "Uptown Bistro",
        "description": "Seasonal New American with local produce.",
        "cuisine": "American",
        "$$": "$$$",
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0",
        "street": "1234 W. Fifth Street",
        "city": "Chicago",
        "state": "IL",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }
    },
    {
        "restaurant_id": "89898989",
        "name": "Kimchi Corner",
        "description": "Korean BBQ and bubbling stews.",
        "cuisine": "Korean",
        "$$": "$$",
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1544025162-d76694265947",
        "street": "1234 W. Fifth Street",
        "city": "Chicago",
        "state": "IL",
        "availability": {
            '11-15-2025': ["19:00:00","19:30:00", "20:00:00", "21:30:00"],
            '11-16-2025': ["19:30:00","20:30:00", "21:00:00", "21:30:00"],
            '11-17-2025': ["18:00:00","18:30:00", "19:30:00", "21:00:00"],
            '11-18-2025': ["19:00:00","19:30:00", "20:30:00", "21:00:00"],
            '11-19-2025': ["17:30:00","18:30:00", "19:30:00", "20:30:00"],
        }

    },
]

logging.basicConfig(level=logging.INFO, format='[SERVER] %(message)s')

app = FastMCP(
    name="Restaurant Assistant",
)

# ──────────────────────────────────────────────────────────────
# 1. Data models
# ──────────────────────────────────────────────────────────────
class Restaurant(BaseModel):
    id: str = Field(..., description="Unique restaurant ID")
    name: str
    cuisine: str
    rating: float
    price_range: str  # "$", "$$", "$$$", "$$$"
    address: str
    image_url: str | None = None
    highlights: List[str] = Field(default_factory=list)

class RecommendationResponse(BaseModel):
    type: str = "restaurant_recommendations"  # Important!
    restaurants: List[Restaurant]

# ──────────────────────────────────────────────────────────────
# 2. Recommendation tool → returns structured JSON cards
# ─────────────────────────────────────────────────────────────────
@app.tool(
    name='Restaurant-recomm',
    description='Provides a list of available restaurants based on city, state and cuisine. The client will display these options as selectable cards.'
)
def get_recommendations(
        city: str = "Phoenix",
        state: str = "AZ",
        cuisine: str  = "Japanese",
) -> RecommendationResponse:
    """Get personalized restaurant recommendations."""
    results = []
    for rest in RESTAURANTS:
        if rest["city"] == city and rest["state"] == state and rest["cuisine"] == cuisine:
            results.append(rest)

    return RecommendationResponse(restaurants=results)

# ──────────────────────────────────────────────────────────────
# 3. SINGLE UI Widget for booking (this is what the user sees)
# ──────────────────────────────────────────────────────────────

#
#
# def dam_fetch_text(path: str) -> str:
#     url = f"{ASSETS_DIR}{path}"
#     r = requests.get(url, timeout=10)
#     r.raise_for_status()
#     return r.text

# class BookTableWidget():
#     restaurant_id: str = Field(..., description="Restaurant ID")
#
#     # This HTML runs inside ChatGPT's secure widget iframe
#     def render(self) -> str:
#         css = dam_fetch_text(f"/Restaurant-booking.css")
#         js  = dam_fetch_text(f"/Restaurant-booking.js")
#
#         html = f"""<!doctype html>
#         <html lang="en">
#         <head>
#           <meta charset="UTF-8" />
#           <meta name="viewport" content="width=device-width, initial-scale=1" />
#           <title>Restaurant-recomm</title>
#           <style>{css}</style>
#         </head>
#         <body>
#           <div id="root"></div>
#           <script type="module">{js}</script>
#         </body>
#         </html>"""
#         return html

# @app.tool(
#     name="Restaurant-booking",
#     description="Opens the reservation widget for a specific restaurant"
# )
# def book_restaurant() -> list[UIResource]:
#     # This creates a resource object that the client (LLM UI) will render
#     widget_instance = BookTableWidget()
#     html_content = widget_instance.render()
#
#     ui_resource = create_ui_resource({
#         "uri": "ui://widget/Restaurant-booking.html",
#         "content": {
#             "type": "rawHtml",
#             "htmlString": html_content
#         },
#         "encoding": "text"
#     })
#     return [ui_resource]

# ──────────────────────────────────────────────────────────────
# 4. The actual booking tool (still needed so LLM can confirm)
# ──────────────────────────────────────────────────────────────
# @app.tool()
# def book_reservation(
#         restaurant_id: str,
#         date: str,
#         time: str,
#         party_size: int
# ) -> str:
#     """Actually create the reservation (called by the widget or directly)."""
#     # Call your existing reservation API here
#     print(f"Booking {restaurant_id} for {party_size} on {date} at {time}")
#     return f"✅ Reservation confirmed at restaurant {restaurant_id}!"

# ──────────────────────────────────────────────────────────────
# 5. Auto-generate the card → widget actions (this is the magic)
# ──────────────────────────────────────────────────────────────
# @app.on_tool_result("get_recommendations")
# def enrich_recommendations(result: RecommendationResponse):
#     # This runs right after get_recommendations returns
#     cards = []
#     for r in result.restaurants:
#         cards.append({
#             "title": r.name,
#             "subtitle": f"{r.cuisine} • {r.city} • {r.state}★",
#             "image_url": r.image_url,
#             "actions": [
#                 {
#                     "type": "widget",
#                     "widget": "book_restaurant_table",
#                     "label": "Book Table",
#                     "parameters": {
#                         "restaurant_id": r.id,
#                     }
#                 }
#             ]
#         })
#     return {"cards": cards}

# ──────────────────────────────────────────────────────────────
# Middleware (optional but nice)
# ──────────────────────────────────────────────────────────────
class InitialRequestLogger(Middleware):
    async def process_request(self, context: Context, call_next):
        logging.info(f'Received request: {context.request.dict()}')
        return await call_next(context)

app.add_middleware(InitialRequestLogger())

# ──────────────────────────────────────────────────────────────
# Correct way to get the ASGI app in fastmcp ≥2.0
# ──────────────────────────────────────────────────────────────
application = app.http_app()   # This is the modern, recommended transport

# ──────────────────────────────────────────────────────────────
# Run with uvicorn (or let FastMCP run it)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(application, host="0.0.0.0", port=8000, reload=True)
