"""
End-to-end tests for the Store Locator API.
All 15 tests must pass to capture the flag.

The FastAPI application must be importable as `app.main` or `main`.
The app object should be named `app`.
"""

import pytest
import httpx
import math
import sys
import os

# Add the challenge directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the FastAPI app
try:
    from app.main import app
except ImportError:
    try:
        from main import app
    except ImportError:
        raise ImportError(
            "Could not import the FastAPI app. "
            "Make sure it's at app/main.py (with `app` variable) or main.py."
        )

from httpx import AsyncClient, ASGITransport


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------- Test 1: Homepage returns 200 ----------
@pytest.mark.anyio
async def test_homepage_returns_200(client):
    """GET / should return 200."""
    response = await client.get("/")
    assert response.status_code == 200


# ---------- Test 2: Get all stores ----------
@pytest.mark.anyio
async def test_get_all_stores(client):
    """GET /api/stores should return stores."""
    response = await client.get("/api/stores")
    assert response.status_code == 200
    data = response.json()
    # Should be a list or have a data/stores key
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) > 0


# ---------- Test 3: Filter by city ----------
@pytest.mark.anyio
async def test_filter_by_city(client):
    """GET /api/stores?city=Chicago should return only Chicago stores."""
    response = await client.get("/api/stores?city=Chicago")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) > 0
    for store in stores:
        assert store["city"] == "Chicago"


# ---------- Test 4: Filter by brand ----------
@pytest.mark.anyio
async def test_filter_by_brand(client):
    """GET /api/stores?brand=KFC should return only KFC stores."""
    response = await client.get("/api/stores?brand=KFC")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) > 0
    for store in stores:
        assert store["brand"] == "KFC"


# ---------- Test 5: Filter by city and brand ----------
@pytest.mark.anyio
async def test_filter_by_city_and_brand(client):
    """GET /api/stores?city=Chicago&brand=KFC should filter both."""
    response = await client.get("/api/stores?city=Chicago&brand=KFC")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) > 0
    for store in stores:
        assert store["city"] == "Chicago"
        assert store["brand"] == "KFC"


# ---------- Test 6: Search by name ----------
@pytest.mark.anyio
async def test_search_stores(client):
    """GET /api/stores?search=pizza should return matching stores."""
    response = await client.get("/api/stores?search=pizza")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) > 0
    for store in stores:
        assert "pizza" in store["name"].lower() or "pizza" in store["brand"].lower()


# ---------- Test 7: Get specific store ----------
@pytest.mark.anyio
async def test_get_store_by_id(client):
    """GET /api/stores/1 should return the store with id 1."""
    response = await client.get("/api/stores/1")
    assert response.status_code == 200
    store = response.json()
    assert store["id"] == 1 or str(store["id"]) == "1"


# ---------- Test 8: Get non-existent store returns 404 ----------
@pytest.mark.anyio
async def test_get_nonexistent_store(client):
    """GET /api/stores/99999 should return 404."""
    response = await client.get("/api/stores/99999")
    assert response.status_code == 404


# ---------- Test 9: Get nearest stores ----------
@pytest.mark.anyio
async def test_get_nearest_stores(client):
    """GET /api/stores/nearest?lat=41.8781&lng=-87.6298&limit=5 should return 5 stores."""
    response = await client.get("/api/stores/nearest?lat=41.8781&lng=-87.6298&limit=5")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) == 5


# ---------- Test 10: Nearest stores sorted by distance ----------
@pytest.mark.anyio
async def test_nearest_sorted_by_distance(client):
    """Nearest stores should be sorted by distance ascending."""
    response = await client.get("/api/stores/nearest?lat=41.8781&lng=-87.6298&limit=10")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))

    distances = [s["distance_miles"] for s in stores]
    assert distances == sorted(distances), "Stores should be sorted by distance ascending"


# ---------- Test 11: Nearest stores have distance_miles field ----------
@pytest.mark.anyio
async def test_nearest_has_distance_field(client):
    """Each store in nearest response should have a distance_miles field."""
    response = await client.get("/api/stores/nearest?lat=34.0522&lng=-118.2437&limit=3")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))

    for store in stores:
        assert "distance_miles" in store, "Store missing 'distance_miles' field"
        assert isinstance(store["distance_miles"], (int, float))
        assert store["distance_miles"] >= 0


# ---------- Test 12: Get brands ----------
@pytest.mark.anyio
async def test_get_brands(client):
    """GET /api/brands should return list of unique brands."""
    response = await client.get("/api/brands")
    assert response.status_code == 200
    data = response.json()
    brands = data if isinstance(data, list) else data.get("brands", data.get("data", []))
    # Should have our 4 brands
    brand_names = [b if isinstance(b, str) else b.get("name", b.get("brand", "")) for b in brands]
    assert "KFC" in brand_names
    assert "Taco Bell" in brand_names
    assert "Pizza Hut" in brand_names
    assert "Habit Burger" in brand_names


# ---------- Test 13: Get cities ----------
@pytest.mark.anyio
async def test_get_cities(client):
    """GET /api/cities should return list of unique cities."""
    response = await client.get("/api/cities")
    assert response.status_code == 200
    data = response.json()
    cities = data if isinstance(data, list) else data.get("cities", data.get("data", []))
    city_names = [c if isinstance(c, str) else c.get("name", c.get("city", "")) for c in cities]
    assert "Chicago" in city_names
    assert "Los Angeles" in city_names
    assert len(city_names) >= 10


# ---------- Test 14: Pagination ----------
@pytest.mark.anyio
async def test_pagination(client):
    """GET /api/stores?page=1&limit=10 should return exactly 10 stores."""
    response = await client.get("/api/stores?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))
    assert len(stores) == 10


# ---------- Test 15: Store objects have required fields ----------
@pytest.mark.anyio
async def test_store_has_required_fields(client):
    """Store objects must have id, name, brand, city, latitude, longitude."""
    response = await client.get("/api/stores?limit=5")
    assert response.status_code == 200
    data = response.json()
    stores = data if isinstance(data, list) else data.get("stores", data.get("data", []))

    required_fields = ["id", "name", "brand", "city", "latitude", "longitude"]
    for store in stores:
        for field in required_fields:
            assert field in store, f"Store missing required field: '{field}'"


# ---------- Auto-submit ----------
def test_submit():
    """If all tests above pass, submit to CTF server."""
    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED!")
    print("=" * 50)

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import ctf_helper
    ctf_helper.submit(12, ["app/main.py"])
