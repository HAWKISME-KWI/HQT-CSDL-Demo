import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import datetime
import sys
import os
import requests
import threading
from io import BytesIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.service import db_service

def format_datetime(dt_str):
    if dt_str:
        try:
            # Giả sử chuỗi đến là UTC, hiển thị dạng địa phương (cộng 7h)
            dt = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            dt_local = dt + datetime.timedelta(hours=7)  # Chuyển sang giờ Việt Nam
            return dt_local.strftime("%d/%m/%Y %H:%M")
        except:
            return dt_str
    return ""

class CourtManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản lý Sân bóng")
        self.root.geometry("1400x800")
        self.current_user = None

        self.court_id_map = {}
        self.booking_id_map = {}
        self.notification_id_map = {}
        self.court_image_map = {}
        self.image_cache = {}

        self.selected_court_id = None
        self.selected_date = None
        self.notebook = None

        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        self.build_login_frame()

    # ================== LOGIN / REGISTER ==================
    def build_login_frame(self):
        for widget in self.login_frame.winfo_children():
            widget.destroy()
        tk.Label(self.login_frame, text="ĐĂNG NHẬP", font=("Arial", 20, "bold")).pack(pady=20)
        tk.Label(self.login_frame, text="Tên đăng nhập:").pack()
        self.entry_username = tk.Entry(self.login_frame, width=30)
        self.entry_username.pack(pady=5)
        tk.Label(self.login_frame, text="Mật khẩu:").pack()
        self.entry_password = tk.Entry(self.login_frame, show="*", width=30)
        self.entry_password.pack(pady=5)
        btn_frame = tk.Frame(self.login_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Đăng nhập", command=self.do_login, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Đăng ký", command=self.show_register, width=15).pack(side=tk.LEFT, padx=5)

    def show_register(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Đăng ký")
        reg_win.geometry("400x450")
        tk.Label(reg_win, text="ĐĂNG KÝ", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(reg_win, text="Tên đăng nhập:").pack()
        entry_user = tk.Entry(reg_win, width=30)
        entry_user.pack(pady=5)

        tk.Label(reg_win, text="Mật khẩu:").pack()
        entry_pass = tk.Entry(reg_win, show="*", width=30)
        entry_pass.pack(pady=5)

        tk.Label(reg_win, text="Số điện thoại:").pack()
        entry_phone = tk.Entry(reg_win, width=30)
        entry_phone.pack(pady=5)

        tk.Label(reg_win, text="Vai trò:").pack()
        role_var = tk.StringVar(value="CUSTOMER")
        ttk.Combobox(reg_win, textvariable=role_var, values=["CUSTOMER", "COURT_MANAGER"]).pack(pady=5)

        def do_register():
            username = entry_user.get().strip()
            password = entry_pass.get().strip()
            phone = entry_phone.get().strip()
            role = role_var.get()
            if not username or not password or not phone:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin")
                return
            res = db_service.register(username, password, phone, role)
            if "error" in res:
                messagebox.showerror("Lỗi", res["error"])
            else:
                messagebox.showinfo("Thành công", "Đăng ký thành công! Vui lòng đăng nhập.")
                reg_win.destroy()

        tk.Button(reg_win, text="Đăng ký", command=do_register, width=20).pack(pady=20)

    def do_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return
        result = db_service.login(username, password)
        if "error" in result:
            messagebox.showerror("Lỗi", result["error"])
        else:
            self.current_user = result["user"]
            self.login_frame.destroy()
            self.build_main_app()

    # ================== MAIN APP ==================
    def build_main_app(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        toolbar = tk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(toolbar, text=f"👤 {self.current_user['username']} ({self.current_user['role']})").pack(side=tk.LEFT)
        tk.Button(toolbar, text="Đăng xuất", command=self.logout).pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_courts = tk.Frame(self.notebook)
        self.notebook.add(self.tab_courts, text="🏸 Sân")
        self.build_courts_tab()

        self.tab_my_bookings = tk.Frame(self.notebook)
        self.notebook.add(self.tab_my_bookings, text="📋 Lịch của tôi")
        self.build_my_bookings_tab()

        if self.current_user['role'] in ('MANAGER', 'COURT_MANAGER'):
            self.tab_manage = tk.Frame(self.notebook)
            self.notebook.add(self.tab_manage, text="⚙️ Quản lý")
            self.build_manage_tab()

            self.tab_stats = tk.Frame(self.notebook)
            self.notebook.add(self.tab_stats, text="📊 Thống kê")
            self.build_stats_tab()

        self.tab_notifications = tk.Frame(self.notebook)
        self.notebook.add(self.tab_notifications, text="🔔 Thông báo")
        self.build_notifications_tab()

        self.load_courts()

    # ================== TAB 1: SÂN ==================
    def build_courts_tab(self):
        main_pane = tk.PanedWindow(self.tab_courts, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, width=400)

        filter_frame = tk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        tk.Label(filter_frame, text="Mặt sân:").pack(side=tk.LEFT, padx=2)
        self.filter_surface = ttk.Combobox(filter_frame, values=["", "PVC", "WOOD", "CEMENT", "SYNTHETIC_RESIN"], width=12)
        self.filter_surface.pack(side=tk.LEFT, padx=2)
        tk.Label(filter_frame, text="Kích thước:").pack(side=tk.LEFT, padx=2)
        self.filter_size = ttk.Combobox(filter_frame, values=["", "SINGLE", "DOUBLE"], width=8)
        self.filter_size.pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Lọc", command=self.load_courts).pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree_courts = ttk.Treeview(tree_frame, columns=("id", "name", "address", "surface", "size", "price"), show="headings", height=20)
        self.tree_courts.heading("id", text="ID")
        self.tree_courts.heading("name", text="Tên sân")
        self.tree_courts.heading("address", text="Địa chỉ")
        self.tree_courts.heading("surface", text="Mặt")
        self.tree_courts.heading("size", text="Kích thước")
        self.tree_courts.heading("price", text="Giá/h")
        self.tree_courts.column("id", width=80)
        self.tree_courts.column("name", width=150)
        self.tree_courts.column("address", width=200)
        self.tree_courts.column("surface", width=100)
        self.tree_courts.column("size", width=100)
        self.tree_courts.column("price", width=80)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_courts.yview)
        self.tree_courts.configure(yscrollcommand=scrollbar.set)
        self.tree_courts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_courts.bind("<<TreeviewSelect>>", self.on_court_selected)

        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame, width=550)

        # Chi tiết sân
        detail_frame = tk.Frame(right_frame)
        detail_frame.pack(fill=tk.X, pady=5)
        self.court_image_label = tk.Label(detail_frame, text="Chọn sân để xem ảnh", bg="#f0f0f0", width=30, height=10)
        self.court_image_label.pack(side=tk.LEFT, padx=5)

        info_frame = tk.Frame(detail_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        self.court_name_label = tk.Label(info_frame, text="Tên: ", font=("Arial", 12, "bold"))
        self.court_name_label.pack(anchor=tk.W)
        self.court_address_label = tk.Label(info_frame, text="Địa chỉ: ")
        self.court_address_label.pack(anchor=tk.W)
        self.court_surface_label = tk.Label(info_frame, text="Mặt: ")
        self.court_surface_label.pack(anchor=tk.W)
        self.court_size_label = tk.Label(info_frame, text="Kích thước: ")
        self.court_size_label.pack(anchor=tk.W)
        self.court_price_label = tk.Label(info_frame, text="Giá/h: ")
        self.court_price_label.pack(anchor=tk.W)
        self.court_owner_phone_label = tk.Label(info_frame, text="SĐT chủ sân: ")
        self.court_owner_phone_label.pack(anchor=tk.W)
        self.court_free_label = tk.Label(info_frame, text="Trạng thái: ", foreground="green")
        self.court_free_label.pack(anchor=tk.W)

        # Lịch sân
        tk.Label(right_frame, text="Lịch sân trong ngày:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10,0))
        date_frame = tk.Frame(right_frame)
        date_frame.pack(anchor=tk.W, pady=2)
        tk.Label(date_frame, text="Ngày (DD/MM/YYYY):").pack(side=tk.LEFT)
        self.entry_date = tk.Entry(date_frame, width=12)
        self.entry_date.pack(side=tk.LEFT, padx=5)
        self.entry_date.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))
        tk.Button(date_frame, text="Xem lịch", command=self.load_court_schedule).pack(side=tk.LEFT, padx=5)

        self.schedule_tree = ttk.Treeview(right_frame, columns=("start", "end", "status"), show="headings", height=5)
        self.schedule_tree.heading("start", text="Bắt đầu")
        self.schedule_tree.heading("end", text="Kết thúc")
        self.schedule_tree.heading("status", text="Trạng thái")
        self.schedule_tree.pack(fill=tk.X, pady=5)

        # Form đặt sân - dùng Combobox chọn giờ
        book_frame = tk.LabelFrame(right_frame, text="Đặt sân", padx=5, pady=5)
        book_frame.pack(fill=tk.X, pady=10)

        tk.Label(book_frame, text="Bắt đầu:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.start_hour = ttk.Combobox(book_frame, values=[f"{i:02d}" for i in range(24)], width=4)
        self.start_hour.grid(row=0, column=1, padx=2, pady=2)
        self.start_hour.set("08")
        tk.Label(book_frame, text=":").grid(row=0, column=2)
        self.start_minute = ttk.Combobox(book_frame, values=["00", "15", "30", "45"], width=4)
        self.start_minute.grid(row=0, column=3, padx=2, pady=2)
        self.start_minute.set("00")

        tk.Label(book_frame, text="Kết thúc:").grid(row=0, column=4, sticky=tk.W, padx=(15,5), pady=2)
        self.end_hour = ttk.Combobox(book_frame, values=[f"{i:02d}" for i in range(24)], width=4)
        self.end_hour.grid(row=0, column=5, padx=2, pady=2)
        self.end_hour.set("09")
        tk.Label(book_frame, text=":").grid(row=0, column=6)
        self.end_minute = ttk.Combobox(book_frame, values=["00", "15", "30", "45"], width=4)
        self.end_minute.grid(row=0, column=7, padx=2, pady=2)
        self.end_minute.set("00")

        tk.Label(book_frame, text="Chi phí dự kiến:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.label_cost = tk.Label(book_frame, text="0 VND", foreground="blue", font=("Arial", 10, "bold"))
        self.label_cost.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5)
        tk.Button(book_frame, text="Tính tiền", command=self.calculate_cost).grid(row=1, column=4, padx=5)
        tk.Button(book_frame, text="Đặt sân", command=self.book_court, bg="lightgreen").grid(row=1, column=5, columnspan=2, padx=5)

    def load_courts(self):
        def fetch():
            surface = self.filter_surface.get() if self.filter_surface.get() else None
            size = self.filter_size.get() if self.filter_size.get() else None
            res = db_service.filter_courts(surface=surface, size=size)
            self.root.after(0, self.update_courts_tree, res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_courts_tree(self, result):
        for item in self.tree_courts.get_children():
            self.tree_courts.delete(item)
        if "data" in result:
            for court in result["data"]:
                cid = court['court_id']
                short_id = str(cid)[:8]
                self.court_id_map[short_id] = cid
                self.court_image_map[cid] = court.get('image_url')
                self.tree_courts.insert("", tk.END, values=(
                    short_id,
                    court['court_name'],
                    court.get('address', ''),
                    court['surface'],
                    court['size'],
                    court['price_per_hour']
                ))

    def on_court_selected(self, event):
        sel = self.tree_courts.selection()
        if not sel:
            return
        short_id = self.tree_courts.item(sel[0])['values'][0]
        cid = self.court_id_map.get(short_id)
        if not cid:
            return
        self.selected_court_id = cid

        res = db_service.get_court_by_id(cid)
        if "data" in res:
            court = res["data"]
            self.court_name_label.config(text=f"Tên: {court['court_name']}")
            self.court_address_label.config(text=f"Địa chỉ: {court.get('address', '')}")
            self.court_surface_label.config(text=f"Mặt: {court['court_surfaces_type']}")
            self.court_size_label.config(text=f"Kích thước: {court['court_sizes_type']}")
            self.court_price_label.config(text=f"Giá/h: {court['price_per_hour']} VND")
            owner_phone = court.get('owner_phone')
            if owner_phone:
                self.court_owner_phone_label.config(text=f"SĐT chủ sân: {owner_phone}")
            else:
                self.court_owner_phone_label.config(text="SĐT chủ sân: Không có")

            free_res = db_service.get_available_courts()
            if "data" in free_res:
                for c in free_res["data"]:
                    if c['court_id'] == cid:
                        if c.get('is_currently_free'):
                            self.court_free_label.config(text="Trạng thái: Trống", foreground="green")
                        else:
                            self.court_free_label.config(text="Trạng thái: Đang có booking", foreground="red")
                        break

            url = court.get('image_url')
            if url and cid in self.image_cache:
                self.court_image_label.config(image=self.image_cache[cid], text="")
            elif url:
                threading.Thread(target=self._fetch_img, args=(cid, url), daemon=True).start()
            else:
                self.court_image_label.config(image="", text="Không có ảnh")

        self.load_court_schedule()

    def _fetch_img(self, cid, url):
        try:
            resp = requests.get(url, timeout=5)
            img = Image.open(BytesIO(resp.content))
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.image_cache[cid] = photo
            self.root.after(0, lambda: self.court_image_label.config(image=photo, text=""))
        except:
            self.root.after(0, lambda: self.court_image_label.config(text="Lỗi tải ảnh"))

    def load_court_schedule(self):
        if not self.selected_court_id:
            return
        date_str = self.entry_date.get().strip()
        try:
            date_obj = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
        except:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ (DD/MM/YYYY)")
            return
        self.selected_date = date_obj

        def fetch():
            res = db_service.get_court_schedule(self.selected_court_id, date_obj)
            self.root.after(0, self.update_schedule_tree, res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_schedule_tree(self, result):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        if "data" in result:
            for row in result["data"]:
                self.schedule_tree.insert("", tk.END, values=(
                    format_datetime(row['start_time']),
                    format_datetime(row['end_time']),
                    row['status']
                ))

    def get_start_end_datetime(self):
        date_str = self.entry_date.get().strip()
        try:
            date_obj = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
        except:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ (DD/MM/YYYY)")
            return None, None

        try:
            start_h = int(self.start_hour.get())
            start_m = int(self.start_minute.get())
            end_h = int(self.end_hour.get())
            end_m = int(self.end_minute.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Giờ không hợp lệ")
            return None, None

        # Tạo datetime local (giả sử múi giờ Việt Nam UTC+7)
        start_dt = datetime.datetime.combine(date_obj, datetime.time(start_h, start_m))
        end_dt = datetime.datetime.combine(date_obj, datetime.time(end_h, end_m))
        return start_dt, end_dt

    def calculate_cost(self):
        if not self.selected_court_id:
            messagebox.showinfo("Thông báo", "Chọn sân trước")
            return
        start_dt, end_dt = self.get_start_end_datetime()
        if not start_dt or not end_dt:
            return
        if end_dt <= start_dt:
            messagebox.showerror("Lỗi", "Thời gian kết thúc phải sau bắt đầu")
            return

        # Chuyển sang UTC (trừ đi 7 giờ)
        start_utc = (start_dt - datetime.timedelta(hours=7)).isoformat() + 'Z'
        end_utc = (end_dt - datetime.timedelta(hours=7)).isoformat() + 'Z'
        res = db_service.calculate_cost(self.selected_court_id, start_utc, end_utc)
        if "data" in res:
            self.label_cost.config(text=f"{res['data']} VND")
        else:
            self.label_cost.config(text="Lỗi")

    def book_court(self):
        if not self.selected_court_id:
            messagebox.showinfo("Thông báo", "Chọn sân trước")
            return
        start_dt, end_dt = self.get_start_end_datetime()
        if not start_dt or not end_dt:
            return
        if end_dt <= start_dt:
            messagebox.showerror("Lỗi", "Thời gian kết thúc phải sau bắt đầu")
            return
        if start_dt < datetime.datetime.now():
            messagebox.showerror("Lỗi", "Không thể đặt trong quá khứ")
            return

        # Chuyển sang UTC (trừ đi 7 giờ)
        start_utc = (start_dt - datetime.timedelta(hours=7)).isoformat() + 'Z'
        end_utc = (end_dt - datetime.timedelta(hours=7)).isoformat() + 'Z'

        if not messagebox.askyesno("Xác nhận", f"Đặt sân từ {start_dt.strftime('%H:%M')} đến {end_dt.strftime('%H:%M')}? Chi phí: {self.label_cost.cget('text')}"):
            return
        res = db_service.book_court(self.current_user['user_id'], self.selected_court_id, start_utc, end_utc)
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đặt sân thành công! Đang chờ xác nhận.")
            self.load_court_schedule()
            self.load_my_bookings()

    # ================== TAB 2: LỊCH SỬ CỦA TÔI ==================
    def build_my_bookings_tab(self):
        frame = tk.Frame(self.tab_my_bookings)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree_my_bookings = ttk.Treeview(frame, columns=("id", "court", "start", "end", "status", "cost"), show="headings")
        self.tree_my_bookings.heading("id", text="ID")
        self.tree_my_bookings.heading("court", text="Sân")
        self.tree_my_bookings.heading("start", text="Bắt đầu")
        self.tree_my_bookings.heading("end", text="Kết thúc")
        self.tree_my_bookings.heading("status", text="Trạng thái")
        self.tree_my_bookings.heading("cost", text="Chi phí")
        self.tree_my_bookings.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Hủy đặt", command=self.cancel_my_booking).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Làm mới", command=self.load_my_bookings).pack(side=tk.LEFT)

        self.load_my_bookings()

    def load_my_bookings(self):
        def fetch():
            res = db_service.search_bookings(user_id=self.current_user['user_id'])
            self.root.after(0, self.update_my_bookings, res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_my_bookings(self, result):
        for item in self.tree_my_bookings.get_children():
            self.tree_my_bookings.delete(item)
        if "data" in result:
            for row in result["data"]:
                bid = row['booking_id']
                short_id = str(bid)[:8]
                self.booking_id_map[short_id] = bid
                self.tree_my_bookings.insert("", tk.END, values=(
                    short_id,
                    row['court_name'],
                    format_datetime(row['start_time']),
                    format_datetime(row['end_time']),
                    row['status'],
                    row['total_cost']
                ))

    def cancel_my_booking(self):
        sel = self.tree_my_bookings.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Chọn một booking để hủy")
            return
        short_id = self.tree_my_bookings.item(sel[0])['values'][0]
        booking_id = self.booking_id_map.get(short_id)
        if not booking_id:
            messagebox.showerror("Lỗi", "Không tìm thấy booking")
            return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hủy booking này?"):
            return
        res = db_service.cancel_booking_customer(booking_id, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã hủy booking")
            self.load_my_bookings()
            self.load_court_schedule()

    # ================== TAB 3: QUẢN LÝ ==================
    def build_manage_tab(self):
        manage_notebook = ttk.Notebook(self.tab_manage)
        manage_notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_manage_courts = tk.Frame(manage_notebook)
        manage_notebook.add(self.tab_manage_courts, text="Sân")
        self.build_manage_courts()

        self.tab_manage_bookings = tk.Frame(manage_notebook)
        manage_notebook.add(self.tab_manage_bookings, text="Booking")
        self.build_manage_bookings()

    # ---- Quản lý sân ----
    def build_manage_courts(self):
        frame = tk.Frame(self.tab_manage_courts)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = tk.LabelFrame(frame, text="Thêm sân mới", padx=10, pady=10)
        form_frame.pack(fill=tk.X, pady=5)

        tk.Label(form_frame, text="Tên sân:").grid(row=0, column=0, sticky=tk.W)
        self.entry_court_name = tk.Entry(form_frame, width=30)
        self.entry_court_name.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form_frame, text="Địa chỉ:").grid(row=0, column=2, sticky=tk.W)
        self.entry_address = tk.Entry(form_frame, width=40)
        self.entry_address.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(form_frame, text="Mặt sân:").grid(row=1, column=0, sticky=tk.W)
        self.combo_surface = ttk.Combobox(form_frame, values=["PVC", "WOOD", "CEMENT", "SYNTHETIC_RESIN"], width=15)
        self.combo_surface.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form_frame, text="Kích thước:").grid(row=1, column=2, sticky=tk.W)
        self.combo_size = ttk.Combobox(form_frame, values=["SINGLE", "DOUBLE"], width=15)
        self.combo_size.grid(row=1, column=3, padx=5, pady=2)

        tk.Label(form_frame, text="Giá/h (VND):").grid(row=2, column=0, sticky=tk.W)
        self.entry_price_hour = tk.Entry(form_frame, width=15)
        self.entry_price_hour.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form_frame, text="Giá 3h (VND):").grid(row=2, column=2, sticky=tk.W)
        self.entry_price_3h = tk.Entry(form_frame, width=15)
        self.entry_price_3h.grid(row=2, column=3, padx=5, pady=2)

        tk.Label(form_frame, text="Ảnh sân:").grid(row=3, column=0, sticky=tk.W)
        self.entry_image_path = tk.Entry(form_frame, width=25)
        self.entry_image_path.grid(row=3, column=1, padx=5, pady=2)
        tk.Button(form_frame, text="Chọn ảnh", command=self.choose_image).grid(row=3, column=2, padx=5)

        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10)
        tk.Button(btn_frame, text="Thêm sân", command=self.add_court, bg="lightblue").pack(side=tk.LEFT, padx=5)

        list_frame = tk.LabelFrame(frame, text="Danh sách sân hiện có", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.tree_manage_courts = ttk.Treeview(list_frame, columns=("id", "name", "address", "surface", "size", "price", "active"), show="headings")
        self.tree_manage_courts.heading("id", text="ID")
        self.tree_manage_courts.heading("name", text="Tên")
        self.tree_manage_courts.heading("address", text="Địa chỉ")
        self.tree_manage_courts.heading("surface", text="Mặt")
        self.tree_manage_courts.heading("size", text="Kích thước")
        self.tree_manage_courts.heading("price", text="Giá/h")
        self.tree_manage_courts.heading("active", text="Hoạt động")
        self.tree_manage_courts.pack(fill=tk.BOTH, expand=True)

        btn_manage = tk.Frame(list_frame)
        btn_manage.pack(fill=tk.X, pady=5)
        tk.Button(btn_manage, text="Xóa (ngừng hoạt động)", command=self.delete_court).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_manage, text="Làm mới", command=self.load_manage_courts).pack(side=tk.LEFT)

        self.load_manage_courts()

    def choose_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if path:
            self.entry_image_path.delete(0, tk.END)
            self.entry_image_path.insert(0, path)

    def load_manage_courts(self):
        def fetch():
            res = db_service.filter_courts()
            self.root.after(0, self.update_manage_courts, res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_manage_courts(self, result):
        for item in self.tree_manage_courts.get_children():
            self.tree_manage_courts.delete(item)
        if "data" in result:
            for c in result["data"]:
                self.tree_manage_courts.insert("", tk.END, values=(
                    str(c['court_id'])[:8],
                    c['court_name'],
                    c.get('address', ''),
                    c['surface'],
                    c['size'],
                    c['price_per_hour'],
                    "Có" if c.get('is_currently_free') is not None else "N/A"
                ))

    def add_court(self):
        name = self.entry_court_name.get().strip()
        address = self.entry_address.get().strip()
        surface = self.combo_surface.get()
        size = self.combo_size.get()
        price_hour = self.entry_price_hour.get().strip()
        price_3h = self.entry_price_3h.get().strip()
        image_path = self.entry_image_path.get().strip()

        if not name or not address or not surface or not size or not price_hour or not price_3h:
            messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin")
            return
        try:
            price_hour = float(price_hour)
            price_3h = float(price_3h)
        except:
            messagebox.showerror("Lỗi", "Giá phải là số")
            return

        res = db_service.add_court(name, address, surface, size, price_hour, price_3h, image_path, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Thêm sân thành công!")
            self.load_manage_courts()
            self.load_courts()

    def delete_court(self):
        sel = self.tree_manage_courts.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Chọn sân cần xóa")
            return
        short_id = self.tree_manage_courts.item(sel[0])['values'][0]
        cid = self.court_id_map.get(short_id)
        if not cid:
            messagebox.showerror("Lỗi", "Không tìm thấy sân")
            return
        if not messagebox.askyesno("Xác nhận", f"Xóa sân này? (ngừng hoạt động)"):
            return
        res = db_service.delete_court(cid, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã xóa sân")
            self.load_manage_courts()
            self.load_courts()

    # ---- Quản lý booking ----
    def build_manage_bookings(self):
        frame = tk.Frame(self.tab_manage_bookings)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        filter_frame = tk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=5)
        tk.Label(filter_frame, text="Trạng thái:").pack(side=tk.LEFT)
        self.filter_booking_status = ttk.Combobox(filter_frame, values=["", "PENDING", "BOOKED", "COMPLETED", "CANCELLED", "REJECTED"], width=12)
        self.filter_booking_status.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Lọc", command=self.load_manage_bookings).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Làm mới", command=self.load_manage_bookings).pack(side=tk.LEFT)

        self.tree_manage_bookings = ttk.Treeview(frame, columns=("id", "user", "court", "start", "end", "status", "cost"), show="headings")
        self.tree_manage_bookings.heading("id", text="ID")
        self.tree_manage_bookings.heading("user", text="Người đặt")
        self.tree_manage_bookings.heading("court", text="Sân")
        self.tree_manage_bookings.heading("start", text="Bắt đầu")
        self.tree_manage_bookings.heading("end", text="Kết thúc")
        self.tree_manage_bookings.heading("status", text="Trạng thái")
        self.tree_manage_bookings.heading("cost", text="Chi phí")
        self.tree_manage_bookings.pack(fill=tk.BOTH, expand=True)

        action_frame = tk.Frame(frame)
        action_frame.pack(fill=tk.X, pady=5)
        tk.Button(action_frame, text="Duyệt", command=self.approve_booking).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Từ chối", command=self.reject_booking).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Hoàn thành", command=self.complete_booking).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Hủy", command=self.cancel_booking_admin).pack(side=tk.LEFT, padx=5)

        self.load_manage_bookings()

    def load_manage_bookings(self):
        def fetch():
            status = self.filter_booking_status.get() if self.filter_booking_status.get() else None
            res = db_service.search_bookings(status=status)
            self.root.after(0, self.update_manage_bookings, res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_manage_bookings(self, result):
        for item in self.tree_manage_bookings.get_children():
            self.tree_manage_bookings.delete(item)
        if "data" in result:
            for row in result["data"]:
                bid = row['booking_id']
                short_id = str(bid)[:8]
                self.booking_id_map[short_id] = bid
                self.tree_manage_bookings.insert("", tk.END, values=(
                    short_id,
                    row['user_name'],
                    row['court_name'],
                    format_datetime(row['start_time']),
                    format_datetime(row['end_time']),
                    row['status'],
                    row['total_cost']
                ))

    def get_selected_booking_id(self):
        sel = self.tree_manage_bookings.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Chọn một booking")
            return None
        short_id = self.tree_manage_bookings.item(sel[0])['values'][0]
        bid = self.booking_id_map.get(short_id)
        if not bid:
            messagebox.showerror("Lỗi", "Không tìm thấy booking")
            return None
        return bid

    def approve_booking(self):
        booking_id = self.get_selected_booking_id()
        if not booking_id:
            return
        if not messagebox.askyesno("Xác nhận", "Duyệt booking này?"):
            return
        res = db_service.approve_booking(booking_id, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã duyệt booking")
            self.load_manage_bookings()
            self.load_my_bookings()

    def reject_booking(self):
        booking_id = self.get_selected_booking_id()
        if not booking_id:
            return
        if not messagebox.askyesno("Xác nhận", "Từ chối booking này?"):
            return
        res = db_service.reject_booking(booking_id, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã từ chối booking")
            self.load_manage_bookings()
            self.load_my_bookings()

    def complete_booking(self):
        booking_id = self.get_selected_booking_id()
        if not booking_id:
            return
        if not messagebox.askyesno("Xác nhận", "Đánh dấu booking đã hoàn thành?"):
            return
        res = db_service.complete_booking_admin(booking_id, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã hoàn thành booking")
            self.load_manage_bookings()
            self.load_my_bookings()

    def cancel_booking_admin(self):
        booking_id = self.get_selected_booking_id()
        if not booking_id:
            return
        if not messagebox.askyesno("Xác nhận", "Hủy booking này?"):
            return
        res = db_service.cancel_booking_admin(booking_id, self.current_user['user_id'])
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã hủy booking")
            self.load_manage_bookings()
            self.load_my_bookings()

    # ================== TAB 4: THỐNG KÊ ==================
    def build_stats_tab(self):
        frame = tk.Frame(self.tab_stats)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame, text="DOANH THU THEO NGÀY", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        self.tree_stats_revenue = ttk.Treeview(frame, columns=("date", "revenue"), show="headings", height=6)
        self.tree_stats_revenue.heading("date", text="Ngày")
        self.tree_stats_revenue.heading("revenue", text="Doanh thu (VND)")
        self.tree_stats_revenue.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="TOP SÂN ĐƯỢC ĐẶT NHIỀU NHẤT", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.tree_stats_top = ttk.Treeview(frame, columns=("court", "address", "owner_phone", "count"), show="headings", height=6)
        self.tree_stats_top.heading("court", text="Tên sân")
        self.tree_stats_top.heading("address", text="Địa chỉ")
        self.tree_stats_top.heading("owner_phone", text="SĐT chủ sân")
        self.tree_stats_top.heading("count", text="Số lần đặt")
        self.tree_stats_top.pack(fill=tk.X, pady=5)

        btn_stats = tk.Frame(frame)
        btn_stats.pack(fill=tk.X, pady=10)
        tk.Button(btn_stats, text="Làm mới", command=self.load_stats).pack(side=tk.LEFT)

        self.load_stats()

    def load_stats(self):
        def fetch():
            rev_res = db_service.get_daily_revenue()
            top_res = db_service.get_top_courts(5)
            self.root.after(0, self.update_stats, rev_res, top_res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_stats(self, rev_res, top_res):
        for item in self.tree_stats_revenue.get_children():
            self.tree_stats_revenue.delete(item)
        if "data" in rev_res:
            for row in rev_res["data"]:
                self.tree_stats_revenue.insert("", tk.END, values=(row['booking_date'], row['revenue']))

        for item in self.tree_stats_top.get_children():
            self.tree_stats_top.delete(item)
        if "data" in top_res:
            for row in top_res["data"]:
                self.tree_stats_top.insert("", tk.END, values=(
                    row['court_name'],
                    row['address'],
                    row['owner_phone'],
                    row['total_bookings']
                ))

    # ================== TAB 5: THÔNG BÁO ==================
    def build_notifications_tab(self):
        frame = tk.Frame(self.tab_notifications)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree_notifications = ttk.Treeview(frame, columns=("id", "title", "content", "created", "read"), show="headings")
        self.tree_notifications.heading("id", text="ID")
        self.tree_notifications.heading("title", text="Tiêu đề")
        self.tree_notifications.heading("content", text="Nội dung")
        self.tree_notifications.heading("created", text="Thời gian")
        self.tree_notifications.heading("read", text="Đã đọc")
        self.tree_notifications.column("id", width=80)
        self.tree_notifications.column("title", width=150)
        self.tree_notifications.column("content", width=300)
        self.tree_notifications.column("created", width=150)
        self.tree_notifications.column("read", width=80)
        self.tree_notifications.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Làm mới", command=self.load_notifications).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Đánh dấu đã đọc", command=self.mark_read).pack(side=tk.LEFT)

        self.load_notifications()

    def load_notifications(self):
        def fetch():
            res = db_service.get_notifications(self.current_user['user_id'])
            self.root.after(0, self.update_notifications, res)
        threading.Thread(target=fetch, daemon=True).start()

    def update_notifications(self, result):
        for item in self.tree_notifications.get_children():
            self.tree_notifications.delete(item)
        if "data" in result:
            for row in result["data"]:
                nid = row['notification_id']
                short_id = str(nid)[:8]
                self.notification_id_map[short_id] = nid
                self.tree_notifications.insert("", tk.END, values=(
                    short_id,
                    row['title'],
                    row['content'],
                    format_datetime(row['created_at']),
                    "Đã đọc" if row['is_read'] else "Chưa đọc"
                ))

    def mark_read(self):
        sel = self.tree_notifications.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Chọn thông báo cần đánh dấu đã đọc")
            return
        short_id = self.tree_notifications.item(sel[0])['values'][0]
        nid = self.notification_id_map.get(short_id)
        if not nid:
            messagebox.showerror("Lỗi", "Không tìm thấy thông báo")
            return
        res = db_service.mark_notification_read(nid)
        if "error" in res:
            messagebox.showerror("Lỗi", res["error"])
        else:
            messagebox.showinfo("Thành công", "Đã đánh dấu đã đọc")
            self.load_notifications()

    # ================== LOGOUT ==================
    def logout(self):
        self.main_frame.destroy()
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        self.build_login_frame()

if __name__ == "__main__":
    root = tk.Tk()
    app = CourtManagerApp(root)
    root.mainloop()