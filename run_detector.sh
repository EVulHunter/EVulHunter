#!/usr/bin/env bash
# vulnerability dapp list from: https://github.com/peckshield/EOS/tree/master/known_dapp_attacks
# from dapp name to contract name: https://dappradar.com
# from contract name to bytecode: https://eospark.com

# False Eos:
# 20190305 extreme loto | xlotoioeosio
# 20190131 eoslots      | eoslotsystem
# 20181031 eoscast      | eoscastdmgb1

## 20180914 eosbet       | eosbetdice11
# 20180914 newdex       | newdexpocket      #Couldn't get the code before 20180914. A 20181220 gotten but no error.
# 20180914 eos.win      | eosluckygame eosluckydice iamblackjack

# False Recipiet
#20910311 nkpaymentcap      | nkpaymentcap
#20190309 gamble eos        | gambeosadmin
#20190205 eos playstation   | epsdcclassic (13 in total, only epsdcclassic detected for now)
#20181223 pickown           | pickowngames

##20181015 eosbet            | eosbetdice11


#       file name                                        detector result         expected result
files_vul1=(
        "samples/falseos/xlotoioeosio_2019_0226.wasm"    #yes                    yes
        "samples/falseos/xlotoioeosio_2019_0415.wasm"    #no                     no
        "samples/falseos/eoslotsystem_2018_1228.wasm"    #yes                    yes
        "samples/falseos/eoslotsystem_2019_0321.wasm"    #no                     no
        "samples/falseos/eoscastdmgb1_2018_1030.wasm"    #yes                    yes
        "samples/falseos/eoscastdmgb1_2019_0528.wasm"    #no                     no
  )


files_vul2=(
    "samples/falserecipient/pickowngames_2018_1212.wasm"    #特殊情况(没有)
    "samples/falserecipient/pickowngames_2019_0127.wasm"
    "samples/falserecipient/gambeosadmin_2019_0121.wasm" #我觉得就是没有
    "samples/falserecipient/gambeosadmin_2019_0412.wasm" #可以说已经凉了
    "samples/falserecipient/nkpaymentcap_2018_1229.wasm"
    "samples/falserecipient/nkpaymentcap_2019_0314.wasm"
    "samples/falserecipient/epsdcclassic_2018_1206.wasm"
    "samples/falserecipient/epsdcclassic_2019_0214.wasm"
)

for i in "${files_vul1[@]}"
do
   python3 EOSVulDetector.py -i $i -t 1
done

for i in "${files_vul2[@]}"
do
   python3 EOSVulDetector.py -i $i -t 2
done