#!/usr/bin/python3

"""
v1.0 - GS 2019/04/18
Requirements:
    Python 3.6
    JellyPy
    GeL Report Models (v6 or higher)

usage: exit_questionnaire.py [-h] -

Generates an Exit Questionnaire and Summary of Findings payload for NegNeg Reports and uploads them via the CIP-API

optional arguments:
  -h, --help                    show this help message and exit
  -r, --reporter                name of report generator 
  -d, --date                    date of report
  -i, --interpretation_request  interpretation request ID
  -t, --testing                 Flag for using Beta data
"""

# import libraries
import argparse
import ast
import datetime
import os
import json
import re
import requests
import sys

# Documentation for Gel Report Models is available: http://gelreportmodels.genomicsengland.co.uk
from protocols.reports_6_0_0 import RareDiseaseExitQuestionnaire as EQ
from protocols.reports_6_0_0 import FamilyLevelQuestions as FLQs
from protocols.reports_6_0_0 import ClinicalReport as ClinicalReport_6_0_0
from pprint import pprint # Used for debugging

# JellyPy used for authentication
# See  https://github.com/NHS-NGS/JellyPy/blob/master/pyCIPAPI/auth.py
# Append JellyPy to python path, needed when running via paramiko from Windows
# sys.path.append(config.jellypy_path)
from pyCIPAPI.auth import AuthenticatedCIPAPISession
from pyCIPAPI.interpretation_requests import get_interpretation_request_list
from pyCIPAPI.interpretation_requests import get_interpretation_request_json


