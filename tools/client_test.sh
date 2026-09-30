#!/usr/bin/env bash
# Launch the real Minecraft client with the pack (run/ must already be assembled by
# `python tools/modpack.py client --dir run`), let mc-runtime-test create and join a
# single-player world, and pass once it reports success. Used by CI under Xvfb.
set -uo pipefail

HMC_VERSION=2.10.0
MCRT_VERSION=4.5.1
MC=1.21.1
TIMEOUT=${CLIENT_TEST_TIMEOUT:-1500}

mkdir -p HeadlessMC run/mods
cat > HeadlessMC/config.properties <<CFG
hmc.java.versions=$JAVA_HOME/bin/java
hmc.gamedir=$PWD/run
hmc.mcdir=$HOME/.minecraft
hmc.offline=true
hmc.rethrow.launch.exceptions=true
hmc.exit.on.failed.command=true
hmc.assets.dummy=true
CFG

gh release download "$HMC_VERSION" -R 3arthqu4ke/headlessmc -p "headlessmc-launcher-$HMC_VERSION.jar" --clobber
gh release download "$MCRT_VERSION" -R headlesshq/mc-runtime-test -p "mc-runtime-test-$MC-*-fabric-release.jar" -D run/mods --clobber
HMC="headlessmc-launcher-$HMC_VERSION.jar"
java -jar "$HMC" --command download "$MC" </dev/null
java -jar "$HMC" --command fabric "$MC" --java 21 </dev/null

printf 'onboardAccessibility:false\npauseOnLostFocus:false\n' >> run/options.txt

xvfb-run -a java -Dhmc.check.xvfb=true -jar "$HMC" --command launch '.*fabric.*' -regex \
  --jvm "-Djava.awt.headless=true -Xmx10G" </dev/null > run/launcher.log 2>&1 &
pid=$!

stop_game() { pkill -f KnotClient; sleep 3; pkill -f "$HMC"; pkill -f Xvfb; }
start=$(date +%s)
while true; do
  if grep -q "Successfully finished" run/logs/latest.log 2>/dev/null; then
    echo "Client joined a world and mc-runtime-test finished after $(( $(date +%s) - start ))s."
    stop_game
    exit 0
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    wait "$pid"; code=$?
    echo "The client exited with code $code before finishing the test."
    tail -60 run/launcher.log
    exit 1
  fi
  if (( $(date +%s) - start > TIMEOUT )); then
    echo "Timed out after ${TIMEOUT}s."
    stop_game
    exit 1
  fi
  sleep 10
done
