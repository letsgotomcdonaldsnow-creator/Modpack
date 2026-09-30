#!/usr/bin/env bash
# Take in-game screenshots of the Alola Region world with the real client.
# run/ must already be assembled (`python tools/modpack.py client --dir run`) with the world in
# run/saves/Alola and the tour datapack (tools/worldgen/tour.py) in its datapacks folder.
# The datapack announces "TOUR <n> <name>" in chat at every viewpoint; this script waits for
# the chunks to render, grabs the X screen and saves tour/<nn>-<name>.png.
set -uo pipefail

HMC_VERSION=2.10.0
MC=1.21.1
TIMEOUT=${TOUR_TIMEOUT:-3900}
export DISPLAY=:99

mkdir -p HeadlessMC tour
cat > HeadlessMC/config.properties <<CFG
hmc.java.versions=$JAVA_HOME/bin/java
hmc.gamedir=$PWD/run
hmc.mcdir=$HOME/.minecraft
hmc.offline=true
hmc.rethrow.launch.exceptions=true
hmc.exit.on.failed.command=true
hmc.assets.dummy=true
hmc.check.xvfb=true
CFG

gh release download "$HMC_VERSION" -R 3arthqu4ke/headlessmc -p "headlessmc-launcher-$HMC_VERSION.jar" --clobber
HMC="headlessmc-launcher-$HMC_VERSION.jar"
java -jar "$HMC" --command download "$MC" </dev/null
java -jar "$HMC" --command fabric "$MC" --java 21 </dev/null

Xvfb :99 -screen 0 1600x900x24 -nolisten tcp &
xvfb_pid=$!
sleep 3

java -jar "$HMC" --command launch '.*fabric.*' -regex \
  --jvm '"-Djava.awt.headless=true -Xmx10G"' \
  --game-args '"--quickPlaySingleplayer Alola --width 1600 --height 900"' </dev/null > run/launcher.log 2>&1 &
pid=$!

stop_game() { pkill -f KnotClient; sleep 3; pkill -f "$HMC"; kill "$xvfb_pid" 2>/dev/null; }
log=run/logs/latest.log
start=$(date +%s)
done_n=0
hid_hud=0
while true; do
  if (( $(date +%s) - start > TIMEOUT )); then
    echo "Timed out after ${TIMEOUT}s with $done_n screenshots."
    break
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "The client exited early."
    tail -80 run/launcher.log
    break
  fi
  if [ "$hid_hud" = 0 ] && grep -q "TOUR START" "$log" 2>/dev/null; then
    # hide the HUD (F1) so the screenshots show only the world
    xdotool mousemove 800 450 2>/dev/null; sleep 1; xdotool key F1 2>/dev/null
    hid_hud=1
  fi
  # the datapack says "SHOT <n> <name>" and waits 4 s before moving the camera: grab the screen now
  line=$(grep -oE "SHOT [0-9]+ [a-z0-9_]+" "$log" 2>/dev/null | tail -1)
  if [ -n "$line" ]; then
    n=$(echo "$line" | cut -d' ' -f2)
    name=$(echo "$line" | cut -d' ' -f3)
    if (( n > done_n )); then
      file=$(printf "tour/%03d-%s.png" "$n" "$name")
      import -window root "$file" && echo "captured $file"
      done_n=$n
    fi
  fi
  if grep -q "TOUR END" "$log" 2>/dev/null; then
    echo "Tour finished with $done_n screenshots after $(( $(date +%s) - start ))s."
    break
  fi
  sleep 1
done
stop_game
ls tour | head -80
[ "$done_n" -gt 0 ]
