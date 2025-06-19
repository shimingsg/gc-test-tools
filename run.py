from cargo.common import RunCommand, push_dir
from cargo.logger import setup_loggers
from sys import argv
from typing import List, Any
from argparse import ArgumentParser
from individual.constants import INDIVIDUAL_TESTS, TEST_BINARIES_ROOT,CLR_BINARIES_ROOT,TEST_RESULTS
from individual.common import parse_test_results,generate_test_result_file_name
# from pathlib import Path
import os

def __process_args(args: List[str]) -> Any:
    '''Processes command line arguments and returns parsed arguments.
    param args: List of command line arguments.
    return: Parsed arguments as an object.
    Raises ValueError if no arguments are provided.'''
    if not args or len(args) == 0:
        raise ValueError('No arguments provided. Please provide the required arguments.')
    
    parser = ArgumentParser(
        description='GC Individual Tests warpper',
        allow_abbrev=False
    )
    
    parser.add_argument(
        '-r','--repo-root',
        required=True,
        type=str,
        help='runtime repository root directory',
    )
    
    parser.add_argument(
        '-v', '--verbose',
        required=False,
        default=False,
        action='store_true',
        help='Turns on verbosity (default "False")',
    )
    
    # update the runtime repository
    parser.add_argument(
        '-ur', '--update-repo',
        required=False,
        default=False,
        action='store_true',
        help='updates the runtime repository (default "False")',
    )
    
    # skip building the clr
    parser.add_argument(
        '-bcl', '--build-clr-libs',
        required=False,
        default=False,
        action='store_true',
        help='builds clr+libs in Release and Checked mode (default "False")',
    )
    
    # skip building the GC Individual Tests
    parser.add_argument(
        '-bt', '--build-tests',
        required=False,
        default=False,
        action='store_true',
        help='builds the GC Individual Tests (default "False")',
    )
    
    # run the GC Individual Tests
    parser.add_argument(
        '-rt', '--run-tests',
        required=False,
        default=False,
        action='store_true',
        help='runs the GC Individual Tests (default "False")',
    )
    
    # all actions enabled by default
    parser.add_argument(
        '-a', '--all-actions',
        required=False,
        default=False,
        action='store_true',
        help='enables all actions (default "False")',
    )
    
    #rerun the failed tests
    parser.add_argument(
        '-rr', '--rerun-failed-tests',
        required=False,
        default=False,
        action='store_true',
        help='re-runs the failed tests (default "False")',
    )
    
    return parser.parse_args(args)

def __get_commit_hash(repo_root: str, verbose: bool = True) -> str:
    '''Gets the latest commit hash from the runtime repository.
    This function changes the current working directory to the repository root and runs the git log command.
    param repo_root: The root directory of the runtime repository.
    param verbose: If True, prints the command lines being executed.
    return: The latest commit hash as a string.
    '''
    cmdline = ['git', 'log', '-1', '--pretty=format:%H']
    return RunCommand(cmdline=cmdline, verbose=verbose).run_and_get_output(repo_root)
    
def __get_repo_update(repo_root: str, verbose: bool = True) -> None:
    '''Updates the runtime repository by pulling the latest changes from the remote repository.
    This function changes the current working directory to the repository root and runs the git pull command.
    param repo_root: The root directory of the runtime repository.
    param verbose: If True, prints the command lines being executed.
    '''
    cmdlines = [
        ['git', 'pull'],
        # ['git', 'log', '-1', '--pretty=format:%H']
    ]
    with push_dir(repo_root):
        for cmdline in cmdlines:
            RunCommand(cmdline, verbose=verbose).run()

def __build_clr_libs(repo_root: str, verbose: bool = True) -> None:
    '''Builds the CLR and libraries in Release and Checked mode.
    This function builds the CLR and libraries using the provided command lines.
    param repo_root: The root directory of the runtime repository.
    param verbose: If True, prints the command lines being executed.
    '''
    cmdlines =[
        ['build.cmd', '-s', 'clr+libs', '-c', 'Release', '-rc', 'Checked'],
        [rf'src\tests\build.cmd', 'generatelayoutonly', 'Checked']
    ]
    with push_dir(repo_root):
        for cmdline in cmdlines:
            RunCommand(cmdline, verbose=verbose).run()

def __build_gc_individual_tests(repo_root: str, verbose: bool = True) -> None:
    '''Builds the GC Individual Tests.
    This function builds the individual test projects specified in the `individual_test_projects` list.
    param repo_root: The root directory of the runtime repository.
    param verbose: If True, prints the command lines being executed.
    '''
    build_tool = rf'.dotnet\dotnet.exe'
    individual_test_projects = [
        r'src\tests\GC\GC.csproj', 
        r'src\tests\GC\Features\GC-features.csproj',
        r'src\tests\GC\Scenarios\GC-scenarios1.csproj',
        r'src\tests\GC\Scenarios\GC-simulator.csproj']
    with push_dir(repo_root):
        for project in individual_test_projects:
            cmdline = [build_tool, 'build', '-c', 'Release', project]
            print(f'Running command: {cmdline}')
            RunCommand(cmdline, verbose=verbose).run()
        print('GC Individual Tests built successfully.')    

def __run_gc_individual_tests(repo_root: str, verbose: bool = True) -> None:
    '''Runs the GC Individual Tests.
    This function assumes that the tests are built and available in the specified directory.
    param repo_root: The root directory of the runtime repository.
    param verbose: If True, prints the command lines being executed.
    '''
    coreroot = rf'{repo_root}\{CLR_BINARIES_ROOT}\Tests\Core_Root'
    with push_dir(repo_root):
        for test in INDIVIDUAL_TESTS:
            if test[0] == 'GC-simulator':
                # For GC-simulator, we need to set the environment variable
                # RunningGCSimulatorTests to 1 to run the simulator tests.
                os.environ['RunningGCSimulatorTests'] = '1'
            else:
                # os.environ['RunningGCSimulatorTests'] = ''
                os.environ.pop('RunningGCSimulatorTests')
            
            cmdline = [test[1], '-coreroot', coreroot]
            print(f'Running command: {cmdline}')
            RunCommand(cmdline, verbose=True).run()
        
