#!/usr/bin/python3
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

def check_date(_d):
    """Sanity check on the entered date"""
    current_date = datetime.datetime.today()
    if _d > current_date:
        sys.exit("Selected_date is in the future, please check value entered.\n")
    elif _d < (current_date - datetime.timedelta(days=365)): # Ensure date entered is within last year
        sys.exit("Selected_date is in the distant past, please check value entered.\n")
    

# Check format of request_id matches expected format:
def get_request_details(_id):
    """Check the format of the entered Interpretation request ID and version number"""
    if bool(re.match(r"^\d+-\d+$", _id)) == False:
        sys.exit("Interpretation request ID doesn't match the format 11111-1, please check entry")
    else:
        # If correctly formated split intertation_request on '-' and allocate to request_id, request_version
        request_id, request_version = _id.split('-')
    return request_id, request_version

# Check that reporter is entered correctly by checking against config.json file of valid reporters:
# TODO Write code to check reporter is correct + create json file of expected inputs

def create_flq():
    """instantiate FamilyLevelQuestions (FLQs)"""
    flqs = FLQs(
        # Hard coded entries appropriate for Neg Neg reports (NOTE LOWER case "no")
        caseSolvedFamily = "no", 
        segregationQuestion = "no",
        additionalComments = "No tier 1 or 2 variants detected",
    )
    return flqs

def validate_flqs(_flqs):
    """Validate flqs object"""
    if  _flqs.validate(_flqs.toJsonDict()) == False:
        # pprint(flqs.toJsonDict()) # Prints flqs for debugging
        # Print error message with list of non-valid fields:
        print("Invalid flqs object created as described below:\n")
        print(_flqs.validate(_flqs.toJsonDict(), verbose=True).messages)
        sys.exit()

def create_eq(_selected_date, _reporter, _flqs):
    """instantiate ExitQuestionnaire (EQ)"""
    eq = EQ(
        eventDate=str(_selected_date), # Convert from datetime to str
        reporter=_reporter,
        familyLevelQuestions=_flqs,
        variantGroupLevelQuestions=[],
    )
    return eq

def validate_eq(_eq):
    """Validate eq object"""
    if _eq.validate(_eq.toJsonDict()) == False:
        # Print error message with list of non-valid fields:
        #pprint(eq.toJsonDict())) # Prints eq for debugging
        print("Invalid eq object created as described below:\n")
        print(_eq.validate(_eq.toJsonDict(), verbose=True).messages)
        sys.exit()


# TODO add JellyPy authentication
# See  https://github.com/NHS-NGS/JellyPy/blob/master/pyCIPAPI/auth.py

# AuthenticatedCIPAPISession()

cip_api_url = "https://cipapi-test-tng.gel.zone/api/2/" # TODO add as commandline arg

def get_case():
    """GET /api/2/interpretation-request/{ir_id}/{ir_version}/"""
    endpoint = "interpretation-request/{ir_id}/{ir_version}/".format(
            ir_id=2, ir_version=2,
    )
    url = cip_api_url + endpoint
    print(url)
    try:
        response = requests.get(url=url, headers=auth_header)
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("Undefined Error:",err)
    if response.status_code != 200:
        SystemExit("Function get_case response.status_code != 200 indicating error")

    # Check ????
    response.json().keys()

    # Check ????
    len(response.json().get("clinical_report"))

def put_case():
    """PUT /api/2/exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/ """
    
    endpoint = "exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/".format(
            ir_id=2, ir_version=2, clinical_report_version=1
    )
    url = cip_api_url + endpoint
    print(url)

    # response = requests.put(url=url, headers=auth_header, json=eq.toJsonDict())

    # check status code
    if response.status_code != 200:
        SystemExit("Function put_case response.status_code != 200 indicating error")

    # check status content
    response.content

    new_eq = EQ.fromJsonDict(response.json().get("exit_questionnaire_data"))

    new_eq.validate(new_eq.toJsonDict())

def main():
    args = parser_args()
    # Parse arguments form the command line
    reporter = args.reporter[0] # Name of user generating report (Firstname Surname)
    selected_date = args.date[0] # In "YYYY-MM-DD" format. If date not specified will default to current_date.
    # Sanity check on entered date
    check_date(selected_date)
    interpretation_request = args.interpretation_request[0]
    # Split interpretation_request into request_id & request_version
    request_id, request_version = get_request_details(interpretation_request)
    # Create Exit Questionnaire payload
    flqs = create_flq()
    validate_flqs(flqs)
    eq = create_eq(selected_date, reporter, flqs)
    validate_eq(eq)
    # Send the Exit Questionnaire payload via the CIP API:
    # get_case()
    put_case()

if __name__ == '__main__':
    main()


