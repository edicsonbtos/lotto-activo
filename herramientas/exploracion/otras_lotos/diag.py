import csv,collections,unicodedata,itertools
P='../../../scraping/resultados/consolidado_todos.csv'
def nm(s): return ''.join(c for c in unicodedata.normalize('NFD',s.upper().strip()) if unicodedata.category(c)!='Mn')
d=collections.defaultdict(dict); dup=collections.Counter()
for r in csv.DictReader(open(P,encoding='utf-8')):
    k=(r['fecha'],r['hora']); 
    if k in d[r['operador']]: dup[r['operador']]+=1
    d[r['operador']][k]=r['animal_numero'] or nm(r['animal_nombre'])
print('dups',dict(dup))
# repeticion dentro del dia y a distancia 1
for op in ['chanceb','chancea','centenaplus','lotochaima','megaanimal40','ruletaactiva','lottoactivo','centenaanimalitos']:
    s=sorted(d[op].items()); byday=collections.defaultdict(list)
    for (f,h),a in s: byday[f].append(a)
    rep=sum(len(v)-len(set(v)) for v in byday.values()); tot=sum(len(v) for v in byday.values())
    adj=sum(1 for i in range(1,len(s)) if s[i][1]==s[i-1][1])
    print(op,'rep en dia',rep,'de',tot,' adyacentes iguales',adj,'/',len(s), 'dist/dia',round(sum(len(set(v)) for v in byday.values())/len(byday),2),'n/dia',round(tot/len(byday),1))
# coincidencia exacta por slot entre pares
ops=list(d); best=[]
for a,b in itertools.combinations(ops,2):
    ks=set(d[a])&set(d[b])
    if len(ks)<500: continue
    m=sum(d[a][k]==d[b][k] for k in ks)/len(ks); best.append((m,a,b,len(ks)))
for m,a,b,n in sorted(best,reverse=True)[:8]: print(round(m,3),a,b,n)