# def __rerun_failed_tests(repo_root: str, run_name: str, coreroot: str, verbose: bool = True) -> None:

def __rerun_failed_tests(repo_root: str, testresult: str, coreroot: str, verbose: bool = True) -> None:
    """
    Re-runs failed tests and records the results in a Markdown file.
    """
    test_summary = parse_test_results(testresult)
    if not test_summary['failed_test_names']:
        print('No failed tests to re-run.')
        return

    re_run_test_result = []
    markdown_output = "# Failed tests:\n\n| Test name | Reproducible |\n|-----------|--------------|\n"

    for failed_test in test_summary['failed_test_names']:
        cmdline = [rf'{TEST_BINARIES_ROOT}\{failed_test}', '-coreroot', coreroot]
        print(f'Re-running failed test: {failed_test}')
        print(f'Re-running failed tests with command: {cmdline}')
        returncode = RunCommand(cmdline, verbose=True).run()
        
        reproducible = "TRUE" if returncode != 0 else "FALSE"
        markdown_output += f"| {failed_test} | {reproducible} |\n"
        
        re_run_test_result.append({'test_name': failed_test, 'reproducible': reproducible})
        if returncode != 0:
            print(f'Failed to re-run test: {failed_test}')
        else:
            print(f'Successfully re-ran test: {failed_test}')

    # Write results to a Markdown file
    output_file = os.path.join(repo_root, "rerun_results.md")
    with open(output_file, "w") as md_file:
        md_file.write(markdown_output)

    print(f'Re-run results saved to {output_file}')

def __analyze_test_results(test_result: str) -> dict:
    '''Analyzes the test results and returns a summary.'''
    test_summary = parse_test_results(test_result)
    if not test_summary:
        print(f'No test results found in {test_result}')
        return {}
    
    print(f'Test Summary for {test_result}:')
    print(f"Total Cases: {test_summary['total_cases']}")
    print(f"Passed Cases: {test_summary['passed_cases']}")
    print(f"Failed Cases: {test_summary['failed_cases']}")
    
    if test_summary['failed_test_names']:
        for failed_test in test_summary['failed_test_names']:
            print(f"Failed Test: {failed_test}")
    else:
        print('No failed tests.')
    
    return test_summary

def __summary(repo_root: str, verbose: bool = True) -> None:
    '''Generates a summary of the test results and writes it to a Markdown file.
    param repo_root: The root directory of the runtime repository.
    param verbose: If True, prints the command lines being executed.
    '''
    print('Generating summary of test results...')
    commit_hash = __get_commit_hash(repo_root, verbose=verbose)
    markdown_output = f'# GC Individual Tests Summary\n\nCommit Hash: {commit_hash}\n\n'
    markdown_output += "# Test Result:\n\n| Testset name | Number of tests | Passed | Failed |\n|--------------|-------|-------|-------|\n"
    markdown_output_failed_test = "# Failed tests:\n\n| Test name | Reproducible |\n|-----------|--------------|\n"
    with push_dir(repo_root):
        for result in TEST_RESULTS:
            if not os.path.exists(TEST_RESULTS[result]):
                print(f'Test result file {TEST_RESULTS[result]} does not exist.')
                markdown_output += f"| {result} | NA | NA | NA |\n"
                continue
            test_summary = parse_test_results(TEST_RESULTS[result])
            if not test_summary:
                print(f'No test results found in {test_summary}')
                markdown_output += f"| {result} | NA | NA | NA |\n"
                continue
            else:
                markdown_output += f"| {result} | {test_summary['total_cases']} | {test_summary['passed_cases']} | {test_summary['failed_cases']} |\n"
                
            if not test_summary['failed_test_names']:
                print('No failed tests to re-run.')
                continue
            for failed_test in test_summary['failed_test_names']:
                markdown_output_failed_test += f"| {failed_test} | TO DO |\n"

    markdown_output += "\n\n" + markdown_output_failed_test
    # Write results to a Markdown file
    output_file = generate_test_result_file_name()
    with open(output_file, "w") as md_file:
        md_file.write(markdown_output)
    print(f'Summary of test results saved to {output_file}')

def __main(argv: List[str]) -> None:
    '''Main function to run the GC Individual Tests wrapper.
    param argv: List of command line arguments.
    This function processes the command line arguments, sets up loggers, and calls the appropriate functions
    to update the repository, build CLR libraries, build tests, and run tests.
    It also generates a summary of the test results.
    Raises ValueError if no arguments are provided.
    '''
    args = __process_args(argv)
    setup_loggers(verbose=args.verbose)
    
    if args.all_actions:
        args.update_repo = True
        args.build_clr_libs = True
        args.build_tests = True
        args.run_tests = True
    
    if args.rerun_failed_tests:
        args.run_tests = False
        args.build_tests = False
        args.update_repo = False
        args.build_clr_libs = False
        
    if args.update_repo: __get_repo_update(args.repo_root)
    if args.build_clr_libs: __build_clr_libs(args.repo_root)
    if args.build_tests: __build_gc_individual_tests(args.repo_root)
    if args.run_tests: __run_gc_individual_tests(args.repo_root)
    # if args.rerun_failed_tests: __rerun_failed_tests(args.repo_root)
    
    __summary(args.repo_root)
    
if __name__ == '__main__':
    __main(argv[1:])