# 🛰️ NetOutageMonitor (Power and Network Outage NetOutageMonitor)

Yerel ağdaki (LAN) bir cihazın aktifliğini sürekli kontrol ederek, elektrik veya ağ kesintilerini otomatik olarak tespit eden ve Windows üzerinde görsel uyarılar oluşturan Python tabanlı bir Windows Servisi.

[![GitHub Profile](https://img.shields.io/badge/GitHub-Awosk-blue?style=flat-square&logo=github)](https://github.com/Awosk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Projenin Amacı

Bilgisayarınız bir Kesintisiz Güç Kaynağına (UPS) bağlıysa ancak UPS'inizin doğrudan bilgisayarla iletişim kurma özelliği (USB veri kablosu veya yazılım desteği) yoksa, elektriğin kesildiğini fark edemeyebilirsiniz. (Benim gibi UPS in buzzerini iptal ettiyseniz...)

Bu araç, şebeke elektriğine doğrudan bağlı (UPS'e bağlı olmayan) yerel bir cihaza (örneğin modem, akıllı priz veya Raspberry Pi) sürekli ping atar. Elektrik kesildiğinde o cihaz kapanacağı için ping başarısız olur ve Windows ekranınızda otomatik bir uyarı penceresi açılır. Böylece bilgisayarınızı güvenle kapatabilirsiniz.

---

## ✨ Özellikler

* ⚙️ **Windows Servisi Olarak Çalışma:** Arka planda görünmez şekilde çalışır, bilgisayar açıldığında otomatik başlar.
* 🔔 **Session 0 Bildirim Köprüsü:** WTS API'sini kullanarak Windows servis izolasyonunu aşar ve doğrudan masaüstünüze uyarı mesajı gönderir.
* 🔄 **Dinamik Yapılandırma:** `config.json` dosyası üzerinden servis durdurulmadan ayarlar değiştirilebilir.
* ⏳ **Cooldown & Delay:** Elektrik gidip uyarısı geldikten sonra ekranın uyarı kutularıyla dolmaması için bekleme (cooldown) süresi mevcuttur. Bilgisayar açılışında ağın gelmesini bekleyen startup delay ayarı vardır.
* 🪵 **Log Rotasyonu:** `RotatingFileHandler` sayesinde log dosyaları diskinizi doldurmaz (maksimum 5 dosya ve her biri 5MB).

---

## 🛠️ Kurulum ve Kullanım

### 1. Dosyaları Hazırlayın
Proje dosyalarını bilgisayarınızda bir klasöre çekin (örn: `C:\NetOutageMonitor`).

### 2. Servisi Yönetin
Klasörün içindeki `servis_yonetim.bat` dosyasını **Yönetici Olarak Çalıştırın**. Çıkan menüden:
* `[1]` tuşlayarak servisi kurabilir ve başlatabilirsiniz.
* `[2]` tuşlayarak servisi durdurup kaldırabilirsiniz.
* `[3]` tuşlayarak anlık durumuna bakabilirsiniz.

---

## ⚙️ Yapılandırma (`config.json`)

Servis ilk kez başladığında otomatik bir `config.json` oluşturur. Ayarları buradan özelleştirebilirsiniz:

* `aktif`: 1 aktif, 0 pasif mod.
* `ip`: UPS'e bağlı olmayan, şebeke elektriğine bağlı yerel cihazın IP adresi.
* `interval`: Kaç saniyede bir ping atılacağı.
* `cooldown`: Elektrik kesildiğinde art arda uyarı gelmemesi için saniye cinsinden sessizlik süresi.
* `startup_delay`: Windows açıldığında ağ kartının IP almasını beklemek için geçecek süre (saniye).

---

## 👨‍💻 Geliştirici

**Awosk**
* GitHub: [@Awosk](https://github.com/Awosk)

---

## 📜 Lisans

Bu proje MIT lisansı altında korunmaktadır. Kişisel veya ticari amaçlarla özgürce kullanılabilir, değiştirilebilir.
