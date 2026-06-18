from supabase import create_client
from dotenv import load_dotenv
import os
import bcrypt
import datetime
import io
import time
from PIL import Image

load_dotenv()
SECRET_URL = os.getenv("SUPABASE_URL")
SECRET_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SECRET_URL, SECRET_KEY)

# ================== AUTHENTICATION ==================
def register(username, password, phone_number, role='CUSTOMER'):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    data = {
        "username": username,
        "password_hash": hashed,
        "phone_number": phone_number,
        "role": role,
        "is_active": True
    }
    for attempt in range(3):
        try:
            response = supabase.table("users").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def login(username, password):
    for attempt in range(3):
        try:
            response = supabase.table("users").select("*").eq("username", username).execute()
            if not response.data:
                return {"error": "User not found"}
            user = response.data[0]
            if not user.get("is_active", True):
                return {"error": "Account is deactivated"}
            if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                return {"error": "Invalid password"}
            supabase.table("users").update({"last_login": datetime.datetime.now(datetime.timezone.utc).isoformat()}).eq("user_id", user["user_id"]).execute()
            user.pop("password_hash", None)
            return {"success": True, "user": user}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

# ================== BOOKING ==================
def book_court(user_id, court_id, start_time, end_time):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_book_court", {
                "p_user_id": user_id,
                "p_court_id": court_id,
                "p_start": start_time,
                "p_end": end_time
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def cancel_booking_customer(booking_id, user_id):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_cancel_booking_customer", {
                "p_booking_id": booking_id,
                "p_user_id": user_id
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def cancel_booking_admin(booking_id, admin_id):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_cancel_booking_powerfull", {
                "p_booking_id": booking_id,
                "p_admin_id": admin_id
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def complete_booking_admin(booking_id, admin_id):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_complete_booking", {
                "p_booking_id": booking_id,
                "p_admin_id": admin_id
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def approve_booking(booking_id, admin_id):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_approve_booking", {
                "p_booking_id": booking_id,
                "p_admin_id": admin_id
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def reject_booking(booking_id, admin_id):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_reject_booking", {
                "p_booking_id": booking_id,
                "p_admin_id": admin_id
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

# ================== COURT MANAGEMENT ==================
def upload_court_image(file_path, court_id):
    try:
        img = Image.open(file_path)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"court_{court_id}_{timestamp}.jpg"
        res = supabase.storage.from_("court_images").upload(
            file_name,
            buffer.getvalue(),
            {"content-type": "image/jpeg"}
        )
        if hasattr(res, 'error') and res.error:
            return {"error": res.error}
        public_url = supabase.storage.from_("court_images").get_public_url(file_name)
        return {"success": True, "url": public_url}
    except Exception as e:
        return {"error": str(e)}

def add_court(court_name, address, surface, size, price_hour, price_3h, image_path, admin_id):
    try:
        if price_3h <= price_hour:
            return {"error": "3-hour price must be greater than 1-hour price"}
        for attempt in range(3):
            try:
                result = supabase.rpc("sp_add_court", {
                    "p_court_name": court_name,
                    "p_address": address,
                    "p_surface": surface,
                    "p_size": size,
                    "p_price_per_hour": price_hour,
                    "p_price_per_three_hours": price_3h,
                    "p_admin_id": admin_id,
                    "p_image_url": None
                }).execute()
                if hasattr(result, 'error') and result.error:
                    return {"error": result.error}
                court_id = result.data
                if image_path:
                    upload_result = upload_court_image(image_path, court_id)
                    if upload_result.get("error"):
                        return {"error": upload_result["error"]}
                    image_url = upload_result["url"]
                    update_response = supabase.table("courts").update({"image_url": image_url}).eq("court_id", court_id).execute()
                    if hasattr(update_response, 'error') and update_response.error:
                        return {"error": update_response.error}
                return {"success": True, "court_id": court_id}
            except Exception as e:
                if "WinError 10035" in str(e) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": str(e)}
        return {"error": "Max retries exceeded"}
    except Exception as e:
        return {"error": str(e)}

