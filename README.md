# vaults-checker

This repository provides a way to check vaults at liquidation risk using https://api.makerdao.com/ API.

## Installation

This project uses *Python 3.6.6* and requires *virtualenv* to be installed.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/vaults-checker.git
cd vaults-checker
git submodule update --init --recursive
./install.sh
```

## Running

```
usage: vaults-checker [-h] --rpc-url RPC_URL [--rpc-timeout RPC_TIMEOUT]
                       [--ilk ILK] [--target-price TARGET_PRICE]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-url RPC_URL     JSON-RPC host URL
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 10)
  --ilk ILK             ILK to query
  --target-price TARGET_PRICE
                        Target price for given ILK
```

## Sample startup script

#### Check vaults at risk for specific ILK at target price
```
#!/bin/bash

bin/vaults-checker \
    --rpc-url https://localhost:8545 \
    --ilk MATIC-A \
    --target-price 0.1
```
Output:
```
====================================================
Collateral: MATIC-A 
Current OSM price: 2.0902324196097206 | Next OSM price: 2.0006662814399987 | Target price: 0.1 
Total collateral to liquidate: 61551385.160817645 | Total DAI to liquidate: 19746689.37961446
====================================================
Vaults at risk: 

URN: 0x7Ae4010A2fcB6236f8BC1460a3dAd7eC572403F4 | Liquidation Price: 1.7147154811941436 | Collateral: 273233.0
URN: 0x3Cf1a8a30B2A98346D69f8F6B0DE1A8aAdcFdBc3 | Liquidation Price: 1.3407017945752795 | Collateral: 20699.643803008363
URN: 0xA495198EfF058055E112ef2262853A71D25B5f19 | Liquidation Price: 1.2196941675782018 | Collateral: 21550.0
URN: 0xA9d388ae731cA5B0dA220066AA81016EC14bdd21 | Liquidation Price: 1.1461413604877306 | Collateral: 35187.42823950006
URN: 0x66fFc134D49764A7B0c223e0884489fc91d53019 | Liquidation Price: 1.1440083265683065 | Collateral: 61456.11339819305
URN: 0xCe4F170234691D1DCC43b457752A0771376cF8B4 | Liquidation Price: 1.0517626039755943 | Collateral: 55380.0
URN: 0xA305475d56168924a46b624aad53C217a729D65a | Liquidation Price: 0.8840993333909114 | Collateral: 862150.5312001666
URN: 0x1efD936EB27b7902864F69096c16Ef2532eCDB5E | Liquidation Price: 0.5505105142256955 | Collateral: 60000000.0
URN: 0xC0e1566507D08e051BAdb66F51A6760757624C06 | Liquidation Price: 0.450212648406718 | Collateral: 121728.44417677987
URN: 0x141B68B0D8ce6b7dD3CcEE5F3bF921FBd605554c | Liquidation Price: 0.17609166320723732 | Collateral: 100000.0
```

#### Check vaults at risk for specific ILK at next OSM price
```
#!/bin/bash

bin/vaults-checker \
    --rpc-url https://localhost:8545 \
    --ilk ETH-A
```
Output:
```
====================================================
Collateral: ETH-A 
Current OSM price: 3163.76 | Next OSM price: 3163.76 | Target price: 3163.76 
Total collateral to liquidate: 0.0 | Total DAI to liquidate: 0.0
====================================================
Vaults at risk: 

====================================================
```

#### Check vaults at risk for all ILKs at next OSM price
```
#!/bin/bash

bin/vaults-checker \
    --rpc-url https://localhost:8545
```