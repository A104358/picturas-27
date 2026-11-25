NET=picturas-spike_default; S=$(pwd)
url(){ docker compose exec -T t python -c "
import boto3; from botocore.config import Config
s=boto3.client('s3',endpoint_url='https://seaweedfs:9000',aws_access_key_id='imgstorage',aws_secret_access_key='imgstorage-secret-0123456789',region_name='us-east-1',verify='/pki/ca.crt',config=Config(s3={'addressing_style':'path'},signature_version='s3v4'))
print(s.generate_presigned_url('get_object',Params={'Bucket':'picturas','Key':'users/u/projects/p/src/$1'},ExpiresIn=300))"; }
OPTS='-v error -print_format json -show_format -show_streams -protocol_whitelist https,tls,tcp -tls_verify 1 -max_redirects 0 -rw_timeout 5000000 -reconnect 0'
probe(){ # label url extra-opts
  docker run --rm --network $NET -v $S/pki:/pki:ro --entrypoint sh picturas-nfr-projects -c "
    r0=\$(cat /sys/class/net/eth0/statistics/rx_bytes); t0=\$(date +%s%N)
    timeout 20 ffprobe $OPTS -ca_file \${CA:-/pki/ca.crt} $3 '$2' > /tmp/o.json 2>/tmp/e.txt; rc=\$?
    t1=\$(date +%s%N); r1=\$(cat /sys/class/net/eth0/statistics/rx_bytes)
    echo \"rc=\$rc ms=\$(( (t1-t0)/1000000 )) rx_bytes=\$((r1-r0))\"
    head -c 300 /tmp/e.txt
    grep -oE '\"(codec_name|duration|width|height|format_name)\": \"?[^,\"]*' /tmp/o.json | sort -u | tr '\n' ' '; echo" ; }
for f in pad_500MiB_H.mp4 pad_500MiB_T.mp4 sample_6s.mov; do
  for i in 1 2 3; do echo "## $f run $i"; probe $f "$(url $f)"; done
done
U=$(url pad_500MiB_T.mp4)
echo "## wrong CA";              CA=/pki/otherca.crt probe x "$U" "-ca_file /pki/otherca.crt"
echo "## tls_verify on, verifyhost=projects (name mismatch)"; probe x "$U" "-verifyhost projects"
echo "## plain http URL (protocol whitelist https only)"; probe x "${U/https:/http:}"
echo "## redirect (max_redirects 0)"; probe x "https://seaweedfs-redirect:9443/redirect"
echo "## redirect with ffmpeg default (max_redirects 8, for contrast)"; OPTS="${OPTS/-max_redirects 0/}" probe x "https://seaweedfs-redirect:9443/redirect"
echo "## stalled server (rw_timeout 5 s)"; probe x "https://seaweedfs-redirect:9443/stall"
echo "## expired/forged URL"; probe x "${U/X-Amz-Signature=/X-Amz-Signature=00}"
