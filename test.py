import os
from individual.common import parse_test_results, combine_test_result_path
from cargo.common import push_dir


INDIVIDUAL_TESTS =[
    ['GC', rf'artifacts\tests\coreclr\windows.x64.Release\GC\GC\GC.cmd'],
    ['GC-features', rf'artifacts\tests\coreclr\windows.x64.Release\GC\Features\GC-features\GC-features.cmd'],
   ]

if __name__ == '__main__':
    # Example usage
    os.environ.pop('RunningGCSimulatorTests', None)
    
    # with push_dir(r'd:\repos\runtime'):
    #     for test in INDIVIDUAL_TESTS:
    #         test_result_path = combine_test_result_path(test[1])
    #         print(f'Test result path: {test_result_path}')
    #         test_summary = parse_test_results(test_result_path)
    #         print(f'Test Summary for {test[1]}:')
    #         print(f"Total Cases: {test_summary['total_cases']}")
    #         print(f"Passed Cases: {test_summary['passed_cases']}")
    #         print(f"Failed Cases: {test_summary['failed_cases']}")
    #         if test_summary['failed_test_names']:
    #             for failed_test in test_summary['failed_test_names']:
    #                 print(f"Failed Test: {failed_test}")
    #             # print(f"Failed Test Names: {', '.join(test_summary['failed_test_names'])}")
    #         else:
    #             print('No failed tests.')
    
     