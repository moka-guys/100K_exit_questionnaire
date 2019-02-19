from __future__ import print_function
# Generate an Exit Questionnaire for NegNeg Reports
# Documentation for Gel Report Models is available: http://gelreportmodels.genomicsengland.co.uk
# TODO use mokaguys github
# TODO create pytest unit testing
# TODO create README.txt

# import libraries
from protocols.reports_3_0_0 import RareDiseaseExitQuestionnaire as EQ
from protocols.reports_3_0_0 import FamilyLevelQuestions as FLQs
import argparse, datetime, os, requests, sys

# Parse arguments from the command line:
def parser_args():
    parser = argparse.ArgumentParser(
        description='Generates an Exit Questionnaire for NegNeg reports and sends via CIP API')
    parser.add_argument(
        '-reporter', '-r', nargs='+',
        help='Name of user who is generating the report.',
        required=True)
    parser.add_argument(
        '-selected_date', '-d', nargs='+',
        help='Date in YYYY-MM-DD format recorded in Exit Questionnaire, defaults to current date.',
        required=False)
    # TODO add argument for comments
    return parser.parse_args()

# Parse arguments form the command line
reporter = "" # Name of user generating report
current_date = datetime.datetime.today().strftime('%Y-%m-%d')
selected_date = "" # In "YYYY-MM-DD" format. If date not specified will default to current_date.

# Sanity check on date:
if selected_date > current_date:
    sys.exit("Selected_date is in the future, please check value entered.\n")
elif selected_date < (current_date - timedelta(days=3650)): # Ensure date entered is within last decade
    sys.exit("Selected_date is in the distant past, please check value entered.\n")

# Check that reporter is entered correctly by checking against config.json file of valid reporters:
# TODO Create config generation file

# Step 1) Create exit questionnaire payload

# instantiate FamilyLevelQuestions (FLQs)
flqs = FLQs(
    # Hard coded entries appropriate for Neg Neg reports
    caseSolvedFamily = "no",
    segregationQuestion = "no",
    additionalComments = "No tier 1 or 2 variants detected",
)

# Validate flqs object
if flqs.validate(flqs.toJsonDict()) == False:
    # Print error message with list of non-valid fields:
    sys.exit(''.join("Invalid flqs object created:\n", 
    flqs.validate(flqs.toJsonDict(), verbose=True).result,"\n",
     pprint(flqs.toJsonDict()))

# instantiate ExitQuestionnaire (EQ)
eq = EQ(
    eventDate=selected_date,
    reporter="Greg Lever",
    familyLevelQuestions=flqs,
    variantGroupLevelQuestions=[],
)

# Validate eq object
if eq.validate(eq.toJsonDict()) == False:
    # Print error message with list of non-valid fields:
    sys.exit("Invalid flqs object created:\n" +
    flqs.validate(flqs.toJsonDict(), verbose=True).result + "\n" +
    pprint(eq.toJsonDict()))

# Step 2) Once the Exit Questionnaire payload is ready send via the CIP API:

# `get_authenticated_header` is a simple method for authenticating your credentials with
#  the CIP API, which will return you authenticated headers to supply with your HTTP requests.

# TODO add JellyPy authentication
# JellyPy/pyCIPAPI/auth.py
def get_authenticated_header(url, username):
    
    url += "{endpoint}"
    auth_endpoint = "get-token/"
    import getpass
    password = getpass.getpass()

    irl_response = requests.post(
        url=url.format(endpoint=auth_endpoint),
        json=dict(
            username=username,
            password=password,
        ),
    )
    irl_response_json = irl_response.json()
    token = irl_response_json.get('token')

    auth_header = {
        'Accept': 'application/json',
        "Authorization": "JWT {token}".format(token=token),
    }
    return auth_header


# You will be prompted to enter your CIP API password here
# TODO replace with code to add API token access

import requests
cip_api_url = "https://cipapi-test-tng.gel.zone/api/2/"
auth_header = get_authenticated_header(url=cip_api_url, username="glever")
# TODO remove hardcoded user

# ???????????????????????
"""
GET /api/2/interpretation-request/{ir_id}/{ir_version}/ 
"""
endpoint = "interpretation-request/{ir_id}/{ir_version}/".format(
        ir_id=2, ir_version=2,
)
url = cip_api_url + endpoint
print(url)

response = requests.get(url=url, headers=auth_header)

# Check ????
response.json().keys()

# Check ????
len(response.json().get("clinical_report"))


# ????????????????????????
"""
PUT /api/2/exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/ 
"""
endpoint = "exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/".format(
        ir_id=2, ir_version=2, clinical_report_version=1
)
url = cip_api_url + endpoint
print(url)

response = requests.put(url=url, headers=auth_header, json=eq.toJsonDict())

# check status code
response.status_code

# check status content
response.content

new_eq = EQ.fromJsonDict(response.json().get("exit_questionnaire_data"))

new_eq.validate(new_eq.toJsonDict())

