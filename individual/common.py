import xml.etree.ElementTree as ET
from individual.constants import TEST_RESULT_EXTENSION
from cargo.common import get_root_path
from os import path, makedirs
from time import time
from datetime import datetime

def generate_test_result_file_name() -> str:
    '''Generates a unique log file name for the current script.'''
    test_result_dir = path.join(get_root_path(), 'test_results')
    makedirs(test_result_dir, exist_ok=True)

    timestamp = datetime.fromtimestamp(time()).strftime("%Y%m%d%H%M%S")
    test_result_file_name = f'{timestamp}-test-summary.md'
    return path.join(test_result_dir, test_result_file_name)

def combine_test_result_path(test_name: str) -> str:
    return test_name[:-4] + TEST_RESULT_EXTENSION
    # return os.path.join(os.path.dirname(os.path.realpath(test_name)), test_result_file)

def parse_test_results(xml_file: str):
    """
    Parses the test results XML file and extracts test summary.

    Args:
        xml_file (str): Path to the test results XML file.

    Returns:
        dict: A dictionary containing total cases, passed cases, failed cases, and failed test case names.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    summary = {
        "total_cases": 0,
        "passed_cases": 0,
        "failed_cases": 0,
        "failed_test_names": []
    }

    # Iterate through assemblies and collections to gather test data
    for assembly in root.findall("assembly"):
        summary["total_cases"] += int(assembly.get("total", 0))
        summary["passed_cases"] += int(assembly.get("passed", 0))
        summary["failed_cases"] += int(assembly.get("failed", 0))

        # Find failed tests and collect their names
        for test in assembly.findall(".//test[@result='Fail']"):
            summary["failed_test_names"].append(test.get("name"))

    return summary