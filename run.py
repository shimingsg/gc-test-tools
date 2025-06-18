from cargo.common import RunCommand, push_dir
from cargo.logger import setup_loggers
from sys import argv
from typing import List, Any
from argparse import ArgumentParser
from individual.constants import INDIVIDUAL_TESTS, TEST_BINARIES_ROOT,CLR_BINARIES_ROOT
from individual.common import parse_test_results, combine_test_result_path
# from pathlib import Path

def __process_args(args: List[str]) -> Any:
    '''Processes command-line arguments and returns the first argument.'''
    if not args:
        raise ValueError('No arguments provided.')
    
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
    
    return parser.parse_args(args)

def __get_repo_update(repo_root: str, verbose: bool = True) -> None:
    cmdlines = [
        ['git', 'pull'],
        ['git', 'log', '-1', '--pretty=format:%H']
    ]
    with push_dir(repo_root):
        for cmdline in cmdlines:
            RunCommand(cmdline, verbose=verbose).run()

def __build_clr_libs(repo_root: str, verbose: bool = True) -> None:
    cmdlines =[
        ['build.cmd', '-s', 'clr+libs', '-c', 'Release', '-rc', 'Checked'],
        [rf'src\tests\build.cmd', 'generatelayoutonly', 'Checked']
    ]
    with push_dir(repo_root):
        for cmdline in cmdlines:
            RunCommand(cmdline, verbose=verbose).run()

def __build_gc_individual_tests(repo_root: str, verbose: bool = True) -> None:
    build_tool = rf'.dotnet\dotnet.exe'
    individual_test_projects = [
        r'src\tests\GC\GC.csproj', 
        r'src\tests\GC\Features\GC-features.csproj',
        r'src\tests\GC\Scenarios\GC-scenarios1.csproj',
        r'src\tests\GC\Scenarios\GC-simulator.csproj']
    
    for project in individual_test_projects:
        cmdline = [build_tool, 'build', '-c', 'Release', project]
        print(f'Running command: {cmdline}')
        RunCommand(cmdline, verbose=verbose).run()
    print('GC Individual Tests built successfully.')    

def __main(argv: List[str]) -> None:
    args = __process_args(argv)
    setup_loggers(verbose=args.verbose)
    if args.all_actions:
        args.update_repo = True
        args.build_clr_libs = True
        args.build_tests = True
        args.run_tests = True
        
    with push_dir(args.repo_root):
        if args.update_repo:
            print(f'Updating the runtime repository in {args.repo_root}')
            __get_repo_update(args.repo_root)
        
        if args.build_clr_libs:
            print(f'Building the runtime in {args.repo_root}')
            __build_clr_libs(args.repo_root)
                   
        if args.build_tests:
            print(f'Building the GC Individual Tests in {args.repo_root}')
            __build_gc_individual_tests(args.repo_root)
        
        if args.run_tests:
            # Run the GC Individual Tests
            print('Running the GC Individual Tests...')
            coreroot = rf'{args.repo_root}\{CLR_BINARIES_ROOT}\Tests\Core_Root'

            test_result = []
            re_run_test_result = []
            for test in INDIVIDUAL_TESTS:
                cmdline = [test[1], '-coreroot', coreroot]
                print(f'Running command: {cmdline}')
                RunCommand(cmdline, verbose=True).run()
            
                # Analyze the results
                print('Analyzing the test results...')
                test_summary = parse_test_results(combine_test_result_path(test[1]))
                test_result.append((test[0], test_summary))
                if test_summary['failed_test_names']:
                    for failed_test in test_summary['failed_test_names']:
                        print(f'Failed Test: {failed_test} in {test[0]}')
                        # re-run the failed tests
                        print(f"Failed Tests in {test[1]}: {', '.join(test_summary['failed_test_names'])}")
                        cmdline = [rf'{TEST_BINARIES_ROOT}\{failed_test}', '-coreroot', coreroot]
                        print(f'Re-running failed tests with command: {cmdline}')
                        returncode = RunCommand(cmdline, verbose=True).run()
                        if returncode != 0:
                            print(f'Failed to re-run test: {failed_test}')
                        else:
                            print(f'Successfully re-ran test: {failed_test}')
                        
                        re_run_test_result.append([test[0], failed_test, returncode])
               

            
if __name__ == '__main__':
    __main(argv[1:])