def update_court(court_id, court_name, address, surface, size, price_hour, price_3h, is_active, image_url, admin_id):
    try:
        data = {}
        if court_name is not None: data["court_name"] = court_name
        if address is not None: data["address"] = address
        if surface is not None: data["court_surfaces_type"] = surface
        if size is not None: data["court_sizes_type"] = size
        if price_hour is not None: data["price_per_hour"] = price_hour
        if price_3h is not None: data["price_per_three_hours"] = price_3h
        if is_active is not None: data["is_active"] = is_active
        if image_url is not None: data["image_url"] = image_url
        if not data:
            return {"error": "No fields to update"}
        for attempt in range(3):
            try:
                response = supabase.table("courts").update(data).eq("court_id", court_id).execute()
                if hasattr(response, 'error') and response.error:
                    return {"error": response.error}
                return {"success": True, "data": response.data}
            except Exception as e:
                if "WinError 10035" in str(e) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": str(e)}
        return {"error": "Max retries exceeded"}
    except Exception as e:
        return {"error": str(e)}

def delete_court(court_id, admin_id):
    for attempt in range(3):
        try:
            response = supabase.rpc("sp_delete_court", {
                "p_court_id": court_id,
                "p_admin_id": admin_id
            }).execute()
            if hasattr(response, 'error') and response.error:
                return {"error": response.error}
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

# ================== VIEWS & QUERIES ==================
def get_available_courts():
    for attempt in range(3):
        try:
            response = supabase.table("view_available_courts").select("*").execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_booking_history(user_id):
    return search_bookings(user_id=user_id)

def get_admin_dashboard_stats():
    for attempt in range(3):
        try:
            response = supabase.table("view_admin_dashboard").select("*").execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_all_bookings(owner_id=None):
    return search_bookings(owner_id=owner_id)

def calculate_cost(court_id, start_time, end_time):
    for attempt in range(3):
        try:
            response = supabase.rpc("fn_calculate_booking_cost", {
                "p_court_id": court_id,
                "p_start_time": start_time,
                "p_end_time": end_time
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def search_bookings(user_id=None, from_date=None, to_date=None, status=None, court_id=None, owner_id=None):
    params = {
        "p_user_id": user_id,
        "p_from_date": from_date.isoformat() if isinstance(from_date, datetime.datetime) else from_date,
        "p_to_date": to_date.isoformat() if isinstance(to_date, datetime.datetime) else to_date,
        "p_status": status,
        "p_court_id": court_id,
        "p_owner_id": owner_id
    }
    params = {k: v for k, v in params.items() if v is not None}
    for attempt in range(3):
        try:
            response = supabase.rpc("fn_search_bookings", params).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def filter_courts(surface=None, size=None, min_price=None, max_price=None, is_free=None):
    params = {}
    if surface: params["p_surface"] = surface
    if size: params["p_size"] = size
    if min_price is not None: params["p_min_price"] = min_price
    if max_price is not None: params["p_max_price"] = max_price
    if is_free is not None: params["p_is_free"] = is_free
    for attempt in range(3):
        try:
            response = supabase.rpc("fn_filter_courts", params).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_court_by_id(court_id):
    for attempt in range(3):
        try:
            court_res = supabase.table("courts").select("*").eq("court_id", court_id).execute()
            if not court_res.data:
                return {"error": "Court not found"}
            court = court_res.data[0]
            owner_id = court.get("owner_id")
            if owner_id:
                user_res = supabase.table("users").select("phone_number").eq("user_id", owner_id).execute()
                if user_res.data:
                    court["owner_phone"] = user_res.data[0]["phone_number"]
                else:
                    court["owner_phone"] = None
            else:
                court["owner_phone"] = None
            return {"success": True, "data": court}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_court_schedule(court_id, date):
    for attempt in range(3):
        try:
            response = supabase.rpc("fn_get_court_schedule", {
                "p_court_id": court_id,
                "p_date": date.isoformat() if isinstance(date, datetime.date) else date
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_daily_revenue(from_date=None, to_date=None, owner_id=None):
    params = {}
    if from_date: params["from_date"] = from_date.isoformat() if isinstance(from_date, datetime.date) else from_date
    if to_date: params["to_date"] = to_date.isoformat() if isinstance(to_date, datetime.date) else to_date
    if owner_id: params["p_owner_id"] = owner_id
    for attempt in range(3):
        try:
            response = supabase.rpc("fn_daily_revenue", params).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_top_courts(limit=10, owner_id=None):
    params = {"limit_count": limit}
    if owner_id: params["p_owner_id"] = owner_id
    for attempt in range(3):
        try:
            response = supabase.rpc("fn_top_courts", params).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def get_notifications(user_id):
    for attempt in range(3):
        try:
            response = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def mark_notification_read(notification_id):
    for attempt in range(3):
        try:
            response = supabase.table("notifications").update({"is_read": True}).eq("notification_id", notification_id).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            if "WinError 10035" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}