def valid_date(_date):
    """Checks that entered data is in the correct format"""
    try:
        return datetime.datetime.strptime(_date, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(_date)
        raise argparse.ArgumentTypeError(msg)


def parser_args():
    """Parse arguments from the command line"""
    parser = argparse.ArgumentParser(
        description='Generates an Exit Questionnaire for NegNeg reports and submits via CIP API')
    parser.add_argument(
        '-r', '--reporter', nargs=1,
        help='Name of person who is generating the report, in the format "Firstname Surname"',
        required=True, type=str)
    parser.add_argument(
        '-u', '--user_name', nargs=1,
        help='CIP-API user name which will be recorded in the report, normally in the format "jbloggs"',
        required=True, type=str)
    parser.add_argument(
        '-d', '--date', nargs=1,
        help='Date in YYYY-MM-DD format recorded in Exit Questionnaire as process date.',
        required=True, type=valid_date)
    parser.add_argument(
        '-t', '--testing',
        help='Flag to use the CIP-API Beta data during testing', action='store_true')
    parser.add_argument(
        '-i', '--interpretation_request', nargs=1,
        help='Interpretation request ID including version number, in the format 11111-1',
        required=True)

    return parser.parse_args()


def check_date(_date):
    """Sanity check on the entered date"""
    current_date = datetime.datetime.today()
    if _date > current_date:
        sys.exit("Selected_date is in the future, please check value entered.\n")
    elif _date < (current_date - datetime.timedelta(days=365)):  # Ensure date entered is within last year
        sys.exit("Selected_date is in the distant past, please check value entered.\n")


def get_request_details(_id):
    """Check the format of the entered Interpretation request ID and version number"""
    # Regex to check that entered value is digits separated by -
    if bool(re.match(r"^\d+-\d+$", _id)) == False:
        sys.exit("Interpretation request ID doesn't match the format 11111-1, please check entry")
    else:
        # If correctly formatted split itertation_request on '-' and allocate to request_id, request_version
        request_id, request_version = _id.split('-')
    return request_id, request_version


# Check that reporter is entered correctly by checking against config.json file of valid reporters:
# TODO Write code to check reporter is correct + create json file of expected inputs

def create_flq():
    """instantiate FamilyLevelQuestions (FLQs) using GeL Report Models module"""
    flqs = FLQs(
        # Hard coded entries appropriate for Neg Neg reports (NOTE LOWER case "no")
        caseSolvedFamily="no",
        segregationQuestion="no",
        additionalComments="No tier 1 or 2 variants detected",
    )
    return flqs


def create_eq(_selected_date, _reporter, _flqs):
    """create ExitQuestionnaire (EQ)"""
    eq = EQ(
        eventDate=_selected_date,
        reporter=_reporter,
        familyLevelQuestions=_flqs,
        variantGroupLevelQuestions=[],
    )
    return eq


def validate_object(_object, _str_object_type):
    """Validates an flqs, eq or cr object and produces an informative error message if non-valid object"""
    if _object.validate(_object.toJsonDict()) == False:
        # Print error message with list of non-valid fields:
        print("Invalid {} object created as described below:".format(_str_object_type))
        sys.exit(_object.validate(_object.toJsonDict(), verbose=True).messages)


def create_cr(_user_name, _date, _ir_id, _ir_version, _genome_assembly, _software_version):
    """Create Summary of Findings"""

    cr = ClinicalReport_6_0_0(interpretationRequestId=_ir_id,
                                interpretationRequestVersion=int(_ir_version), 
                                interpretationRequestAnalysisVersion=_ir_version,
                                reportingDate=_date,
                                user=_user_name,
                                candidateVariants= [],
                                candidateStructuralVariants=[],
                                genomicInterpretation="No tier 1 or 2 variants detected",
                                referenceDatabasesVersions={"genomeAssembly": _genome_assembly},
                                softwareVersions=ast.literal_eval("{" + _software_version + "}"),
                                supportingEvidence=[]
                                )
    return cr


#TODO separate summary of findings and eq functions:
def put_case(ir_id, full_ir_id, ir_version,cip_api_url, eq, cr, testing_on=False):
    """PUT /api/2/exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/"""
    # Create endpoint from user supplied variables ir_id and ir_version: # TODO chnage ir_version dynamically 
    eq_endpoint = "exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/?reports_v6=true".format(
        ir_id=ir_id, ir_version=ir_version, clinical_report_version=1
    )
    cr_endpoint = "clinical-report/genomics_england_tiering/raredisease/{full_ir_id}}/?reports_v6=true"
        # TODO dynamically create cr_endpoint report ID (may need to query CIP-API to return GEL, CIP etc)
        # https://cipapi-beta.genomicsengland.co.uk/api/2/clinical-report/genomics_england_tiering/raredisease/GEL-23-1/

  
    # Create urls for uploading exit questionnaire and summary of findings 
    exit_questionnaire_url = cip_api_url + eq_endpoint
    summary_of_findings_url = cip_api_url + cr_endpoint

    # Open Authenticated CIP-API session:
    gel_session = AuthenticatedCIPAPISession(testing_on=testing_on)

    # Upload Summary of findings:
    response = gel_session.post(url=summary_of_findings_url, json=cr.toJsonDict())
    print(response.status_code)
    if response.status_code != 201:
        sys.exit("Function put_case response.status_code != 201 indicating error: Summary of Findings creation failed")

    # Download and check summary of findings:
    # response = gel_session.put(url=summary_of_findings_url, json=cr.toJsonDict())
    # TODO code to check downloaded cr
    
    # Upload exit questionnaire:
    response = gel_session.put(url=exit_questionnaire_url, json=eq.toJsonDict())
    if response.status_code != 200:
       sys.exit("Function put_case response.status_code != 200 indicating error: Exit Questionnaire upload failed")

    # Download and check exit questionnaire:
    # response = gel_session.put(url=exit_questionnaire_url, json=eq.toJsonDict())
    # TODO code to check downloaded eq


def main():
    parsed_args = parser_args()
    # Parse arguments from the command line
    reporter = parsed_args.reporter[0]  # Name of user generating report (Firstname Surname)
    user_name = parsed_args.user_name[0] # CIP-API user name when generating the clinical report. 
    selected_date = parsed_args.date[0]  # In "YYYY-MM-DD" format. If date not specified will default to current_date.
    check_date(selected_date) # Sanity check on entered date
    selected_date = selected_date.strftime("%Y-%m-%d") # Convert datetime to string for downstream functions
    interpretation_request = parsed_args.interpretation_request[0]
    request_id, request_version = get_request_details(interpretation_request) # Split into request_id & request_version
    # Set the CIP-API URL:
    if parsed_args.testing == False:
        cip_api_url = "https://cipapi.genomicsengland.nhs.uk/api/2/"
    else:
        cip_api_url = "https://cipapi-beta.genomicsengland.co.uk/api/2/"
        print("TESTING MODE active using the beta data at: {}".format(cip_api_url))  
    
    # Get interpretation request data from Interpretation Portal
    ir_json = get_interpretation_request_json(request_id, request_version, reports_v6=True, testing_on=True)
    # Parse interpretation request data for required fields

    try:
        genome_build = ir_json.get('assembly')  # Parse genome assembly from ir_json - genomeAssemblyVersion
        full_ir_id = ir_json.get('case_id') 
        # Some ugly code to get software versions from ir_json (I expected nested dictionary but got list of length 1 so I regexed for the data I needed)
        extracted_list =  str(ir_json['interpreted_genome'])
        pattern = re.compile('softwareVersions\': {(.*?)}')
        software_version = pattern.findall(extracted_list)[0]

        #print(ir_json.keys())
    except KeyError as e:
        sys.exit('I got a KeyError when parsing ir_json')
    except:
        print('Exception thrown generating ir_json to parse for genome assembly')
        raise

    # Create Exit Questionnaire payload
    flqs = create_flq()
    validate_object(flqs, "Family Level Questions")
    eq = create_eq(selected_date, reporter, flqs)
    validate_object(eq, "Exit Questionnaire")
    # print(json.dumps(eq.toJsonDict())) # For debugging
    # Create Summary of Findings
    cr = create_cr(user_name, selected_date, request_id, request_version, genome_build, software_version)
    validate_object(cr, "Summary of Findings")
    # print(json.dumps(cr.toJsonDict())) # For debugging

    # Submit the Exit Questionnaire and summary of findings payload via the CIP API:
    # put_case(request_id, request_version, cip_api_url, eq, cr, testing_on=parsed_args.testing)

if __name__ == '__main__':
    main()
    
