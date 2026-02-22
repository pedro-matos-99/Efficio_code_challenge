import pandas as pd
import glob
import json
import logging
import re
import os

ROOT_DIR = "data"
OUT_PATH = "output.parquet"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("pipeline")

_DUNS_RE = re.compile(r"^\d+$")


"""
Validate the fomat of the DUNS - numeric without empty spaces
"""
def normalize_duns(x: str) -> str:
    if x is None:
        return None
    s = re.sub(r"\s+", "", str(x))
    return s if _DUNS_RE.match(s) else None


"""
Safely loading the json files, throwing decoding error if it happens
"""
def json_load(path: str) -> json:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning("Skipping malformed JSON: %s (%s)", path, e)
        return None
    except Exception as e:
        logger.error("Failed to read %s: %s", path, e, exc_info=True)
        return None
    

"""
Reads all the json files with the provided name inside the 'data' parent directory.
It normalizes the json so that it is then possible to convert it into a DataFrame.
"""
def ingest_json(filename: str) -> pd.DataFrame:
    files = glob.glob(f"{ROOT_DIR}/*/{filename}.json")
    if not files:
        logger.warning("No files found for %s under %s/*/", filename, ROOT_DIR)

    all_dfs = []
    for f in files:
        data = json_load(f)
        if data is None:
            continue
        try:
            df = pd.json_normalize(data)
            all_dfs.append(df)
        except Exception as e:
            logger.warning("Normalization failed for %s: %s", f, e)

    if not all_dfs:
        logger.error("No valid frames produced for %s", filename)
        return pd.DataFrame()

    df_complete = pd.concat(all_dfs, ignore_index=True)
    logger.info("Ingested %s: %d rows from %d file(s)", filename, len(df_complete), len(all_dfs))
    return df_complete


"""
Extracts a nested column inside a DataFrame.
"""
def extract_nested_df(df, column):
    if column not in df.columns:
        logger.error("Column '%s' not present; returning empty frame.", column)
        return pd.DataFrame()

    mask = df[column].apply(lambda v: isinstance(v, list))  # Only explodes if the column is a list
    if not mask.any():
        logger.warning("No list-like values to explode in '%s'; returning empty frame.", column)
        return pd.DataFrame()

    df_exploded = df.loc[mask].explode(column, ignore_index=True)

    try:
        final_df = pd.json_normalize(df_exploded[column], sep=".")
    except Exception as e:
        logger.error("json_normalize failed on '%s': %s", column, e, exc_info=True)
        return pd.DataFrame()

    return final_df



if __name__ == "__main__":
    # Ingest both sources
    df_data_blocks = ingest_json("data_blocks")
    df_family_tree = ingest_json("family_tree")

    # Script fails if one of the sources is empty
    if df_data_blocks.empty or df_family_tree.empty:
        logger.error("One of the sources is empty; aborting.")
        raise SystemExit(1)

    # Extract the family list
    df_family = extract_nested_df(df_family_tree, "familyTreeMembers")

    # Ensure DQ of duns fiedl (used in the merge)
    df_data_blocks["duns"] = df_data_blocks["duns"].map(normalize_duns)

    # Left merge: all from left, only relevant columns from right
    df_merged = df_data_blocks.merge(df_family[['duns', 'corporateLinkage.parent.duns']], on="duns", how="left")

    # Write parquet
    df_merged.to_parquet(OUT_PATH, index=False)
    logger.info("Wrote %s", os.path.abspath(OUT_PATH))