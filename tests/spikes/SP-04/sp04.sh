U=https://127.0.0.1:18443
C(){ curl -sk --cacert pki/ca.crt -o resp.txt -w '%{http_code}' "$@"; printf '  %s\n' "$(grep -o '<Code>[^<]*' resp.txt | head -1)"; }
head -c 1000 /dev/urandom > k1.bin; head -c 2000 /dev/urandom > k2.bin; head -c 20971520 /dev/urandom > k20.bin
echo "## 1 B7 shape (Host seaweedfs:9000, Authorization cleared), 1000 bytes"; printf '  '; C -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --data-binary @k1.bin $U/uploads/t1
echo "## 2 key with spaces, +, ç and parentheses"; printf '  '; C -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --data-binary @k1.bin $U/uploads/t2
echo "## 3 signed length 1000, client sends 2000"; printf '  '; C -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --data-binary @k2.bin $U/uploads/t3
echo "## 4 20 MiB at 4 MiB/s, streamed"; printf '  '; C -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --limit-rate 4M --data-binary @k20.bin $U/uploads/t20
echo "## 5 client Authorization forwarded to S3"; printf '  '; C -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --data-binary @k1.bin $U/uploads-keepauth/t5
echo "## 6 public Host forwarded"; printf '  '; C -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --data-binary @k1.bin $U/uploads-publichost/t6
echo "## 7 no JWT"; printf '  '; C -X PUT -H 'Expect:' --data-binary @k1.bin $U/uploads/t7
echo "## 8 presigned GET (signed for seaweedfs:9000) through /s3/ with Host seaweedfs:9000 and through /s3-publichost/"
GETURL=$(docker compose exec -T t python -c "
import boto3; from botocore.config import Config
s=boto3.client('s3',endpoint_url='https://seaweedfs:9000',aws_access_key_id='imgstorage',aws_secret_access_key='imgstorage-secret-0123456789',region_name='us-east-1',verify='/pki/ca.crt',config=Config(s3={'addressing_style':'path'},signature_version='s3v4'))
print(s.generate_presigned_url('get_object',Params={'Bucket':'picturas','Key':'staging/sp04-plain'},ExpiresIn=300))")
P=${GETURL#https://seaweedfs:9000/}
printf '  /s3/ GET: '; C "$U/s3/$P"
printf '  /s3/ Range GET: '; curl -sk -o /dev/null -w '%{http_code} bytes=%{size_download}\n' -H 'Range: bytes=0-99' "$U/s3/$P"
printf '  /s3/ HEAD: '; curl -sk -I -o /dev/null -w '%{http_code}\n' "$U/s3/$P"
printf '  /s3/ PUT (limit_except): '; C -X PUT --data-binary @k1.bin "$U/s3/$P"
printf '  /s3-publichost/ GET: '; C "$U/s3-publichost/$P"
echo "## 9 objects written (admin listing)"
docker compose exec -T t python -c "
import boto3; from botocore.config import Config
s=boto3.client('s3',endpoint_url='https://seaweedfs:9000',aws_access_key_id='spikeadmin',aws_secret_access_key='spikeadmin-secret-0123456789',region_name='us-east-1',verify='/pki/ca.crt',config=Config(s3={'addressing_style':'path'}))
[print('  ',o['Key'],o['Size']) for o in s.list_objects_v2(Bucket='picturas',Prefix='staging/sp04').get('Contents',[])]"
