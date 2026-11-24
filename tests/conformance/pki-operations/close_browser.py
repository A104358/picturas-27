"""Close only the technical browser fixture; records no inspection receipt."""
import sys
from pilot_paths import ROOT
flag=ROOT/'pilot'/('trial-'+sys.argv[1])/'browser-close'
if '--prepare' in sys.argv:flag.unlink(missing_ok=True)
else:flag.touch()
