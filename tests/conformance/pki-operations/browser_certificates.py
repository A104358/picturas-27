"""Issue only negative browser fixtures under the private pilot CA. No key output."""
import datetime
import os
from pathlib import Path
import sys
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID
from pilot_paths import ROOT as root
output=Path(sys.argv[1]);output.mkdir(mode=0o700,exist_ok=True)
ca=x509.load_pem_x509_certificate((root/'pki/ca/ca.crt').read_bytes())
ca_key=serialization.load_pem_private_key((root/'pki/ca/ca.key').read_bytes(),password=None)
now=datetime.datetime.utcnow()
for case in ['wrong_name','expired']:
 key=ec.generate_private_key(ec.SECP256R1())
 dns='wrong-picturas.invalid' if case=='wrong_name' else 'localhost'
 cert=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,dns)]))
  .issuer_name(ca.subject).public_key(key.public_key()).serial_number(x509.random_serial_number())
  .not_valid_before(now-datetime.timedelta(days=2)).not_valid_after(now+datetime.timedelta(days=1) if case!='expired' else now-datetime.timedelta(days=1))
  .add_extension(x509.SubjectAlternativeName([x509.DNSName(dns)]),critical=False)
  .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
  .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),critical=False)
  .sign(ca_key,hashes.SHA256()))
 (output/(case+'.key')).write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
 (output/(case+'.key')).chmod(0o600)
 (output/(case+'.crt')).write_bytes(cert.public_bytes(serialization.Encoding.PEM));(output/(case+'.crt')).chmod(0o644)
print('Browser certificate fixtures prepared; no credentials reported')
