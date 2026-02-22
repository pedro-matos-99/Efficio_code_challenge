import pandas as pd
from pipeline import extract_nested_df

def test_parent_company():
    # Simulate data_blocks.json flattened output
    df_blocks = pd.DataFrame([
        {"duns": "690763115", "primaryName": "Microsoft Japan"},
        {"duns": "081466849", "primaryName": "Microsoft HQ"},
    ])

    # Simulate family_tree.json flattened output (just the familyTreeMembers)
    df_family_tree = pd.DataFrame({
        "familyTreeMembers": [[
            {
                "duns": "690763115",
                "corporateLinkage.parent.duns": "081466849"
            }
        ]]
    })

    df_family = extract_nested_df(df_family_tree, "familyTreeMembers")

    df_merged = df_blocks.merge(
        df_family[["duns", "corporateLinkage.parent.duns"]],
        on="duns",
        how="left"
    )

    # child must have parent
    child = df_merged[df_merged["duns"] == "690763115"].iloc[0]
    assert child["corporateLinkage.parent.duns"] == "081466849"

    # parent should have NaN
    parent = df_merged[df_merged["duns"] == "081466849"].iloc[0]
    assert pd.isna(parent["corporateLinkage.parent.duns"])