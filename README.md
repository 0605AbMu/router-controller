# router-controller

TP-Link router boshqarish uchun cross-platform CLI. macOS, Windows va Linux da ishlaydi.

## O'rnatish

```bash
pip install git+https://github.com/AlexandrErohin/TP-Link-Archer-C6U
pip install -e .
```

## Sozlash

```bash
router config set --host http://192.168.0.1 --password PAROLINGIZ
```

## Buyruqlar

```bash
router status                     # Umumiy holat
router devices                    # Ulangan qurilmalar
router devices --all              # Oflayn qurilmalar ham
router devices --band 2.4         # Faqat 2.4 GHz qurilmalar
router devices --sort ip          # IP bo'yicha saralash

router wifi status                # WiFi holati va channellar
router wifi on 2.4                # 2.4 GHz yoqish
router wifi off 5                 # 5 GHz o'chirish
router wifi channel 2.4 6         # 2.4 GHz channelni 6 ga o'zgartirish
router wifi channel 5 36          # 5 GHz channelni 36 ga o'zgartirish
router wifi channel 2.4 0         # Avtomatik channel

router firmware                   # Firmware versiyasi
router dhcp                       # DHCP ro'yxati
router reboot                     # Qayta ishga tushirish

router config show                # Saqlangan sozlamalar
router config clear               # Sozlamalarni o'chirish
```

## Qo'llab-quvvatlanadigan modellar

Barcha `tplinkrouterc6u` kutubxonasi tomonidan qo'llab-quvvatlanadigan modellar:
Archer C6, C80, C50, C1200, C3200, C5400X, VR seriyasi, MR seriyasi, Deco, WR841N va boshqalar.
