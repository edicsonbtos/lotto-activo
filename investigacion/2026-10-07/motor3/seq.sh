for a in "S3 90" "S3 45" "S2 45"; do set -- $a; python3 -I correr_s3.py $1 $2 > salida_$1_$2.txt 2>&1; done
