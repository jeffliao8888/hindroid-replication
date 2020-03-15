# dsc180a
How to run this project:  
python3 run.py [clean, data, process, data-test, test-project]  
- clean - removes the data directory
- data - downloads number apps specified in data-params.json
- process - performs project on full dataset. Uses data-params.json
- data-test - performs project on partial dataset. Uses test-parmas.json
- test-project - performs project on full dataset. Uses test-project.json

## Notes

- Process and data-test requires the data to already be present.
- test-project will streamline the whole process from downloading the data to saving the results.
