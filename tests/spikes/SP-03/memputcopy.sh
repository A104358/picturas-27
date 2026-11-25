anon(){ docker compose exec -T seaweedfs sh -c 'grep "^anon " /sys/fs/cgroup/memory.stat' | awk '{printf "%.0f\n", $2/1048576}'; }
for run in 1 2 3; do
  docker compose restart seaweedfs >/dev/null 2>&1; sleep 22
  base=$(anon)
  ( for i in $(seq 1 60); do anon; sleep 0.05; done ) > put.txt &
  docker compose exec -T t python /w/memput.py $run; wait
  mid=$(anon)
  ( for i in $(seq 1 60); do anon; sleep 0.05; done ) > copy.txt &
  docker compose exec -T t python /w/memcopy2.py $run; wait
  echo "run $run: base ${base} | PUT peak $(sort -n put.txt | tail -1) (delta $(( $(sort -n put.txt | tail -1) - base ))) | before copy ${mid} | COPY peak $(sort -n copy.txt | tail -1) (delta vs base $(( $(sort -n copy.txt | tail -1) - base ))) MiB"
done
