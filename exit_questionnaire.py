from __future__ import print_function
# Generate an Exit Questionnaire for NegNeg Reports
# Documentation for Gel Report Models is available: http://gelreportmodels.genomicsengland.co.uk

# import libraries
from protocols.reports_3_0_0 import RareDiseaseExitQuestionnaire as EQ
from protocols.reports_3_0_0 import FamilyLevelQuestions as FLQs
import argparse, os, requests, sys, re
import datetime
from pprint import pprint

def valid_date(s):
    """Checks that entered data is in the correct format"""
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def parser_args():
    """Parse arguments from the command line"""
    parser = argparse.ArgumentParser(
        description='Generates an Exit Questionnaire for NegNeg reports and sends via CIP API')
    parser.add_argument(
        '-reporter', '-r', nargs=1,
        help='Name of user who is generating the report, in the format "Firstname Surname"',
        required=True, type=str)
    parser.add_argument(
        '-date', '-d', nargs=1,
        help='Date in YYYY-MM-DD format recorded in Exit Questionnaire as process date, defaults to current date.',
        required=False, type=valid_date)
    parser.add_argument(
        '-interpretation_request', '-i', nargs='+',
        help='Interpretation request ID including version number, in the format 11111-1',
        required=True)
    return parser.parse_args()

args = parser_args()
# Parse arguments form the command line
reporter = args.reporter[0] # Name of user generating report (Firstname Surname)
current_date = datetime.datetime.today()
selected_date = args.date[0] # In "YYYY-MM-DD" format. If date not specified will default to current_date.

# Sanity check on entered date:
if selected_date > current_date:
    sys.exit("Selected_date is in the future, please check value entered.\n")
elif selected_date < (current_date - datetime.timedelta(days=365)): # Ensure date entered is within last year
    sys.exit("Selected_date is in the distant past, please check value entered.\n")
 
interpretation_request = args.interpretation_request[0]

# Check format of request_id matches expected format:
if bool(re.match(r"^\d+-\d+$", interpretation_request)) == False:
    sys.exit("Interpretation request ID doesn't match the format 11111-1, please check entry")
else:
    # If correctly formated split intertation_request on '-' and allocate to request_id, request_version
    request_id, request_version = interpretation_request.split('-')

# Check that reporter is entered correctly by checking against config.json file of valid reporters:
# TODO Write code to check reporter is correct + create json file of expected inputs

# Step 1) Create exit questionnaire payload:

# instantiate FamilyLevelQuestions (FLQs)
flqs = FLQs(
    # Hard coded entries appropriate for Neg Neg reports (NOTE LOWER case "no")
    caseSolvedFamily = "no", 
    segregationQuestion = "no",
    additionalComments = "No tier 1 or 2 variants detected",
)

# Validate flqs object
if flqs.validate(flqs.toJsonDict()) == False:
    # pprint(flqs.toJsonDict()) # Prints flqs for debugging
    # Print error message with list of non-valid fields:
    print("Invalid flqs object created as described below:\n")
    print(flqs.validate(flqs.toJsonDict(), verbose=True).messages)
    sys.exit()

# instantiate ExitQuestionnaire (EQ)
eq = EQ(
    eventDate=str(selected_date), # Convert from datetime to str
    reporter=reporter,
    familyLevelQuestions=flqs,
    variantGroupLevelQuestions=[],
)

# Validate eq object
if eq.validate(eq.toJsonDict()) == False:
    # Print error message with list of non-valid fields:
    #pprint(eq.toJsonDict())) # Prints eq for debugging
    print("Invalid eq object created as described below:\n")
    print(eq.validate(eq.toJsonDict(), verbose=True).messages)
    sys.exit()

# Step 2) Once the Exit Questionnaire payload is ready send via the CIP API:

# `get_authenticated_header` is a simple method for authenticating your credentials with
#  the CIP API, which will return you authenticated headers to supply with your HTTP requests.

# TODO add JellyPy authentication
# JellyPy/pyCIPAPI/auth.py

# def get_authenticated_header(url, username):
    
#     url += "{endpoint}"
#     auth_endpoint = "get-token/"
#     import getpass
#     password = getpass.getpass()

#     irl_response = requests.post(
#         url=url.format(endpoint=auth_endpoint),
#         json=dict(
#             username=username,
#             password=password,
#         ),
#     )
#     irl_response_json = irl_response.json()
#     token = irl_response_json.get('token')

#     auth_header = {
#         'Accept': 'application/json',
#         "Authorization": "JWT {token}".format(token=token),
#     }
#     return auth_header


# # You will be prompted to enter your CIP API password here
# # TODO replace with code to add API token access

# import requests
# cip_api_url = "https://cipapi-test-tng.gel.zone/api/2/"
# auth_header = get_authenticated_header(url=cip_api_url, username="glever")
# # TODO remove hardcoded user

# # ???????????????????????
# """
# GET /api/2/interpretation-request/{ir_id}/{ir_version}/ 
# """
# endpoint = "interpretation-request/{ir_id}/{ir_version}/".format(
#         ir_id=2, ir_version=2,
# )
# url = cip_api_url + endpoint
# print(url)

# response = requests.get(url=url, headers=auth_header)

# # Check ????
# response.json().keys()

# # Check ????
# len(response.json().get("clinical_report"))


# # ????????????????????????
# """
# PUT /api/2/exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/ 
# """
# endpoint = "exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/".format(
#         ir_id=2, ir_version=2, clinical_report_version=1
# )
# url = cip_api_url + endpoint
# print(url)

# response = requests.put(url=url, headers=auth_header, json=eq.toJsonDict())

# # check status code
# response.status_code

# # check status content
# response.content

# new_eq = EQ.fromJsonDict(response.json().get("exit_questionnaire_data"))

# new_eq.validate(new_eq.toJsonDict())

