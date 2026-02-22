
# README

## Overview
This project loads two JSON inputs (`data_blocks.json` and `family_tree.json`), flattens the nested `familyTreeMembers` list, enriches each company with its parent DUNS, and writes the final dataset to `output.parquet`.

## How to Run
1. Install requirements:
```bash
pip install -r requirements.txt
```
2. Place input files under `data/<case>/data_blocks.json` and `data/<case>/family_tree.json`.
3. Run:
```bash
python pipeline.py
```
4. Output:
```
output.parquet
```

## Testing
Run the unit test:
```bash
python -m pytest -q
```

## Project Files
- `pipeline.py` – main script
- `test_pipeline.py` – single pytest test
- `requirements.txt`
- `.gitignore`


## Notes for Upscaling
The function used to load the jsons in this project is already capable of receiving more sources (e.g. companyD, companyE, etc.)
without the need to change anything in the code.

Nevertheless, in case the volume of data increases noteably, one solution would be to stream the json files using ijson and process
the results in chunks.

Similarly to what is already done with the results of the family_tree json, the data_blocks dataframe can also be filtered in order 
to only keep the relevant columns.

On the output side, if the resulting dataframe is very big, the parquet can be partitioned and written to a directory, instead of
being a single file. 