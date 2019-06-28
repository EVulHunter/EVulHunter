# EVulHunter

EVulHunter is a binary-level vulnerability detector for EOS smart contracts, which is based on [Octopus](https://github.com/quoscient/octopus) project. 


## Description

EVulHunter supports two types of vulnerability detection for now: **Fake EOS Transfer** and **Fake Transfer Notice**. 

- A video illustration: https://youtu.be/5SJ0ZJKVZvw

- Paper related: https://arxiv.org/abs/1906.10362

## Run EVulHunter

### Dependencies

- install [Octopus](https://github.com/quoscient/octopus) project first.

### Run Test Data
 
```
$ git clone git@github.com:EVulHunter/EVulHunter.git

$ cd ./EVulHunter

$ mkdir ./log

$ chmod +x ./EosParkData_test.sh

$ ./EosParkData_test.sh
```

After running these commands, a file named ``EosParkDataResult.txt`` will be generated in the ``./log/`` directory, containing the final detection results. Also a file named ``time.txt`` will be generated, suggesting the execution time of each detection.

The description of test data is [here](https://github.com/EVulHunter/EVulHunter#description-of-test-data).

### Analyze your own contract

In your terminal, 
```
python3 EOSVulDetector.py -i|--input <FILEPATH> -t|--type <VUL_TYPE> -o|--output <OUTPUT_FILENAME>
```
- ``<FILEPATH>`` is the path of the binary file of your contract.

- ``type`` can be either `1` or `2`. `1` means the **Fake EOS Transfer** vulnerability detection and `2` means the **Fake Transfer Notice** vulnerablity.

- ``<OUTPUT_FILENAME>`` suggests the output file path.

For example, you can run the following command to analyze the file ``"Assistant/EosParkData/eosbetdice11_2018-10-26T23:57:55_23706016.wasm"``:
```
 python3 EOSVulDetector.py -i "Assistant/EosParkData/eosbetdice11_2018-10-26T23:57:55_23706016.wasm" -t 2 -o "test.txt"
 ```

The result will be like:
```
Detector start!
Assistant/EosParkData/eosbetdice11_2018-10-26T23:57:55_23706016.wasm 2
the index of eosio_assert is  23
C1 paths searched! 4
C2 paths searched! 320
focused f : [43, 46, 48, 50, 52, 55]

in C2,  80 paths will lead to indirect call
in C2,  [49] is the target func to be called: 
$func49
start block_d_0
assert block when call 87
dubious func:  -48
start block_d_0
assert block when call 87
dubious func:  -48
######result########
No Vul2.
######result########

```
The description of the output is [here](https://github.com/EVulHunter/EVulHunter#description-of-output).

Also, a file named ``test.txt`` will be generated in the ``./log`` directory. In this file, the content will be like:
```
Assistant/EosParkData/eosbetdice11_2018-10-26T23:57:55_23706016.wasm        No Vul2.
```

## Other Content Included in This Repository

- ``./Assistant`` [directory](https://github.com/EVulHunter/EVulHunter/tree/master/Assistant): A python sript used to fetch binary data from EosPark.

- ``./myhelper/wasm`` directory: It is modified from [this project](https://github.com/athre0z/wasm), in order to solve the problem about getting the offset of data section in wasm module. (Notes: It's a temporary solution. Better solution wip)

## More Details

### Description of Test Data

### Description of Output