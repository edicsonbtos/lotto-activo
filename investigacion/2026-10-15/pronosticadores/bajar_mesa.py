# -*- coding: utf-8 -*-
"""Baja /api/mesa?offset=N (solo GET, con curl) y guarda fecha, hora, ganador y prob del motor congelado.
Salida: datos/mesa.jsonl"""
import json, os, subprocess, time

AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, "datos", "mesa.jsonl")
BASE = "https://lotto-activo-production.up.railway.app/api/mesa?offset="


def get(o):
    r = subprocess.run(["curl", "-s", "--max-time", "40", BASE + str(o)], capture_output=True)
    return json.loads(r.stdout.decode("utf-8"))


def main():
    os.makedirs(os.path.dirname(SAL), exist_ok=True)
    total = get(1)["total"]
    with open(SAL, "w", encoding="utf-8") as fo:
        for o in range(1, total + 1):
            d = get(o)
            fo.write(json.dumps({"fecha": d["fecha"], "hora": d["hora"], "winner_num": d["winner_num"],
                                 "modelo": d.get("modelo"),
                                 "prob": {a["num"]: a["prob"] for a in d["animales"]}}) + "\n")
            time.sleep(0.2)
    print("ok", total)


if __name__ == "__main__":
    main()
