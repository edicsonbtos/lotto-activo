import json,os,sys,time,glob,subprocess
from concurrent.futures import ThreadPoolExecutor
B="https://lotto-activo-production.up.railway.app/api/mesa"
def get(args):
    m,o=args; f=f"raw/{m}/{o}.json"
    if os.path.exists(f): return
    for i in range(4):
        r=subprocess.run(["curl","-s","--max-time","60",f"{B}?offset={o}&modelo={m}"],capture_output=True)
        try: json.loads(r.stdout); open(f,"wb").write(r.stdout); return
        except Exception: time.sleep(2)
    print("fallo",m,o)
m=sys.argv[1]; os.makedirs(f"raw/{m}",exist_ok=True)
for f in glob.glob(f"raw/{m}/*.tmp"):
    try: json.load(open(f)); os.rename(f,f[:-4])
    except Exception: os.remove(f)
T=json.loads(subprocess.run(["curl","-s","--max-time","60",f"{B}?offset=0&modelo={m}"],capture_output=True).stdout)["total"]
with ThreadPoolExecutor(8) as ex: list(ex.map(get,[(m,o) for o in range(T+1)]))
print(m,T,len(glob.glob(f"raw/{m}/*.json")))
