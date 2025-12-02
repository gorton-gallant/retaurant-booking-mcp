"""Restaurant restaurant demo MCP server implemented with the Python FastMCP helper.

The server mirrors the Node example in this repository and exposes
widget-backed tools that render the Restaurant UI bundle. Each handler returns the
HTML shell via an MCP resource and echoes the selected cuisine, city and state as structured
content so the ChatGPT client can hydrate the widget. The module also wires the
handlers into an HTTP/SSE stack so you can run the server with uvicorn on port
8000, matching the Node transport behavior."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List
import json
import requests
from requests.exceptions import RequestException, HTTPError

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Type
from server import rest_api

class RestaurantRecommend(BaseModel):
    """Schema for Restaurant recommendations tools."""
    cuisine: str = Field(
        ...,
        alias="cuisine",
        description="Restaurant type to mention when rendering the widget.",
    ),
    city: str = Field(
        ...,
        alias="city",
        description="The city where located to mention when rendering the widget.",
    ),
    state: str = Field(
        ...,
        alias="state",
        description="the state associated with city to mention when rendering the widget.",
    ),
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

class RestaurantBooking(BaseModel):
    """Schema for Restaurant Booking tool."""
    restaurant_id: str = Field(
        ...,
        alias="restaurant_id",
        description="Restaurant identifier number"
    ),
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

@dataclass(frozen=True)
class RestaurantWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str

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
        "restaurant_id": "98769876",
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

def find_restaurant_by_id(target_id: str) -> dict | None:
    for restaurant in RESTAURANTS:
        if restaurant.get("restaurant_id") == target_id:
            return restaurant
    return None

def dam_fetch_text(path: str) -> str:
    url = f"{ASSETS_DIR}{path}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text

def get_title(name: str) -> str:
    match name:
        case "Restaurant_recomm":
            return "Restaurant Recommendations"
        case "Restaurant_booking":
            return "Restaurant Reservations"
        case _:
            return "Unknown"

@lru_cache(maxsize=None)
def _load_widget_html(component_name: str) -> str:
    print(f'Component name is {component_name}')
    css = dam_fetch_text(f"/{component_name}.css")
    js  = dam_fetch_text(f"/{component_name}.js")
    title = get_title(component_name)

    html = f"""<!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>{title}</title>
      <style>{css}</style>
    </head>
    <body>
      <div id="root"></div>
      <script type="module">{js}</script>
    </body>
    </html>"""
    return html


widgets: List[RestaurantWidget] = [
    RestaurantWidget(
        identifier="Restaurant-recomm",
        title="Provides a list of available restaurants based on city, state and cuisine. The client will display these options as selectable cards.",
#        template_uri="ui://widget/Restaurant-recomm.html",
        template_uri="",
        invoking="Retrieving a list",
        invoked="Received a fresh map",
#        html=_load_widget_html("Restaurant-recomm"),
        html="",
        response_text="Rendered a restaurant list!",
    ),
    RestaurantWidget(
        identifier="Restaurant-booking",
        title="Book A Restaurant Reservation",
        template_uri="ui://widget/Restaurant-booking.html",
        invoking="Getting reservation details",
        invoked="Received reservation details",
        html=_load_widget_html("Restaurant-booking"),
        response_text="Rendered reservation options!",
    ),
]


MIME_TYPE = "text/html+skybridge"

WIDGETS_BY_ID: Dict[str, RestaurantWidget] = {
    widget.identifier: widget for widget in widgets
}
WIDGETS_BY_URI: Dict[str, RestaurantWidget] = {
    widget.template_uri: widget for widget in widgets
}

mcp = FastMCP(
    name="Restaurant-recomm-mcp",
    stateless_http=True,
)

SCHEMA_MAP: dict[str, Type[BaseModel]] = {
    "Restaurant-recomm": RestaurantRecommend,
    "Restaurant-booking": RestaurantBooking,
}

def _resource_description(widget: RestaurantWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: RestaurantWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }


def _embedded_widget_resource(widget: RestaurantWidget) -> types.EmbeddedResource:
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            title=widget.title,
        ),
    )

@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=widget.title,
            inputSchema=SCHEMA_MAP.get(widget.identifier).model_json_schema(),
            securitySchemes=[
                {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorization_endpoint": f"{OAUTH_URL}/oauth2/authorize",
                            "token_endpoint":  f"{OAUTH_URL}/oauth2/token",
                            "registration_endpoint":  f"{OAUTH_URL}/oauth2/register",
                            "authorizationUrl": f"{OAUTH_URL}/oauth2/authorize",
                            "tokenUrl":  f"{OAUTH_URL}/oauth2/token",
                            "scopes": {
                                "token": "token"
                            }
                        }
                    },
                },
            ],
            _meta=_tool_meta(widget),
            # To disable the approval prompt for the tools
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))

    if widget is None:
        print(f'Widget not found')
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    widget = WIDGETS_BY_ID.get(req.params.name)
    if widget is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Unknown tool: {req.params.name}")],
                isError=True,
            )
        )

    arguments = req.params.arguments or {}

    match req.params.name:
        # =============== RECOMMENDATIONS — ONLY DATA, NO WIDGET ===============
        case "Restaurant-recomm":
            cuisine = arguments.get("cuisine", "Japanese")
            city = arguments.get("city", "New York")
            state = arguments.get("state", "NY")

            results = [
                rest for rest in RESTAURANTS
                if rest["city"] == city and rest["state"] == state and rest["cuisine"].lower() == cuisine.lower()
            ]

            structured_content = {
                "restaurants": [
                    {
                        "restaurant_id": r["restaurant_id"],
                        "name": r["name"],
                        "description": r["description"],
                        "street": r["street"],
                        "city": r["city"],
                        "state": r["state"],
                        "cuisine": r["cuisine"],
                        "price_range": r["$$"],
                        "rating": r["rating"],
                        "image": r["image"],
                        "book_action": {
                            "type": "tool_call",
                            "tool_name": "Restaurant-booking",
                            "parameters": {
                                "restaurant_id": r["restaurant_id"]
                            }
                        }
                    }
                    for r in results
                ]
            }

            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="Here are the top matching restaurants. Tap “Book” on any card to make a reservation. Always display restaurant images."
                        )
                    ],
                    structuredContent=structured_content,
                )
            )

        # ========================= BOOKING — WITH WIDGET =========================
        case "Restaurant-booking":
            target_id = arguments.get("restaurant_id")
            restaurant = find_restaurant_by_id(target_id)
            if not restaurant:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[types.TextContent(type="text", text="Restaurant not found.")],
                        isError=True,
                    )
                )

            # Embed the actual widget HTML
            widget_resource = _embedded_widget_resource(widget)

            meta = {
                "openai.com/widget": widget_resource,
                "openai/outputTemplate": widget.template_uri,
                "openai/toolInvocation/invoking": widget.invoking,
                "openai/toolInvocation/invoked": widget.invoked,
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
            }

            return types.ServerResult(
                types.CallToolResult(
                    _meta=meta,
                    content=[
                        types.TextContent(
                            type="text",
                            text="Do not add any commentary, prefatory text, or explanations. Once tool output is displayed, do not add any more text on the chat",
                        )
                    ],
                    structuredContent={"restaurant": restaurant},  # optional extra data
                )
            )

        case _:
            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text="Unknown tool")],
                    isError=True,
                )
            )

mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource

mcp_app = mcp.streamable_http_app()
mcp_app.mount("/", rest_api, name="rest_api_server")

if __name__ == "__main__":
    import uvicorn
    # To run this server, execute: python server.py
    # or uvicorn server:app --reload
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)
