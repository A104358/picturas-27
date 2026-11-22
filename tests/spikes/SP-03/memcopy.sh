anon(){ docker compose exec -T seaweedfs sh -c 'grep "^anon " /sys/fs/cgroup/memory.stat' | awk '{printf "%.0f\n", $2/1048576}'; }
docker compose exec -T t python /w/memcopy.py prep
for run in 1 2 3; do
  docker compose restart seaweedfs >/dev/null 2>&1; sleep 22
  base=$(anon)
  ( for i in $(seq 1 30); do anon; sleep 0.05; done ) > memsamples.txt &
  docker compose exec -T t python /w/memcopy.py copy $run
  wait; max=$(sort -n memsamples.txt | tail -1)
  echo "run $run (seaweedfs restarted): anon before ${base} MiB, max ${max} MiB, delta $((max-base)) MiB"
done
