import cv2
from pynput import mouse, keyboard
import time
from datetime import datetime
import os
import ctypes
import winreg
import tkinter as tk
from tkinter import scrolledtext
import threading
from PIL import Image, ImageTk, ImageDraw, ImageFont
from screeninfo import get_monitors

try:
    import pystray
    from pystray import MenuItem as TrayItem
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

def get_desktop_path():
    """Windows için en güvenilir Masaüstü (Desktop) yolunu bulur."""
    try:
        # Registry üzerinden güncel lokasyonu çek (OneDrive dahil doğru bulur)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        return winreg.QueryValueEx(key, "Desktop")[0]
    except Exception:
        return os.path.join(os.path.expanduser("~"), "Desktop")

class FullscreenViewer:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.withdraw() # Başlangıçta gizli
        self.window.overrideredirect(True) # Pencere çubuğunu gizle
        
        # En soldaki monitörü tespit et
        try:
            monitors = get_monitors()
            monitors.sort(key=lambda m: m.x)
            left_monitor = monitors[0]
            self.mon_width = left_monitor.width
            self.mon_height = left_monitor.height
            self.window.geometry(f"{self.mon_width}x{self.mon_height}+{left_monitor.x}+{left_monitor.y}")
        except Exception as e:
            # Yedek plan (İlk ekran)
            self.mon_width = parent.winfo_screenwidth()
            self.mon_height = parent.winfo_screenheight()
            self.window.attributes("-fullscreen", True)

        self.window.attributes("-topmost", True)
        self.window.configure(bg='black')
        
        self.label = tk.Label(self.window, bg='black')
        self.label.pack(expand=True, fill=tk.BOTH)
        
        self.photo_image = None
        self.is_visible = False
        self.hide_timer = None

    def show_image(self, bgr_frame):
        # BGR'den RGB'ye çevir ve Pillow resmi oluştur
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        
        # Kırmızı "İZİNSİZ GİRİŞ" yazısı ekle
        draw = ImageDraw.Draw(pil_img)
        try:
            # Arial Black, Impact, veya standart bir font
            font = ImageFont.truetype("arialbd.ttf", 60) 
        except IOError:
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except IOError:
                font = ImageFont.load_default()
                
        lines = ["YAKALANDIN!", "İZİNSİZ GİRİŞ!"]
        current_y = 50
        
        for line_text in lines:
            text_bbox = draw.textbbox((0, 0), line_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            # Fontun yüksekliği
            text_height = text_bbox[3] - text_bbox[1]
            
            # Ortala
            x = (pil_img.width - text_width) // 2
            y = current_y
            
            # Yazı çok belirgin olsun diye siyah çerçeve
            outline_color = "black"
            for adj_x, adj_y in [(-2,-2), (2,-2), (-2,2), (2,2)]:
                draw.text((x + adj_x, y + adj_y), line_text, font=font, fill=outline_color)
            
            draw.text((x, y), line_text, font=font, fill="red")
            
            # Sonraki satır için aşağı kaydır
            current_y += text_height + 20
        
        # Ekrana Orantılama (Aspect Ratio)
        img_ratio = pil_img.width / pil_img.height
        mon_ratio = self.mon_width / self.mon_height
        
        if img_ratio > mon_ratio: # Resim ekrandan daha geniş (Genişlik bazlı uydur)
            new_w = self.mon_width
            new_h = int(new_w / img_ratio)
        else: # Resim ekrandan daha dar/uzun (Yükseklik bazlı uydur)
            new_h = self.mon_height
            new_w = int(new_h * img_ratio)
            
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Tkinter formatına dönüştür
        self.photo_image = ImageTk.PhotoImage(pil_img)
        self.label.config(image=self.photo_image)
        
        # Eğer daha önce gizliyse görünür yap
        if not self.is_visible:
            self.window.deiconify()
            self.is_visible = True

        # 10 saniye sonra kapanması için zamanlayıcıyı ayarla
        if self.hide_timer is not None:
            self.window.after_cancel(self.hide_timer)
        self.hide_timer = self.window.after(10000, self.hide)

    def hide(self):
        # Pencereyi gizle
        self.window.withdraw()
        self.is_visible = False
        if self.hide_timer is not None:
            self.window.after_cancel(self.hide_timer)
            self.hide_timer = None


class HoneypotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Honeypot Güvenlik Sistemi")
        self.root.geometry("570x450")
        self.root.resizable(False, False)

        # Temel Değişkenler
        self.is_active = False
        self.cap = None
        self.last_capture_time = 0
        self.cooldown_seconds = 1  # 1 Saniyeye düşürüldü. Çok hareket edilirse donmaması/taşmaması için
        self.camera_port = 0
        self.secret_exit_key = keyboard.Key.f12
        self.capture_lock = threading.Lock()
        self.capture_count = 0
        
        # Dinleyiciler
        self.mouse_listener = None
        self.keyboard_listener = None

        # Gelişmiş Tam Ekran Görüntüleyici Sınıfı
        self.viewer = FullscreenViewer(self.root)

        # Düzenlenmiş Masaüstü Yolu Bulma Sistemi
        desktop_path = get_desktop_path()
        self.save_folder = os.path.join(desktop_path, "Honeypot_Yakalananlar")
        if not os.path.exists(self.save_folder):
            try:
                os.makedirs(self.save_folder)
            except Exception as e:
                print(f"[!] Klasör oluşturulamadı: {e}")

        # UI Tasarımı
        self.create_widgets()
        
        # HAYALET MOD: Arayüz oluşturulur ancak ekranda ASLA gösterilmez. Arka planda pusuya yatar.
        self.root.withdraw()

        # GLOBAL KISAYOL: Herhangi bir zamanda 'Ctrl + Q' tuşlarına basılırsa sistemi başlatır.
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+q': self.on_hotkey_activate
        })
        self.hotkey_listener.start()
        
        # İlk log mesajları
        self.log_message("[*] Uygulama Başlatıldı. Hayalet moda (Gizli) geçildi.")
        self.log_message(f"[*] Kayıt Dizini: {self.save_folder}")
        self.log_message("[*] Sistem 'Ctrl + Q' kısayoluna basılmasını bekliyor...")
        
        # Tray(Sistem Tepsisi) simgesini başlat
        self.setup_tray()

    def create_widgets(self):
        title_label = tk.Label(self.root, text="HONEYPOT TUZAK SİSTEMİ", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        self.status_label = tk.Label(self.root, text="DURUM: PASİF", fg="red", font=("Helvetica", 14, "bold"))
        self.status_label.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        self.btn_start = tk.Button(btn_frame, text="Sistemi Aktif Et", command=self.start_system, 
                                   width=15, height=2, bg="#d4edda", fg="black", font=("Helvetica", 10, "bold"))
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="Sistemi Durdur", command=self.stop_system, state=tk.DISABLED, 
                                  width=15, height=2, bg="#f8d7da", fg="black", font=("Helvetica", 10, "bold"))
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        log_label = tk.Label(self.root, text="Hareket Kayıtları:", font=("Helvetica", 10, "bold"))
        log_label.pack(anchor=tk.W, padx=25, pady=(5, 0))

        self.log_area = scrolledtext.ScrolledText(self.root, width=65, height=12, state='disabled', font=("Consolas", 9))
        self.log_area.pack(pady=5)

    def setup_tray(self):
        if not HAS_PYSTRAY:
            self.log_message("[!] pystray kütüphanesi eksik. Sağ alt köşe simgesi oluşturulamadı.")
            self.log_message("[!] Yüklemek için komut satırında şunu çalıştırın: pip install pystray")
            return

        def create_icon_image(color):
            image = Image.new('RGB', (64, 64), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle((16, 16, 48, 48), fill="white")
            draw.ellipse((24, 24, 40, 40), fill=color)
            return image

        def on_open_ui(icon, item):
            self.root.after(0, lambda: [self.root.deiconify(), self.root.lift()])

        def on_toggle_active(icon, item):
            if self.is_active:
                self.root.after(0, self.stop_system)
            else:
                self.root.after(0, self.start_system)

        def on_exit(icon, item):
            self.root.after(0, self.real_quit)

        menu = pystray.Menu(
            TrayItem("Arayüzü Göster", on_open_ui),
            TrayItem(lambda item: "Sistemi Durdur" if self.is_active else "Sistemi Başlat", on_toggle_active),
            TrayItem("Tamamen Çıkış", on_exit)
        )

        self.tray_icon = pystray.Icon("Honeypot", create_icon_image("red"), "Honeypot", menu=menu)
        
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def update_tray_icon(self):
        if hasattr(self, 'tray_icon') and getattr(self, 'tray_icon'):
            color = "green" if self.is_active else "red"
            def create_icon_image(c):
                img = Image.new('RGB', (64, 64), c)
                dr = ImageDraw.Draw(img)
                dr.rectangle((16, 16, 48, 48), fill="white")
                dr.ellipse((24, 24, 40, 40), fill=c)
                return img
            self.tray_icon.icon = create_icon_image(color)

    def log_message(self, message):
        self.root.after(0, self._insert_log, message)

    def _insert_log(self, message):
        self.log_area.config(state='normal')
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{time_str}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def on_hotkey_activate(self):
        # Ctrl+Q basıldığında start_system'i UI thread üzerinden tetikler
        self.root.after(0, self.start_system)

    def capture_photo(self):
        with self.capture_lock:
            current_time = time.time()
            
            # Non-stop çekim için bekleme süresi sadece 1 saniye. (Harekete devam ettiği sürece saniyede 1 fotoğraf!)
            if current_time - self.last_capture_time < self.cooldown_seconds:
                return

            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"yakalandin_{timestamp}.jpg"
                    filepath = os.path.join(self.save_folder, filename)
                    
                    # Fotoğrafı kaydet
                    cv2.imwrite(filepath, frame)
                    self.log_message(f"[!] HAREKET ALGILANDI! Kaydedildi: {filename}")
                    
                    # Güvenli Pencere Güncellemesi Anakol Thread'e atılarak Sol Ekranda yenilenir
                    self.root.after(0, self.viewer.show_image, frame)

                    self.last_capture_time = current_time
                    self.capture_count += 1
                    
                    if self.capture_count >= 5 and self.is_active:
                        self.log_message("[*] 5 fotoğraf çekildi, BİLGİSAYAR KİLİTLENİYOR!")
                        # Windows'u kilitle (Win + L tuşuna basılmış gibi)
                        ctypes.windll.user32.LockWorkStation()
                        self.capture_count = 0
                else:
                    self.log_message("[Hata] Kameradan görüntü okunamadı!")

    # --- DINLEYICI FONKSİYONLARI ---
    def on_move(self, x, y):
        if self.is_active:
            self.capture_photo()

    def on_click(self, x, y, button, pressed):
        if self.is_active and pressed:
            self.capture_photo()

    def on_scroll(self, x, y, dx, dy):
        if self.is_active:
            self.capture_photo()

    def on_press(self, key):
        if key == self.secret_exit_key:
            self.log_message("\n[*] Gizli kapatma tuşu (F12) algılandı.")
            self.root.after(0, self.stop_system)
            return False 
        
        if self.is_active:
            self.capture_photo()

    def start_system(self):
        if self.is_active: return

        self.log_message("[*] Kamera modülü yükleniyor, lütfen bekleyin...")
        self.root.update()
        
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_port)
            if not self.cap.isOpened():
                self.log_message("[HATA] Kameraya erişilemedi! Kabloları kontrol edin.")
                return
            time.sleep(1.5)

        self.is_active = True
        self.capture_count = 0
        self.status_label.config(text="DURUM: AKTİF", fg="green")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        if hasattr(self, 'update_tray_icon'):
            self.update_tray_icon()
            
        self.log_message("[*] SİSTEM AKTİF. İzinsiz girişlere karşı dinleniyor...")

        # Fare ve klavye dinleyicilerini başlat
        self.mouse_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        # Ekranın uykuya dalmasını engelle
        self.prevent_sleep(True)

    def stop_system(self):
        if not self.is_active: return

        self.is_active = False
        self.status_label.config(text="DURUM: PASİF", fg="red")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

        if hasattr(self, 'update_tray_icon'):
            self.update_tray_icon()

        self.log_message("[*] Sistem deaktif ediliyor...")

        # Acılan yakalama penceresini kapat
        self.viewer.hide()

        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except: pass
        
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except: pass

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Uyku engelini kaldır ki bilgisayar normal haline dönsün
        self.prevent_sleep(False)

        self.log_message("[*] Sistem başarıyla durduruldu ve tekrar pusuya (Ctrl+Q) geçti.")

    def hide_ui(self):
        # Arayüzü gizle, arka planda çalışmaya devam etsin
        self.root.withdraw()
        if HAS_PYSTRAY:
            self.log_message("[*] Arayüz gizlendi, sistem simge tepsisinde (sağ alt) çalışmaya devam ediyor.")

    def real_quit(self):
        # Uygulamayı tamamen sonlandır
        if self.is_active:
            self.stop_system()
        if hasattr(self, 'tray_icon') and getattr(self, 'tray_icon', None):
            self.tray_icon.stop()
        self.root.destroy()

    def put_pc_to_sleep(self):
        """Sistemi durdurur ve bilgisayarı uyku moduna (Suspend) alır."""
        # Sistemi ve pynput kancalarını durdur
        self.stop_system()
        
        # pynput arka plan listener thread'lerinin tamamen kapanıp farenin hook'larını 
        # işletim sistemine geri vermesi için 1.5 saniye bekle, sonra komutu çalıştır.
        def do_sleep():
            try:
                self.log_message("[*] Windows uyku moduna geçiriliyor...")
                # Windows uyku moduna geçiş komutu
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            except Exception as e:
                self.log_message(f"[Hata] PC uykuya alınamadı: {e}")
                
        self.root.after(1500, do_sleep)

    def prevent_sleep(self, prevent=True):
        """Windows API kullanarak sistemin ve ekranın uyku moduna geçmesini engeller."""
        try:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002

            if prevent:
                # Hem sistemin hem ekranın açık kalmasını zorla
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            else:
                # Engeli kaldır
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception as e:
            self.log_message(f"[Uyarı] Ekran uyku engeli ayarlanamadı: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HoneypotApp(root)
    # X tuşuna basıldığında program kapanmasın, gizlensin
    root.protocol("WM_DELETE_WINDOW", app.hide_ui)
    root.mainloop()
