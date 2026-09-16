@echo off
rem Mesa del consejo: corre las 5 estrategias y guarda predicciones del proximo sorteo.
rem Se programa con el Programador de tareas (ver LEEME o abajo).
cd /d "C:\Users\edics\Downloads\lotto-activo\lotto-activo"
set PYTHONIOENCODING=utf-8
python herramientas\exploracion\consejo_mesa.py > herramientas\resultados\mesa_consejo.txt 2>&1
