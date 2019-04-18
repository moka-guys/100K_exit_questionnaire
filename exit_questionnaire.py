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
  -h, --help            show this help message and exit
  -r, --reporter 
  -d, --date
  -i, --interpretation_request
"""

# import libraries
import argparse
import datetime
import os
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
        '-r', '--reporter', nargs=1,
        help='Name of user who is generating the report, in the format "Firstname Surname"',
        required=True, type=str)
    parser.add_argument(
        '-d', '--date', nargs=1,
        help='Date in YYYY-MM-DD format recorded in Exit Questionnaire as process date, defaults to current date.',
        required=False, type=valid_date)
    parser.add_argument(
        '-i', '--interpretation_request', nargs='+',
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
        caseSolvedFamily="no",
        segregationQuestion="no",
        additionalComments="No tier 1 or 2 variants detected",
    )
    return flqs


def create_eq(_selected_date, _reporter, _flqs):
    """create ExitQuestionnaire (EQ)"""
    eq = EQ(
        eventDate=str(_selected_date),  # Convert from datetime to str
        reporter=_reporter,
        familyLevelQuestions=_flqs,
        variantGroupLevelQuestions=[],
    )
    return eq


def validate_object(_object, _str_object_type):
    """Validate an flqs, eq or cr object"""
    if _object.validate(_object.toJsonDict()) == False:
        # Print error message with list of non-valid fields:
        print("Invalid {} object created as described below:".format(_str_object_type))
        print(_object.validate(_object.toJsonDict(), verbose=True).messages)
        sys.exit()


def create_cr(_reporter, _date, _ir_id, _ir_version, _genome_assembly):
    """Create Summary of Findings"""

    cr = ClinicalReport_6_0_0(interpretationRequestId=_ir_id,
                                interpretationRequestVersion=int(_ir_version), 
                                interpretationRequestAnalysisVersion=_ir_version,
                                reportingDate=_date,
                                user=_reporter,
                                candidateVariants= [],
                                candidateStructuralVariants=[],
                                genomicInterpretation='No tier 1 or 2 variants detected',
                                referenceDatabasesVersions={'genomeAssembly': _genome_assembly},
                                softwareVersions={}
                                )
    return cr


def put_case(ir_id, ir_version,cip_api_url, eq, cr):
    """PUT /api/2/exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/ """

    endpoint = "exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/".format(
        ir_id=ir_id, ir_version=ir_version, clinical_report_version=1
    )
    url = cip_api_url + endpoint
    # print(url)

    gel_session = AuthenticatedCIPAPISession()
    response = gel_session.get(url=url, json=eq.toJsonDict())

    # check status code
    if response.status_code != 200:
        SystemExit("Function put_case response.status_code != 200 indicating error")

    # check status content
    response.content

    new_eq = EQ.fromJsonDict(response.json().get("exit_questionnaire_data"))

    new_eq.validate(new_eq.toJsonDict())


def main():
    parsed_args = parser_args()
    # Parse arguments from the command line
    reporter = parsed_args.reporter[0]  # Name of user generating report (Firstname Surname)
    selected_date = parsed_args.date[0]  # In "YYYY-MM-DD" format. If date not specified will default to current_date.
    # Sanity check on entered date
    check_date(selected_date)
    # Get the interpretation request info from command line
    interpretation_request = parsed_args.interpretation_request[0]
    # Split interpretation_request into request_id & request_version
    request_id, request_version = get_request_details(interpretation_request)
    # Get interpretation request data from Interpretation Portal
    ir_json = get_interpretation_request_json(request_id, request_version, reports_v6=True)
    # pprint(ir_json)
    # Parse genome assembly from ir_json
    genome_build = ir_json['assembly']
    # Create Exit Questionnaire payload
    flqs = create_flq()
    validate_object(flqs, "Family Level Questions")
    eq = create_eq(selected_date, reporter, flqs)
    validate_object(eq, "Exit Questionnaire")
    # Create Summary of Findings
    cr = create_cr(reporter, str(selected_date), request_id, request_version, genome_build)
    # pprint(cr.toJsonDict())
    validate_object(cr, "Summary of Findings")
    # Send the Exit Questionnaire payload via the CIP API:
    cip_api_url = "https://cipapi.genomicsengland.nhs.uk/interpretationportal/#/participant/"
    # put_case(request_id, request_version, cip_api_url, eq, cr)

if __name__ == '__main__':
    main()
