import pytest
import sys
import datetime

sys.path.append('/home/graeme/Desktop/100k_exit_questionnaire')
import exit_questionnaire

def test_check_date():
    """Test that dates in the distant past cannot be submitted"""
    with pytest.raises(SystemExit):
        exit_questionnaire.check_date(datetime.datetime.strptime("2017-01-01", "%Y-%m-%d"))
        exit_questionnaire.check_date(datetime.datetime.strptime("1971-11-11", "%Y-%m-%d"))
        exit_questionnaire.check_date(datetime.datetime.strptime("3001-01-01", "%Y-%m-%d"))
        
def test_get_request_details():
    # These tests should NOT raise SystemExit
    exit_questionnaire.get_request_details("12345-1")
    exit_questionnaire.get_request_details("10000-11")
    exit_questionnaire.get_request_details("11112345-3")
    # These tests should raise SystemExit
    with pytest.raises(SystemExit):
        exit_questionnaire.get_request_details("12345")
        exit_questionnaire.get_request_details("-")
        exit_questionnaire.get_request_details("12345-qw")
        exit_questionnaire.get_request_details("sd-12")
        exit_questionnaire.get_request_details("ahfuefs")
    

# def test_date_validator():
#     #with pytest.raises(ValueError):
#         #exit_questionnaire.valid_date("AAAAA")
#     with pytest.raises(SystemExit):
#         exit_questionnaire.valid_date("AAAAA")

