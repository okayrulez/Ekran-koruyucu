; Scriptin Yönetici (Admin) haklarıyla çalışmasını zorunlu kılıyoruz. 
; (Registry değiştirmek için şarttır)
if not A_IsAdmin
{
   Run *RunAs "%A_ScriptFullPath%"
   ExitApp
}

; Gizli Tuş Kombinasyonu: Ctrl + Alt + Shift + U
^!+u::
    ToggleAntiGravity()
return

ToggleAntiGravity() {
    ; USB Depolama Durumunu Oku
    RegRead, UsbStatus, HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\USBSTOR, Start
    
    if (UsbStatus == 3) { 
        ; --- ANTİGRAVİTY MODU AKTİF ---
        ; 1. USB Depolamayı Kapat (Değeri 4 yap)
        RegWrite, REG_DWORD, HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\USBSTOR, Start, 4
        
        ; 2. Yeni Cihaz (BadUSB/Klavye vb.) Kurulumunu Engelle
        RegWrite, REG_DWORD, HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions, DenyUnspecified, 1
        
        ; Ekranda 2 saniyelik ufak bir uyarı göster (Bunu silersen tamamen hayalet modunda çalışır)
        TrayTip, AntiGravity Protokolü, TUZAK AKTİF: Tüm yeni USB'ler ve Depolama engellendi., 2
    } else { 
        ; --- ANTİGRAVİTY MODU KAPALI ---
        ; 1. USB Depolamayı Aç (Değeri 3 yap)
        RegWrite, REG_DWORD, HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\USBSTOR, Start, 3
        
        ; 2. Yeni Cihaz Kurulumu Engelini Kaldır
        RegWrite, REG_DWORD, HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions, DenyUnspecified, 0
        
        TrayTip, AntiGravity Protokolü, NORMALE DÖNÜLDÜ: USB erişimi açıldı., 2
    }
}