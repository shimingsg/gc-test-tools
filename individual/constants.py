CLR_CONFIGURATION = 'Checked'
LIBS_CONFIGURATION = 'Release'
TEST_BINARIES_ROOT = rf'artifacts\tests\coreclr\windows.x64.{LIBS_CONFIGURATION}'
CLR_BINARIES_ROOT = rf'artifacts\tests\coreclr\windows.x64.{CLR_CONFIGURATION}'
TEST_RESULT_EXTENSION = '.testResults.xml'
INDIVIDUAL_TESTS =[
    ['GC', rf'{TEST_BINARIES_ROOT}\GC\GC\GC.cmd'],
    # ['GC-features', rf'{TEST_BINARIES_ROOT}\GC\Features\GC-features\GC-features.cmd'],
    # ['GC-scenarios1', rf'{TEST_BINARIES_ROOT}\GC\Scenarios\GC-scenarios1\GC-scenarios1.cmd'],
    # ['GC-simulator', rf'{TEST_BINARIES_ROOT}\GC\Scenarios\GC-simulator\GC-simulator.cmd']
    ]