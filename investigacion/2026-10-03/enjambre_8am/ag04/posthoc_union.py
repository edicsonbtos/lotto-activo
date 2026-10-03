# Post-hoc SOLO en dev (no va a prueba): unión de las 10 familias por origen.
exec(open('analisis.py').read().split("if __name__")[0])
U = np.zeros((K,K),bool)
for f in FAM: U |= REL[f]
print('tamaño medio unión', U.sum(1).mean())
for on,o in ORIG.items():
    for nm,m in [('9:00',era_mask('dev',1)),('8:00',era_mask('dev',0)),('dev',era_mask('dev'))]:
        n,O,E = oe(m,o,U); print(on,nm,n,O,round(E,1),round(O/E,2),'p2=%.3f'%poi_p(O,E)[0])
    nc,Oc,Ec = cal_crudo(o,U); print(on,'cal crudo',nc,Oc,round(Ec,1),round(Oc/Ec,2))
