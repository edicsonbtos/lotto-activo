"""A5 extra 3 (descriptivo): información del motor sobre el azar uniforme (mbits/sorteo), mié-vie vs resto, por tramo."""
import sys, numpy as np
sys.argv = sys.argv[:2]
exec(open(__file__.replace("a5_bits.py", "a5.py")).read().split("RES = {}")[0])
g = 1000 * (lPy - np.log2(1 / 38))
for lab, m in (("dev 2024-25", DEV), ("AJUSTE", AJ), ("PRUEBA", PR)):
    a = boot(g, m & MVF); b = boot(g, m & ~MVF)
    print(f"  {lab:12}: motor vs uniforme mié-vie {a[0]:+6.1f} [{a[1]:+.1f}; {a[2]:+.1f}]  resto {b[0]:+6.1f} [{b[1]:+.1f}; {b[2]:+.1f}] mbits/sorteo")
