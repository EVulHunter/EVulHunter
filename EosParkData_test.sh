#!/usr/bin/env bash
#Vul1 

 FILES=Assistant/EosParkData/xlotoioeosio*
 for f in $FILES
 do
    (time python3 EOSVulDetector.py -i $f -t 1 -o "EosParkDataResult.txt") 2>> ./log/time.txt
 done

 FILES=Assistant/EosParkData/eoslotsystem*
 for f in $FILES
 do
    (time python3 EOSVulDetector.py -i $f -t 1 -o "EosParkDataResult.txt") 2>> ./log/time.txt
 done

 FILES=Assistant/EosParkData/eoscastdmgb1*
 for f in $FILES
 do
    (time python3 EOSVulDetector.py -i $f -t 1 -o "EosParkDataResult.txt") 2>> ./log/time.txt
 done

FILES=Assistant/EosParkData/eosbetdice*
for f in $FILES
do
   (time python3 EOSVulDetector.py -i $f -t 1 -o "EosParkDataResult.txt") 2>> ./log/time.txt
done

#Vul2

 FILES=Assistant/EosParkData/epsdcclassic*
 for f in $FILES
 do
    (time python3 EOSVulDetector.py -i $f -t 2 -o "EosParkDataResult.txt") 2>> ./log/time.txt
 done

 FILES=Assistant/EosParkData/nkpaymentcap*
 for f in $FILES
 do
    (time python3 EOSVulDetector.py -i $f -t 2 -o "EosParkDataResult.txt") 2>> ./log/time.txt
 done

FILES=Assistant/EosParkData/eosbetdice*
for f in $FILES
do
   (time python3 EOSVulDetector.py -i $f -t 2 -o "EosParkDataResult.txt") 2>> ./log/time.txt
done


