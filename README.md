# 100K_exit_questionnaire v 1.0

## What does this script do?
Script is designed to be used in processing 100k Neg Neg reports - programatically creates Exit Questionnaire payloads and sends them to the CIP API.  

## What are typical use cases for this script?
The script is run during the generation of 100k Neg Neg reports.

## What data are required for this script to run?

A valid interpretation request ID and reporter name need to be provided. 

## What does this script output?

This script outputs a log file.

## How does this script work?

The script builds an exit questionnaire using Gel Models and then the Exit Questionnaire payload is sent to the CIP API.  The code is based upon this workshop [code](https://github.com/genomicsengland/ACGS_GeL_API_workshop/blob/master/Exit_Questionnaire_Workshop/WORKSHOP.ipynb)  

## What are the limitations of this script

This script imports functions from GelReportModels:
```git
git clone git@github.com:genomicsengland/GelReportModels.git
cd GelReportModels
pip install .
```
It also uses https://github.com/NHS-NGS/JellyPy/blob/master/pyCIPAPI/auth.py to programmatically provide authentication when connecting to the CIP API.

Authentication credentials are stored in auth_credentials.py and are in
        dictionary format:
        ```python
        auth_credentials = {"username": "username", "password": "password"}
```
This script reads in a json file named ????? listing valid reporter names which it uses to validate inputs.

## Testing 

Generating the Exit Questionnaire is covered by tests in tests_generate_eq.py
```bash
pytest tests_generate_eq.py
```
Coverage reports can be generated using:

```bash
# Create coverage report
exit_questionnaire.py -r "John Smith" -i 11111-1 -d 2019-02-19
# View coverage report
coverage report
```

## This script was made by Viapath Genome Informatics

