import io, sys, socket, requests
from PIL import Image
def png(c):
    b = io.BytesIO(); Image.new("RGB", (64, 64), c).save(b, "PNG"); return b.getvalue()
files = lambda: {"image": ("image.png", png((10, 200, 10)), "image/png"), "mask": ("mask.png", png((255, 255, 255)), "image/png")}
def t(label, url="https://generative-mock:7860/outpaint", **kw):
    try:
        r = requests.post(url, files=files(), data={"prompt": "x"}, timeout=10, **kw)
        print(f"  {label}: HTTP {r.status_code} {r.headers.get('Content-Type')} {len(r.content)} bytes")
    except Exception as e:
        print(f"  {label}: {type(e).__name__}: {str(e)[:120]}")
CA, ME = "/pki/ca.crt", ("/pki/expand_ai_tool.crt", "/pki/expand_ai_tool.key")
t("mTLS expand_ai_tool -> outpaint", cert=ME, verify=CA)
t("plain http", url="http://generative-mock:7860/outpaint")
t("https, no client cert", verify=CA)
t("https, client cert from other CA", cert=("/pki/rogue-expand.crt", "/pki/rogue-expand.key"), verify=CA)
t("https, valid installation cert CN=projects (not allowed)", cert=("/pki/projects.crt", "/pki/projects.key"), verify=CA)
t("server checked against other CA", cert=ME, verify="/pki/otherca.crt")
ip = socket.gethostbyname("generative-mock")
t("server by IP (name not in SAN)", url=f"https://{ip}:7860/outpaint", cert=ME, verify=CA)
t("verify=False is the forbidden pattern (control)", cert=ME, verify=False)
