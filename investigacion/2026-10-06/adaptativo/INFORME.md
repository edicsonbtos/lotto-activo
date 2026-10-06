# Ajustes al motor tras el enjambre "día de la semana" (2026-10-06): NINGUNO PASA
Pre-registro: `PREREGISTRO.md`. Scripts: `ad.py` y `temp.py`. Salidas: `salida.txt` y `salida_temp.txt`.

| candidata | elegida en dev-A | dev-B | 2026 | veredicto |
|---|---|---|---|---|
| AD: factor adaptativo de "ya salió hoy" por día de la semana | K=26, a=3 | −0,3 [−2,6; +1,9] | +5,3 [+2,3; +8,4] (mié-vie +11,3) | NO PASA (dev-B) |
| GL: lo mismo sin día de la semana (control) | K=4, a=30 | +2,1 [+0,9; +3,2] | +1,4 [+0,5; +2,4] | era el control; no mueve Top-5, Top-15 ni plata |
| Temperatura global | T=0,92 | −1,9 [−3,1; −0,7] | +1,4 [+0,2; +2,6] | NO PASA (dev-B; T óptima 1,08 en dev-B y 0,87 en 2026) |

- Los domingos de dev-B (el régimen viejo) solo dan +4 [−8; +16] con AD. El factor adaptativo no "siguió" al domingo con
  la claridad necesaria.
- Conclusión: el motor de producción se queda como está. La pérdida de miércoles a viernes de 2026 no se recupera con
  ajustes simples y aprendidos solo del pasado. Sigue el pre-registro en vivo de `../semana/INFORME.md`.
- GL (+1-2 mbits, estable en dev-B y 2026) queda anotada como posible mejora menor. No cambia la jugada.
