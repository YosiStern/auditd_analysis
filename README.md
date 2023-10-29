
# Auditd Logs Analysis - Python Task

Software for analyzing changes in files under Linux, using logs created by Auditd rules. The software reads the log files, analyzes them and saves the result in the SQLite database.
There are built-in queries that can be used to check certain changes.


## Requirements:
- Ubuntu or anther linux OS (64 bit)
- Python 3.10.12 or later.
- Libraries: sqlite3, re, datetime, dotenv, os.
- Auditd
## Usage

In file audit_rules.txt has a list of rules. Make sure all the rules you want to check are configured according to the list. Note that the key of each rule must be exactly as listed for the software to function properly
If one or more of them are missing, run them from the terminal so the software can analyze them.
for example:
```
sudo auditctl -a always,exit -F arch=b64 -S open -S openat -F success=1 -k file-open-success

```

Execute the software in terminal:
```
python3 auditd_analysis.py
```

## Authors

- [@YosiStern](https://www.github.com/YosiStern)

