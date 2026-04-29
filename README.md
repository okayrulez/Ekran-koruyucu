# Catchmebro: Honeypot & AntiGravity Güvenlik Sistemi

Bu proje, bilgisayara yetkisiz fiziksel erişimi ve zararlı USB cihazlarının (BadUSB) takılmasını engellemek için tasarlanmış, sessiz çalışan bir "Honeypot" (Bal Küpü) ve güvenlik kalkanıdır.

## Özellikler

- **Hayalet Modu (Stealth Mode):** 
  Program çalıştığında ekranda hiçbir pencere açılmaz. Sağ alt köşedeki (system tray) simge tepsisinde gizlice bekler. Kapatıp açma işlemleri özel klavye kısayoluyla yapılır.

- **Hareket Algılama ve Gizli Çekim:**
  Tuzak aktif edildiğinde, bilgisayara dokunan kişinin yaptığı en ufak bir fare veya klavye hareketinde sistem sessizce web kamerasından fotoğraf çeker ve kaydeder.

- **Otomatik İşletim Sistemi Kilidi:**
  Sistem art arda 5 hareket algılayıp 5 fotoğraf çektikten sonra, bilgisayarı otomatik olarak uyku moduna / kilit ekranına (Win + L) alır.

- **Donanım Dondurma (Hardware Suppress):**
  Tuzak devredeyken ekrandaki fare imleci tamamen dondurulur. Bilgisayarı kurcalayan kişi fareyi fiziksel olarak hareket ettirse bile imleç kıpırdamaz, hiçbir yere tıklayamaz (ancak program arka planda bu hareketi algılayıp fotoğraflarını çekmeye devam eder).

- **AntiGravity Protokolü (USB Engelleyici):**
  Program aktif edildiğinde Windows kayıt defterine (Registry) müdahale ederek aşağıdaki güvenlik kalkanlarını devreye sokar:
  1. **USB Depolama Engeli:** Harici disk veya Flash bellek takıldığında sistem okumaz. Veri hırsızlığını engeller.
  2. **Yeni Cihaz Engeli:** Sisteme daha önce hiç takılmamış yeni bir cihaz takıldığında (Örn: Klavye gibi davranan bir BadUSB) Windows'un sürücü kurmasını ve cihazı çalıştırmasını engeller.
  *(Not: Tuzak kapatıldığında bu ayarlar otomatik olarak normale döndürülür.)*

- **Otomatik Yönetici (Admin) Yetkisi:**
  Program, Registry kayıtlarını değiştirebilmek için her açıldığında arka planda otomatik olarak "Yönetici Olarak Çalıştır" izinlerini kontrol eder ve yetkiyi alır.

## Kısayollar ve Kullanım

- **Sistemi Açma:** Program başlatıldıktan sonra bilgisayarı kilitlerken `Ctrl + Q` tuşlarına bastığınızda tuzak aktif olur (Tepsi simgesi yeşile döner).
- **Sistemi Kapatma:** Gizli kapatma kısayolu olan `F12` tuşuna basıldığında sistem devre dışı kalır, fare kilidi açılır ve USB'ler tekrar kullanıma sunulur.

## Dosya Yolları
- **Çekilen Fotoğraflar:** Masaüstündeki `Honeypot_Yakalananlar` klasörüne tarih ve saat damgasıyla kaydedilir.
