from utils.data_validator import validate_all_files

report = validate_all_files('data/')
print("PASSED:", report['passed'])
print("FAILED:", report['failed'])
print("WARNINGS:", report['warnings'])
print("STATUS:", report['overall_status'])