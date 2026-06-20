
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
            dt = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            dt_local = dt + datetime.timedelta(hours=7)
            return dt_local.strftime("%d/%m/%Y %H:%M")
        except:
            return dt_str
    return ""

class CourtManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản lý Sân cầu lông")
        self.root.geometry("1400x800")
        
                        # --- UI Styling Setup ---
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure global background
        self.root.configure(bg='#F4FDF4')
        
        # Configure default font for all ttk widgets
        default_font = ('Segoe UI', 10)
        
        # Global Light Green & Black Borders styling
        style.configure('.', font=default_font, background='#F4FDF4', foreground='#000000', bordercolor='#000000')
        style.configure('TFrame', background='#F4FDF4')
        style.configure('TNotebook', background='#F4FDF4')
        style.configure('TNotebook.Tab', background='#E8F5E9', padding=[10, 5], bordercolor='#000000')
        style.map('TNotebook.Tab', background=[('selected', '#FFFFFF')], foreground=[('selected', '#28a745')])
        
        style.configure('TLabel', font=default_font, background='#F4FDF4')
        style.configure('TLabelFrame', background='#F4FDF4', bordercolor='#000000')
        style.configure('TLabelframe.Label', background='#F4FDF4', font=('Segoe UI', 10, 'bold'), foreground='#28a745')
        
        # Button styling (Default Blue)
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), background='#007BFF', foreground='#FFFFFF', padding=5, bordercolor='#000000')
        style.map('TButton', background=[('active', '#0056b3')], foreground=[('active', '#FFFFFF')])
        
        # Treeview Styling
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#E8F5E9', foreground='#000000', bordercolor='#000000')
        style.configure('Treeview', rowheight=25, background='#FFFFFF', fieldbackground='#FFFFFF', bordercolor='#000000')
        style.map('Treeview', background=[('selected', '#d4edda')], foreground=[('selected', '#155724')])
        
        # Custom styles for specific elements
        style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'), foreground='#28a745', background='#F4FDF4')
        style.configure('SubHeader.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#28a745', background='#F4FDF4')
        
        # Success Button (Green)
        style.configure('Success.TButton', background='#28a745', foreground='#FFFFFF')
        style.map('Success.TButton', background=[('active', '#218838')])
        
        # Danger Button (Red)
        style.configure('Danger.TButton', background='#dc3545', foreground='#FFFFFF')
        style.map('Danger.TButton', background=[('active', '#c82333')])
        
        # Warning Button (Orange)
        style.configure('Warning.TButton', background='#fd7e14', foreground='#FFFFFF')
        style.map('Warning.TButton', background=[('active', '#e8590c')])
        
        # Info Button (Cyan/Teal)
        style.configure('Info.TButton', background='#17a2b8', foreground='#FFFFFF')
        style.map('Info.TButton', background=[('active', '#138496')])

        style.configure('StatusFree.TLabel', foreground='#28a745', background='#F4FDF4')
        style.configure('StatusBusy.TLabel', foreground='#dc3545', background='#F4FDF4')
        style.configure('Cost.TLabel', foreground='#fd7e14', font=('Segoe UI', 12, 'bold'), background='#F4FDF4')
        # ------------------------

        self.current_user = None

        self.court_id_map = {}
        self.booking_id_map = {}
        self.notification_id_map = {}
        self.court_image_map = {}
        self.image_cache = {}

        self.selected_court_id = None
        self.selected_date = None
        self.notebook = None

        self.login_frame = ttk.Frame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.build_login_frame()

    # ================== LOGIN / REGISTER ==================
    def build_login_frame(self):
        for widget in self.login_frame.winfo_children():
            widget.destroy()
            
        # Center card
        card = ttk.Frame(self.login_frame, padding=40)
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ttk.Label(card, text="🏸 Quản lý Sân cầu lông", style="Header.TLabel").pack(pady=(0, 20))
        
        ttk.Label(card, text="Tên đăng nhập:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.entry_username = ttk.Entry(card, width=35, font=("Segoe UI", 11))
        self.entry_username.pack(pady=(5, 15))
        
        ttk.Label(card, text="Mật khẩu:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.entry_password = ttk.Entry(card, show="*", width=35, font=("Segoe UI", 11))
        self.entry_password.pack(pady=(5, 20))
        
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Đăng nhập", style="Success.TButton", command=self.do_login).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="Đăng ký", style="Info.TButton", command=self.show_register).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def show_register(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Đăng ký thành viên")
        reg_win.geometry("450x550")
        
        card = ttk.Frame(reg_win, padding=30)
        card.pack(expand=True, fill=tk.BOTH)
        
        ttk.Label(card, text="TẠO TÀI KHOẢN", style="Header.TLabel").pack(pady=(0, 20))

        ttk.Label(card, text="Tên đăng nhập:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        entry_user = ttk.Entry(card, width=40, font=("Segoe UI", 11))
        entry_user.pack(pady=(5, 15))

        ttk.Label(card, text="Mật khẩu:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        entry_pass = ttk.Entry(card, show="*", width=40, font=("Segoe UI", 11))
        entry_pass.pack(pady=(5, 15))

        ttk.Label(card, text="Số điện thoại:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        entry_phone = ttk.Entry(card, width=40, font=("Segoe UI", 11))
        entry_phone.pack(pady=(5, 15))

        ttk.Label(card, text="Vai trò:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        role_var = tk.StringVar(value="CUSTOMER")
        ttk.Combobox(card, textvariable=role_var, values=["CUSTOMER", "COURT_MANAGER"], font=("Segoe UI", 11), state="readonly").pack(pady=(5, 25), fill=tk.X)

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

        ttk.Button(card, text="Đăng ký ngay", style="Success.TButton", command=do_register).pack(fill=tk.X, pady=10)

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
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=5, padx=10)
        ttk.Label(toolbar, text=f"👤 {self.current_user['username']} ({self.current_user['role']})").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Đăng xuất", command=self.logout).pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.tab_courts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_courts, text="🏸 Sân")
        self.build_courts_tab()

        self.tab_my_bookings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_my_bookings, text="📋 Lịch của tôi")
        self.build_my_bookings_tab()

        if self.current_user['role'] in ('MANAGER', 'COURT_MANAGER'):
            self.tab_manage = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_manage, text="⚙️ Quản lý")
            self.build_manage_tab()

            self.tab_stats = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_stats, text="📊 Thống kê")
            self.build_stats_tab()



        self.load_courts()

    # ================== TAB 1: SÂN ==================
    def build_courts_tab(self):
        # Vertical split: Top = List, Bottom = Details + Booking
        main_pane = ttk.PanedWindow(self.tab_courts, orient='vertical')
        main_pane.pack(fill='both', expand=True, padx=10, pady=10)

        # TOP FRAME (Filter + Treeview)
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=1)

        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(fill='x', pady=5)
        ttk.Label(filter_frame, text="Mặt sân:").pack(side='left', padx=2)
        self.filter_surface = ttk.Combobox(filter_frame, values=["", "PVC", "WOOD", "CEMENT", "SYNTHETIC_RESIN"], width=12)
        self.filter_surface.pack(side='left', padx=2)
        ttk.Label(filter_frame, text="Kích thước:").pack(side='left', padx=2)
        self.filter_size = ttk.Combobox(filter_frame, values=["", "SINGLE", "DOUBLE"], width=8)
        self.filter_size.pack(side='left', padx=2)
        ttk.Button(filter_frame, text="Lọc", style="Info.TButton", command=self.load_courts).pack(side='left', padx=10)

        tree_frame = ttk.Frame(top_frame)
        tree_frame.pack(fill='both', expand=True)
        self.tree_courts = ttk.Treeview(tree_frame, columns=("id", "name", "address", "surface", "size", "price"), show="headings", height=5)
        self.tree_courts.heading("id", text="ID")
        self.tree_courts.heading("name", text="Tên sân")
        self.tree_courts.heading("address", text="Địa chỉ")
        self.tree_courts.heading("surface", text="Mặt sân")
        self.tree_courts.heading("size", text="Kích thước")
        self.tree_courts.heading("price", text="Giá/h")
        self.tree_courts.column("id", width=80)
        self.tree_courts.column("name", width=200)
        self.tree_courts.column("address", width=300)
        self.tree_courts.column("surface", width=150)
        self.tree_courts.column("size", width=100)
        self.tree_courts.column("price", width=100)
        scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_courts.yview)
        self.tree_courts.configure(yscrollcommand=scrollbar_y.set)
        self.tree_courts.pack(side='left', fill='both', expand=True)
        scrollbar_y.pack(side='right', fill='y')
        self.tree_courts.bind("<<TreeviewSelect>>", self.on_court_selected)

        # BOTTOM FRAME (Left: Details, Right: Booking)
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=1)

        # Left split for details
        detail_frame = ttk.Frame(bottom_frame)
        detail_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        self.court_image_label = tk.Label(detail_frame, text="Chọn sân để xem ảnh", bg="#E8F5E9", font=("Segoe UI", 10))
        self.court_image_label.pack(side='left', padx=5, pady=5)

        info_frame = ttk.Frame(detail_frame)
        info_frame.pack(side='left', fill='both', expand=True, padx=10)
        self.court_name_label = ttk.Label(info_frame, text="Tên: ", font=("Segoe UI", 12, "bold"))
        self.court_name_label.pack(anchor='w', pady=2)
        self.court_address_label = ttk.Label(info_frame, text="Địa chỉ: ")
        self.court_address_label.pack(anchor='w', pady=2)
        self.court_surface_label = ttk.Label(info_frame, text="Mặt: ")
        self.court_surface_label.pack(anchor='w', pady=2)
        self.court_size_label = ttk.Label(info_frame, text="Kích thước: ")
        self.court_size_label.pack(anchor='w', pady=2)
        self.court_price_label = ttk.Label(info_frame, text="Giá/h: ")
        self.court_price_label.pack(anchor='w', pady=2)
        self.court_owner_phone_label = ttk.Label(info_frame, text="SĐT chủ sân: ")
        self.court_owner_phone_label.pack(anchor='w', pady=2)
        self.court_free_label = ttk.Label(info_frame, text="Trạng thái: ")
        self.court_free_label.pack(anchor='w', pady=2)

        # Right split for booking
        booking_pane = ttk.Frame(bottom_frame)
        booking_pane.pack(side='left', fill='both', expand=True)

        ttk.Label(booking_pane, text="Lịch sân trong ngày:", font=("Segoe UI", 10, "bold")).pack(anchor='w', pady=(5,0))
        date_frame = ttk.Frame(booking_pane)
        date_frame.pack(anchor='w', pady=2)
        ttk.Label(date_frame, text="Ngày (DD/MM/YYYY):").pack(side='left')
        self.entry_date = ttk.Entry(date_frame, width=12)
        self.entry_date.pack(side='left', padx=5)
        self.entry_date.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))
        ttk.Button(date_frame, text="Xem lịch", style="Info.TButton", command=self.load_court_schedule).pack(side='left', padx=5)

        self.schedule_tree = ttk.Treeview(booking_pane, columns=("start", "end", "status"), show="headings", height=3)
        self.schedule_tree.heading("start", text="Bắt đầu")
        self.schedule_tree.heading("end", text="Kết thúc")
        self.schedule_tree.heading("status", text="Trạng thái")
        self.schedule_tree.pack(fill='x', pady=5)

        book_frame = ttk.LabelFrame(booking_pane, text="Đặt sân", padding=5)
        book_frame.pack(fill='x', pady=(5, 20), padx=5)

        ttk.Label(book_frame, text="Bắt đầu:").grid(row=0, column=0, sticky='w', padx=2, pady=2)
        self.start_hour = ttk.Combobox(book_frame, values=[f"{i:02d}" for i in range(24)], width=3)
        self.start_hour.grid(row=0, column=1, padx=1, pady=2)
        self.start_hour.set("08")
        ttk.Label(book_frame, text=":").grid(row=0, column=2)
        self.start_minute = ttk.Combobox(book_frame, values=["00", "15", "30", "45"], width=3)
        self.start_minute.grid(row=0, column=3, padx=1, pady=2)
        self.start_minute.set("00")

        ttk.Label(book_frame, text="Kết thúc:").grid(row=0, column=4, sticky='w', padx=(5,2), pady=2)
        self.end_hour = ttk.Combobox(book_frame, values=[f"{i:02d}" for i in range(24)], width=3)
        self.end_hour.grid(row=0, column=5, padx=1, pady=2)
        self.end_hour.set("09")
        ttk.Label(book_frame, text=":").grid(row=0, column=6)
        self.end_minute = ttk.Combobox(book_frame, values=["00", "15", "30", "45"], width=3)
        self.end_minute.grid(row=0, column=7, padx=1, pady=2)
        self.end_minute.set("00")

        ttk.Label(book_frame, text="Chi phí:").grid(row=0, column=8, sticky='w', padx=(10, 2), pady=2)
        self.label_cost = ttk.Label(book_frame, text="0 VND", style="Cost.TLabel")
        self.label_cost.grid(row=0, column=9, sticky='w', padx=2)

        ttk.Button(book_frame, text="Tính tiền", style="Warning.TButton", command=self.calculate_cost).grid(row=0, column=10, padx=(10, 5), pady=8)
        ttk.Button(book_frame, text="Đặt sân", style="Success.TButton", command=self.book_court).grid(row=0, column=11, padx=5, pady=8)

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
                            self.court_free_label.config(text="Trạng thái: Trống", style="StatusFree.TLabel")
                        else:
                            self.court_free_label.config(text="Trạng thái: Đang có booking", style="StatusBusy.TLabel")
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
            img = img.resize((250, 250))
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
        frame = ttk.Frame(self.tab_my_bookings)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree_my_bookings = ttk.Treeview(frame, columns=("id", "court", "start", "end", "status", "cost"), show="headings")
        self.tree_my_bookings.heading("id", text="ID")
        self.tree_my_bookings.heading("court", text="Sân")
        self.tree_my_bookings.heading("start", text="Bắt đầu")
        self.tree_my_bookings.heading("end", text="Kết thúc")
        self.tree_my_bookings.heading("status", text="Trạng thái")
        self.tree_my_bookings.heading("cost", text="Chi phí")
        
        self.tree_my_bookings.column("id", width=100)
        self.tree_my_bookings.column("court", width=200)
        self.tree_my_bookings.column("start", width=200)
        self.tree_my_bookings.column("end", width=200)
        self.tree_my_bookings.column("status", width=150)
        self.tree_my_bookings.column("cost", width=150)
        
        self.tree_my_bookings.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Hủy đặt", style="Danger.TButton", command=self.cancel_my_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Làm mới", style="Info.TButton", command=self.load_my_bookings).pack(side=tk.LEFT)

        self.load_my_bookings()

    def load_my_bookings(self):
        def fetch():
            res = db_service.search_bookings(user_id=self.current_user['user_id'])
            if "error" in res:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", res["error"]))
            else:
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

        self.tab_manage_courts = ttk.Frame(manage_notebook)
        manage_notebook.add(self.tab_manage_courts, text="Sân")
        self.build_manage_courts()

        self.tab_manage_bookings = ttk.Frame(manage_notebook)
        manage_notebook.add(self.tab_manage_bookings, text="Booking")
        self.build_manage_bookings()

    # ---- Quản lý sân ----
    def build_manage_courts(self):
        frame = ttk.Frame(self.tab_manage_courts)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = ttk.LabelFrame(frame, text="Thêm sân mới", padding=5)
        form_frame.pack(fill=tk.X, pady=5)

        # Configure column weights for a neat, responsive grid layout
        form_frame.columnconfigure(1, weight=1, minsize=150)
        form_frame.columnconfigure(3, weight=2, minsize=150)

        # Row 0
        ttk.Label(form_frame, text="Tên sân:").grid(row=0, column=0, sticky='e', padx=(10, 5), pady=8)
        self.entry_court_name = ttk.Entry(form_frame)
        self.entry_court_name.grid(row=0, column=1, sticky='ew', padx=5, pady=8)

        ttk.Label(form_frame, text="Địa chỉ:").grid(row=0, column=2, sticky='e', padx=(20, 5), pady=8)
        self.entry_address = ttk.Entry(form_frame)
        self.entry_address.grid(row=0, column=3, sticky='ew', padx=5, pady=8)

        # Row 1
        ttk.Label(form_frame, text="Mặt sân:").grid(row=1, column=0, sticky='e', padx=(10, 5), pady=8)
        self.combo_surface = ttk.Combobox(form_frame, values=["PVC", "WOOD", "CEMENT", "SYNTHETIC_RESIN"])
        self.combo_surface.grid(row=1, column=1, sticky='ew', padx=5, pady=8)

        ttk.Label(form_frame, text="Kích thước:").grid(row=1, column=2, sticky='e', padx=(20, 5), pady=8)
        self.combo_size = ttk.Combobox(form_frame, values=["SINGLE", "DOUBLE"])
        self.combo_size.grid(row=1, column=3, sticky='ew', padx=5, pady=8)

        # Row 2
        ttk.Label(form_frame, text="Giá/1h (VND):").grid(row=2, column=0, sticky='e', padx=(10, 5), pady=8)
        self.entry_price_hour = ttk.Entry(form_frame)
        self.entry_price_hour.grid(row=2, column=1, sticky='ew', padx=5, pady=8)

        ttk.Label(form_frame, text="Giá/3h (VND):").grid(row=2, column=2, sticky='e', padx=(20, 5), pady=8)
        self.entry_price_3h = ttk.Entry(form_frame)
        self.entry_price_3h.grid(row=2, column=3, sticky='ew', padx=5, pady=8)

        # Row 3
        ttk.Label(form_frame, text="Ảnh sân:").grid(row=3, column=0, sticky='e', padx=(10, 5), pady=8)
        
        img_frame = ttk.Frame(form_frame)
        img_frame.grid(row=3, column=1, columnspan=3, sticky='ew', padx=5, pady=8)
        img_frame.columnconfigure(0, weight=1)
        
        self.entry_image_path = ttk.Entry(img_frame)
        self.entry_image_path.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ttk.Button(img_frame, text="Chọn ảnh", command=self.choose_image).grid(row=0, column=1)

        # Row 4 (Button)
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=15)
        ttk.Button(btn_frame, text="Thêm sân", style="Success.TButton", command=self.add_court).pack(side='left', padx=5)

        list_frame = ttk.LabelFrame(frame, text="Danh sách sân hiện có", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.tree_manage_courts = ttk.Treeview(list_frame, columns=("id", "name", "address", "surface", "size", "price", "active"), show="headings")
        self.tree_manage_courts.heading("id", text="ID")
        self.tree_manage_courts.heading("name", text="Tên")
        self.tree_manage_courts.heading("address", text="Địa chỉ")
        self.tree_manage_courts.heading("surface", text="Mặt")
        self.tree_manage_courts.heading("size", text="Kích thước")
        self.tree_manage_courts.heading("price", text="Giá/h")
        self.tree_manage_courts.heading("active", text="Hoạt động")
        btn_manage = ttk.Frame(list_frame)
        btn_manage.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Button(btn_manage, text="Xóa (ngừng hoạt động)", style="Danger.TButton", command=self.delete_court).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_manage, text="Làm mới", style="Info.TButton", command=self.load_manage_courts).pack(side=tk.LEFT)

        self.tree_manage_courts.pack(fill=tk.BOTH, expand=True)

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
        frame = ttk.Frame(self.tab_manage_bookings)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filter_frame, text="Trạng thái:").pack(side=tk.LEFT)
        self.filter_booking_status = ttk.Combobox(filter_frame, values=["", "PENDING", "BOOKED", "COMPLETED", "CANCELLED", "REJECTED"], width=12)
        self.filter_booking_status.pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Lọc", style="Info.TButton", command=self.load_manage_bookings).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Làm mới", style="Info.TButton", command=self.load_manage_bookings).pack(side=tk.LEFT)

        self.tree_manage_bookings = ttk.Treeview(frame, columns=("id", "user", "court", "start", "end", "status", "cost"), show="headings")
        self.tree_manage_bookings.heading("id", text="ID")
        self.tree_manage_bookings.heading("user", text="Người đặt")
        self.tree_manage_bookings.heading("court", text="Sân")
        self.tree_manage_bookings.heading("start", text="Bắt đầu")
        self.tree_manage_bookings.heading("end", text="Kết thúc")
        self.tree_manage_bookings.heading("status", text="Trạng thái")
        self.tree_manage_bookings.heading("cost", text="Chi phí")
        
        self.tree_manage_bookings.column("id", width=100)
        self.tree_manage_bookings.column("user", width=150)
        self.tree_manage_bookings.column("court", width=150)
        self.tree_manage_bookings.column("start", width=180)
        self.tree_manage_bookings.column("end", width=180)
        self.tree_manage_bookings.column("status", width=150)
        self.tree_manage_bookings.column("cost", width=120)
        
        self.tree_manage_bookings.pack(fill=tk.BOTH, expand=True)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_frame, text="Duyệt", style="Success.TButton", command=self.approve_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Từ chối", style="Danger.TButton", command=self.reject_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Hoàn thành", command=self.complete_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Hủy", style="Danger.TButton", command=self.cancel_booking_admin).pack(side=tk.LEFT, padx=5)

        self.load_manage_bookings()

    def load_manage_bookings(self):
        def fetch():
            status = self.filter_booking_status.get() if self.filter_booking_status.get() else None
            owner_id = None
            if self.current_user['role'] == 'COURT_MANAGER':
                owner_id = self.current_user['user_id']
            res = db_service.search_bookings(status=status, owner_id=owner_id)
            if "error" in res:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", res["error"]))
            else:
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
        frame = ttk.Frame(self.tab_stats)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="DOANH THU THEO NGÀY", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
        self.tree_stats_revenue = ttk.Treeview(frame, columns=("date", "revenue"), show="headings", height=6)
        self.tree_stats_revenue.heading("date", text="Ngày")
        self.tree_stats_revenue.heading("revenue", text="Doanh thu (VND)")
        self.tree_stats_revenue.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="TOP SÂN ĐƯỢC ĐẶT NHIỀU NHẤT", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.tree_stats_top = ttk.Treeview(frame, columns=("court", "address", "owner_phone", "count"), show="headings", height=6)
        self.tree_stats_top.heading("court", text="Tên sân")
        self.tree_stats_top.heading("address", text="Địa chỉ")
        self.tree_stats_top.heading("owner_phone", text="SĐT chủ sân")
        self.tree_stats_top.heading("count", text="Số lần đặt")
        self.tree_stats_top.pack(fill=tk.X, pady=5)

        btn_stats = ttk.Frame(frame)
        btn_stats.pack(fill=tk.X, pady=10)
        ttk.Button(btn_stats, text="Làm mới", style="Info.TButton", command=self.load_stats).pack(side=tk.LEFT)

        self.load_stats()

    def load_stats(self):
        def fetch():
            owner_id = None
            if self.current_user['role'] == 'COURT_MANAGER':
                owner_id = self.current_user['user_id']
            rev_res = db_service.get_daily_revenue(owner_id=owner_id)
            top_res = db_service.get_top_courts(5, owner_id=owner_id)
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
        frame = ttk.Frame(self.tab_notifications)
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

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Làm mới", style="Info.TButton", command=self.load_notifications).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Đánh dấu đã đọc", command=self.mark_read).pack(side=tk.LEFT)

        self.load_notifications()

    def load_notifications(self):
        def fetch():
            res = db_service.get_notifications(self.current_user['user_id'])
            if "error" in res:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", res["error"]))
            else:
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
        self.login_frame = ttk.Frame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.build_login_frame()

if __name__ == "__main__":
    root = tk.Tk()
    app = CourtManagerApp(root)
    root.mainloop()