# compara log-verosimilitud por fila (bits) de dos corridas: diferencia media en mbits y SE pareado
import sys, numpy as np
a=np.load(sys.argv[1]); b=np.load(sys.argv[2]); d=a-b
print(f"diff {d.mean()*1000:+.2f} mbits  SE {d.std()/np.sqrt(len(d))*1000:.2f}  por cuartos {[round(x.mean()*1000,1) for x in np.array_split(d,4)]}")
