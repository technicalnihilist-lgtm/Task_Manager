#!/usr/bin/env bash
# Reproducible build for Task Manager (no Gradle, no Android Studio needed).
#
# Requirements:
#   - JDK 17+  (java, javac or ecj, keytool)
#   - Android SDK build-tools 34.0.0   (aapt2, d8, zipalign, apksigner)
#   - Android platform 34              (android.jar)
#
# Usage:
#   ANDROID_HOME=$HOME/Android/Sdk ./build.sh
#
# Output: Task_Manager.apk (signed, installable on API 21+)
set -euo pipefail

SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
BT="$SDK/build-tools/34.0.0"
AJ="$SDK/platforms/android-34/android.jar"

for t in "$BT/aapt2" "$BT/d8" "$BT/zipalign" "$BT/apksigner" "$AJ"; do
  [ -e "$t" ] || { echo "missing: $t  (set ANDROID_HOME)"; exit 1; }
done

PKG=com.hubclue.taskmanager
OUT=build
KS=keystore.jks
KS_PASS=taskmanager123

rm -rf "$OUT"
mkdir -p "$OUT"/{res,classes,dex,gen}

echo "==> compiling resources"
"$BT/aapt2" compile --dir res -o "$OUT/res.zip"

echo "==> linking resources + assets"
"$BT/aapt2" link -o "$OUT/base.apk" \
  -I "$AJ" --manifest AndroidManifest.xml "$OUT/res.zip" \
  -A assets --java "$OUT/gen" \
  --min-sdk-version 21 --target-sdk-version 34 \
  --version-code 1 --version-name 1.0

echo "==> compiling java"
SRC=$(find src "$OUT/gen" -name '*.java')
if command -v javac >/dev/null 2>&1; then
  javac -source 8 -target 8 -nowarn -bootclasspath "$AJ" -d "$OUT/classes" $SRC
else
  echo "javac not found - expecting ecj.jar next to this script"
  java -jar ecj.jar -source 1.8 -target 1.8 -nowarn -bootclasspath "$AJ" -d "$OUT/classes" $SRC
fi

echo "==> dexing"
"$BT/d8" --release --lib "$AJ" --min-api 21 --output "$OUT/dex" \
  $(find "$OUT/classes" -name '*.class')

cp "$OUT/base.apk" "$OUT/unsigned.apk"
(cd "$OUT/dex" && zip -q -u ../unsigned.apk classes.dex)

echo "==> zipalign + sign"
[ -f "$KS" ] || keytool -genkeypair -keystore "$KS" -alias taskmanager \
  -keyalg RSA -keysize 2048 -validity 10950 \
  -storepass "$KS_PASS" -keypass "$KS_PASS" \
  -dname "CN=Task Manager, OU=Apps, O=HubClue, L=India, C=IN"

"$BT/zipalign" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
"$BT/apksigner" sign --ks "$KS" --ks-pass "pass:$KS_PASS" --key-pass "pass:$KS_PASS" \
  --ks-key-alias taskmanager --min-sdk-version 21 \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --out Task_Manager.apk "$OUT/aligned.apk"

"$BT/apksigner" verify --print-certs Task_Manager.apk
echo "==> done: $(ls -l Task_Manager.apk | awk '{print $5" bytes"}')"
