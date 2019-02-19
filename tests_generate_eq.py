import pytest
import sys
import datetime
import exit_questionnaire

# run 'pytest tests_generate_eq.py' on the commandline to run tests

def test_check_date():
    """Test that dates in the distant past or future correctly raise an error"""
    exit_questionnaire.check_date(datetime.datetime.today())
    with pytest.raises(SystemExit):
        exit_questionnaire.check_date(datetime.datetime.strptime("2017-01-01", "%Y-%m-%d"))
        exit_questionnaire.check_date(datetime.datetime.strptime("1971-11-11", "%Y-%m-%d"))
        exit_questionnaire.check_date(datetime.datetime.strptime("3001-01-01", "%Y-%m-%d"))
        
def test_get_request_details():
        """Tests that check on Interpretation request ID format is done correctly"""
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

def test_create_flq():
        """Tests that correctly configured FamilyLevelQuestions (FLQs) are created"""
        assert exit_questionnaire.create_flq().toJsonDict() == {u'additionalComments': 'No tier 1 or 2 variants detected', u'segregationQuestion': 'no', u'caseSolvedFamily': 'no'}
        exit_questionnaire.validate_flqs(exit_questionnaire.create_flq())

def test_create_eq():
        """Tests that correctly configured Exit Questionnaires are created"""
        assert exit_questionnaire.create_eq(datetime.datetime.today().date(), "Joe Bloggs", exit_questionnaire.create_flq()).toJsonDict() == {u'familyLevelQuestions': {u'additionalComments': 'No tier 1 or 2 variants detected', u'segregationQuestion': 'no', u'caseSolvedFamily': 'no'}, u'variantGroupLevelQuestions': [], u'eventDate': str(datetime.datetime.today().date()), u'reporter': 'Joe Bloggs'}
        exit_questionnaire.validate_eq( exit_questionnaire.create_eq(datetime.datetime.today().date(), "Joe Bloggs", exit_questionnaire.create_flq()))


