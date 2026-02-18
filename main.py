from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio

# --- IMPORT YOUR MODULES ---
from daily_cache import fetch_daily_forecast
from weekly_cache import auto_refresh, fetch_weekly_forecast
from read_ecocrop import load_ecocrop_data, find_crops_by_soil
from medic import search
from crop_summary import get_crop_summary
from seasonforecast import get_season_forecast
from advise import generate_advice



from fastapi import File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from supabase_client import supabase
from datetime import datetime
import uuid
import os




# --- APP ---
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Load CSV ONCE
ecocrop_df = load_ecocrop_data()

# --- STARTUP ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_refresh())

# --- ROUTES ---
@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/daily-forecast/{district}")
def daily_forecast(district: str):
    return fetch_daily_forecast(district)

@app.get("/weekly/{district}")
def weekly_forecast(district: str):
    return fetch_weekly_forecast(district)

@app.get("/query-crops/")
def query_crops(
    fertility: str = Query(...),
    drainage: str = Query(...),
    texture: str = Query(...)
):
    return find_crops_by_soil(fertility, drainage, texture, ecocrop_df)

@app.get("/api/medic")
def medic_api(
    query: str = Query(...),
    search_type: str = Query("plant")
):
    return search(query, search_type)

@app.get("/api/crop-summary")
def crop_summary_api(
    name: str = Query(..., description="Crop name")
):
    return get_crop_summary(name)

@app.get("/api/season-forecast")
def season_forecast_api(
    district: str = Query(..., description="District name, e.g. Zomba")
):
    return get_season_forecast(district)

@app.get("/advise")
def advise(
    crop: str = Query(...),
    district: str = Query(...)
):
    result = generate_advice(crop, district)
    return {"advice": result}

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")




@app.post("/post")
async def create_post(
    title: str = Form(None),
    content: str = Form(None),
    category: str = Form(...),
    district: str = Form(None),
    image: UploadFile = File(None),
):
    if not title and not content and not image:
        return {"error": "You must provide text (title/content) or an image."}

    image_url = None

    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"community/{file_name}"

        file_bytes = await image.read()

        supabase.storage.from_("community-images").upload(
            file_path,
            file_bytes,
            {"content-type": image.content_type},
        )

        # Safe handling for public URL
        image_url_response = supabase.storage.from_("community-images").get_public_url(file_path)
        image_url = image_url_response.get("publicUrl") if isinstance(image_url_response, dict) else str(image_url_response)

    post_data = {
        "title": title,
        "content": content,
        "category": category,
        "district": district,
        "image_url": image_url,
        "published": True,
        "created_at": datetime.utcnow().isoformat()
    }

    supabase.table("community_posts").insert(post_data).execute()

    return {"status": "Post created successfully!"}




from fastapi.responses import JSONResponse

# ---------------- GET ALL POSTS ----------------
@app.get("/posts", response_class=JSONResponse)
def get_posts():
    response = (
        supabase
        .table("community_posts")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


# ---------------- GET SINGLE POST ----------------
@app.get("/posts/{post_id}", response_class=JSONResponse)
def get_single_post(post_id: str):
    response = (
        supabase
        .table("community_posts")
        .select("*")
        .eq("id", post_id)
        .single()
        .execute()
    )
    return response.data


# ---------------- DELETE POST ----------------
@app.delete("/posts/{post_id}")
def delete_post(post_id: str):
    supabase.table("community_posts").delete().eq("id", post_id).execute()
    return {"status": "Post deleted"}
