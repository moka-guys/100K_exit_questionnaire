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
from protocols.reports_6_0_0 import InterpretedGenome
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
        help='CIP-API user name of person who is generating the report, normally in the format "jbloggs"',
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
    """Sanity check that entered date seems reasonable: must not be in future or distant past (>1 year ago)"""
    current_date = datetime.datetime.today()
    if _date > current_date:
        sys.exit("Selected_date is in the future, please check value entered.\n")
    elif _date < (current_date - datetime.timedelta(days=365)):  # Ensure date entered is within last year
        sys.exit("Selected_date is in the distant past (>365 days), please check value entered.\n")


def get_request_details(_irid):
    """Check the format of the entered Interpretation request ID and version number"""
    # Regex to check that entered value is digits separated by -
    if bool(re.match(r"^\d+-\d+$", _irid)) == False:
        sys.exit("Interpretation request ID doesn't match the format 11111-1, please check entry")
    else:
        # If correctly formatted split interpretation_request on '-' and allocate to request_id, request_version
        request_id, request_version = _id.split('-')
    return request_id, request_version

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
    """Create, populate and return an ExitQuestionnaire (EQ) object from GelReportModels."""
    eq = EQ(
        eventDate=_selected_date,
        reporter=_reporter,
        familyLevelQuestions=_flqs,
        variantGroupLevelQuestions=[],
    )
    return eq


def validate_object(_object, _str_object_type):
    """Validates an flqs, eq or cr object using inbuilt validate method and produces an informative error message if non-valid object"""
    # The GelReportModel objects have a validate method. This checks that required fields are completed, data types are correct etc.
    # First you call the toJsonDict method to produce a JSON dictionary from the object
    # Then you pass this JSON dictionary to the validate method.
    # Using verbose=True allows you to pull out failure reason if it fails validation
    if _object.validate(_object.toJsonDict()) == False:
        # Print error message with list of non-valid fields:
        print("Invalid {} object created as described below:".format(_str_object_type))
        sys.exit(_object.validate(_object.toJsonDict(), verbose=True).messages)


def create_cr(_reporter, _date, _ir_id, _ir_version, _genome_assembly, _software_version):
    """Create Summary of Findings"""

    cr = ClinicalReport_6_0_0(interpretationRequestId=_ir_id,
                                interpretationRequestVersion=int(_ir_version), 
                                interpretationRequestAnalysisVersion='1',
                                reportingDate=_date,
                                user=_reporter,
                                variants= [],
                                structuralVariants=[],
                                genomicInterpretation="No tier 1 or 2 variants detected",
                                referenceDatabasesVersions={"genomeAssembly": _genome_assembly},
                                softwareVersions=_software_version,
                                supportingEvidence=[],
                                shortTandemRepeats=[],
                                references=[],      
                                )
    return cr


def put_case(ir_id, full_ir_id, ir_version,cip_api_url, eq, cr, testing_on=False):
    """
    Submit clinical report (aka summary of findings) and exit questionnaire to CIP-API.
    Args:
        ir_id = interpretation request ID without version number e.g. 12345
        ir_version = interpretation request version number e.g. 1
        full_ir_id = both of above plus the cip prefix e.g SAP-12345-1
        cip_api_url = base url to the cip api (to which specific endpoints will be added)
        eq = completed exit questionnaire object
        cr = completed clinical report object 
        testing_on = setting to True will authenticate using beta endpoint rather than live
    """
    # Create endpoint from user supplied variables ir_id and ir_version (hardcoded clinical_report_version 1 is OK
    # because script checks no other clinical reports have been generated before calling this function:
    eq_endpoint = "exit-questionnaire/{ir_id}/{ir_version}/{clinical_report_version}/?reports_v6=true".format(
        ir_id=ir_id, ir_version=ir_version, clinical_report_version=1
    )

    cr_endpoint = "clinical-report/genomics_england_tiering/raredisease/{full_ir_id}/?reports_v6=true".format(
        full_ir_id = full_ir_id)
  
    # Create urls for uploading exit questionnaire and summary of findings 
    exit_questionnaire_url = cip_api_url + eq_endpoint
    summary_of_findings_url = cip_api_url + cr_endpoint

    # Open Authenticated CIP-API session:
    gel_session = AuthenticatedCIPAPISession(testing_on=testing_on)

    # Upload Summary of findings:
    
    response = gel_session.post(url=summary_of_findings_url, json=cr.toJsonDict())
    if not (response.status_code == 200 or response.status_code ==201):
        print("CIP-API response code {r}".format(r =response.status_code))
        sys.exit("Function put_case response.status_code != 200 or 201 indicating error: Summary of Findings creation failed")
    
    # Upload exit questionnaire:
    response = gel_session.put(url=exit_questionnaire_url, json=eq.toJsonDict())
    if not (response.status_code == 200 or response.status_code ==201):
        print("CIP-API response code {r}".format(r =response.status_code))
        sys.exit("Function put_case response.status_code != 200 or 201 indicating error: Exit Questionnaire upload failed")


def main():
    parsed_args = parser_args()
    # Parse arguments from the command line
    reporter = parsed_args.reporter[0]  # CIP-API user name when generating the clinical report.
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
    ir_json = get_interpretation_request_json(request_id, request_version, reports_v6=True, testing_on=parsed_args.testing)
   
    # Check whether summary of findings already exists before preceding:
    if len(ir_json.get("clinical_report")) > 0:
        sys.exit("Processing interpretation request {} cancelled as clinical report already exists, please investigate and process manually".format(interpretation_request))

    # Parse interpretation request data for required fields
    try:
        genome_build = ir_json.get('assembly')  # Parse genome assembly from ir_json - genomeAssemblyVersion
        full_ir_id = ir_json.get('case_id') 
        # extract the pipeline software versions from genomics_england_tiering interpreted genome for adding to the summary of findings:
        interpreted_genomes = ir_json['interpreted_genome']
        for ig in interpreted_genomes:
            ig_obj = InterpretedGenome.fromJsonDict(ig['interpreted_genome_data'])
            cip = ig_obj.interpretationService.lower()
            if cip == 'genomics_england_tiering':
                software_versions = ig_obj.softwareVersions

    except KeyError as e:
        sys.exit(f'I got a KeyError when parsing ir_json, {str(e)}')
    except Exception as e:
        sys.exit(f'Exception thrown generating ir_json to parse for genome assembly, {str(e)}')
        

    # Create Exit Questionnaire payload
    flqs = create_flq()
    validate_object(flqs, "Family Level Questions")
    eq = create_eq(selected_date, reporter, flqs)
    validate_object(eq, "Exit Questionnaire")
    # print(json.dumps(eq.toJsonDict())) # For debugging
    
    # Create Summary of Findings
    cr = create_cr(reporter, selected_date, request_id, request_version, genome_build, software_versions)
    validate_object(cr, "Summary of Findings")
    # print(json.dumps(cr.toJsonDict())) # For debugging

    # Submit the Exit Questionnaire and summary of findings payload via the CIP API:
    put_case(request_id, full_ir_id, request_version, cip_api_url, eq, cr, testing_on=parsed_args.testing)

if __name__ == '__main__':
    main()
