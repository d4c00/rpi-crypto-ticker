Real-time cryptocurrency price display on Waveshare 1.3inch LCD HAT via Binance API for Raspberry Pi.<br>
Hardware Documentation: https://www.waveshare.net/wiki/1.3inch_LCD_HAT<br>
<div align="left">
  <img src="https://github.com/user-attachments/assets/ca1dc8fd-6ccd-40ed-bb53-e11916c7a919" width="80%" />
</div>

Download the code:
```bash
mkdir -p ~/rpi-crypto-ticker
curl -L https://github.com/d4c00/rpi-crypto-ticker/archive/refs/heads/main.tar.gz | tar -xz -C ~/rpi-crypto-ticker --strip-components=1
```
Configure and run:
```bash
mkdir -p ~/.config/systemd/user/
cp ~/rpi-crypto-ticker/rpi-crypto-ticker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable rpi-crypto-ticker
systemctl --user restart rpi-crypto-ticker
```

To modify the displayed trading pairs and prices:
```bash
nano ~/rpi-crypto-ticker/main.py
```
Locate the PAIRS list around line 29:
```nano
PAIRS = [
    ("BTCUSDT", "BTC/USDT", "btc"),
    ("ETHUSDT", "ETH/USDT", "eth"),
    ("ETHBTC",  "ETH/BTC",  "ethbtc"), 
]
```
Modify trading pairs:<br>
Each row represents one pair: ("API_Symbol", "Display_Name", "Icon_Name").<br>
"Icon_Name" Example: "btc" will automatically load img/btc.png.

To monitor logs:
```bash
sudo journalctl _SYSTEMD_USER_UNIT=rpi-crypto-ticker.service -f
```

<br>

###### License & Credits<br>Main Code: © 2026 length <me@length.cc> (https://github.com/d4c00) Licensed under MIT.<br>Drivers (config.py, ST7789.py): By Waveshare. Licensed under MIT.<br>Font (Georama-Regular.ttf): Designed by Production Type. Licensed under SIL Open Font License 1.1.<br>Icons (img/*.png): Licensed under CC0 (Public Domain).
