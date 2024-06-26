
# Stakeland Tokens Checker

## 🔗 Links

🔔 CHANNEL: https://t.me/JamBitPY

💬 CHAT: https://t.me/JamBitChat

💰 DONATION EVM ADDRESS: 0xe23380ae575D990BebB3b81DB2F90Ce7eDbB6dDa


## 🤖 | Description:
```This bot is designed to automate the process of checking the balance of the Stakeland tokens.```

## 🚀 Installation


`` Required python >= 3.10``

``1. Close the repo and open CMD (console) inside it``

``2. Install requirements: pip install -r requirements.txt``

``3. Setup configuration and accounts``

``4. Run: python run.py``


## ⚙️ Config (config > settings.yaml)

| Name                | Description                                        |
|---------------------|----------------------------------------------------|
| eth_rpc             | ETH RPC URL (if not have, leave the default value) |
| threads             | Number of accounts that will work in parallel      |


## ⚙️ Accounts format (config > accounts.txt)

- wallet_mnemonic/private_key|proxy

`` Proxy format: IP:PORT:USER:PASS``


## 📄 Results
```After the script is finished, the results will be saved in the config folder in files success_accounts.txt/failed_accounts.txt```