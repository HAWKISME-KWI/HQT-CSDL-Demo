import threading
import uuid
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.service import db_service

COURT_ID = "e55a66a2-7e7a-4f5a-bd30-ac08be129236"   
USER1_ID = "0ae283a8-4c99-456e-a173-184b82e6cc7d"
USER2_ID = "54d1342d-1415-4fa7-b56a-27af47a860c4"
# ==========Thay đổi theo thời gian thực để test==============
START_TIME = "2026-06-23T11:00:00Z"   
END_TIME = "2026-06-23T12:00:00Z"
# ==========================================================

def book_court(user_id, user_name):
    print(f"[{user_name}] Bắt đầu đặt sân lúc {START_TIME}->{END_TIME}")
    try:
        result = db_service.book_court(user_id, COURT_ID, START_TIME, END_TIME)
        if "error" in result:
            print(f"[{user_name}] Lỗi: {result['error']}")
        else:
            print(f"[{user_name}] Đặt thành công!")
    except Exception as e:
        print(f"[{user_name}] Exception: {e}")

if __name__ == "__main__":
    print("=== TẤN CÔNG DOUBLE BOOKING ===")
    t1 = threading.Thread(target=book_court, args=(USER1_ID, "User1"))
    t2 = threading.Thread(target=book_court, args=(USER2_ID, "User2"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("\nKiểm tra DB xem có 2 booking trùng giờ cho cùng sân không?")
    print("Nếu có, đây là lỗi Lost Update (double booking).")