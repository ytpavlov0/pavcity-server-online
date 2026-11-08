# PAVCITY Server Online

PAVCITY, tarayıcıda çalışan çok oyunculu bir Los Santos rol yapma (RP) sunucusunun **kendi yazdığımız kodudur**: oyun sunucusu, gerçek zamanlı aktarıcı, oyuna eklenen web arayüzü/modlar, yayın araçları ve testler.

> Bu depo **oyun motorunu ve oyun dosyalarını içermez** ve tek başına çalışmaz. Rockstar Games'e ait hiçbir oyun verisi, model, doku, arşiv (.rpf), motor (.wasm) veya şifreleme anahtarı burada yoktur ve eklenmemelidir. Grand Theft Auto ve Los Santos, Rockstar Games / Take-Two Interactive'in markalarıdır; bu proje onlarla bağlantılı değildir.

## İçerik

| Klasör | Ne var |
|---|---|
| `server/` | Python oyun sunucusu: hesaplar, ekonomi, araçlar, meslekler, polis/suç, NPC ambulans vb. Canlı sürüm `server/support/dev-tools/run_gameplay_live_v194.py`, her sürüm bir öncekinin üzerine kurulur. |
| `web/` | Oyun sayfasına eklenen arayüz ve oyun içi sistemler (HUD, telefon, sohbet, ölüm ekranı, köprü kodu). |
| `realtime/` | C# gerçek zamanlı konum aktarıcısı (`pavrt.cs`). |
| `tools/` | Sürüm hazırlama/kontrol/yayın betikleri ve Cloudflare tüneli için watchdog. |
| `tests/` | Node ve Python testleri. |

## Yapılandırma

Gizli bilgiler depoda **yoktur**; çalıştırırken kendin oluşturman gerekir:

- `backups/rt172.secret` – sunucu ile aktarıcı arasındaki paylaşılan HMAC anahtarı (rastgele 32 bayt, base64)
- `backups/gate157-secret.txt` – oturum kapısı anahtarı
- Cloudflare tüneli için kendi `config.yml` dosyan ve kendi alan adın (kodda `your-domain.example` yazan yerler)
- Veritabanı (`online.db`) ilk açılışta boş oluşturulur

Kodda geçen `C:\PAVCITY` yolları kurulum klasörünü temsil eder.

---

**EN:** Source code of PAVCITY, a browser-based multiplayer roleplay server: Python game server, C# realtime relay, in-game web UI/mods, release tooling and tests. It does **not** include the game engine or any game data and cannot run on its own. No Rockstar Games assets are or may be included. Not affiliated with Rockstar Games or Take-Two Interactive.
