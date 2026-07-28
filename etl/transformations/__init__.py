"""Transformation engine — applies reusable transformations to DataFrames.

Supports: rename, drop, filter, fill, convert, calculate, join, split, merge, sort, deduplicate, standardize.
Each transformation is defined by a config dict with 'type' and type-specific parameters.
"""

import pandas as pd


class TransformationEngine:
    """Applies a sequence of transformations to a DataFrame."""

    TRANSFORMATIONS = {
        "rename",
        "drop",
        "filter",
        "fill",
        "convert",
        "calculate",
        "join",
        "split",
        "merge",
        "sort",
        "deduplicate",
        "standardize",
    }

    def apply(self, df: pd.DataFrame, transformations: list[dict]) -> pd.DataFrame:
        """Apply a list of transformations in order.

        Args:
            df: Input DataFrame.
            transformations: List of transformation config dicts.

        Returns:
            Transformed DataFrame.
        """
        for t in transformations:
            t_type = t.get("type")
            if t_type not in self.TRANSFORMATIONS:
                raise ValueError(f"Unknown transformation type: '{t_type}'")
            df = self._apply_one(df, t)
        return df

    def apply_single(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        return self._apply_one(df, config)

    def _apply_one(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        t_type = config["type"]
        handler = getattr(self, f"_t_{t_type}")
        return handler(df, config)

    def _t_rename(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        mapping = config.get("mapping", {})
        return df.rename(columns=mapping)

    def _t_drop(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        columns = config.get("columns", [])
        return df.drop(columns=columns, errors="ignore")

    def _t_filter(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        column = config["column"]
        op = config.get("operator", "eq")
        value = config.get("value")
        ops = {
            "eq": lambda s: s == value,
            "ne": lambda s: s != value,
            "gt": lambda s: s > value,
            "lt": lambda s: s < value,
            "ge": lambda s: s >= value,
            "le": lambda s: s <= value,
            "in": lambda s: s.isin(value),
            "not_in": lambda s: ~s.isin(value),
            "isnull": lambda s: s.isnull(),
            "notnull": lambda s: s.notnull(),
            "contains": lambda s: s.astype(str).str.contains(str(value), case=False, na=False),
        }
        mask = ops[op](df[column])
        return df[mask]

    def _t_fill(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        column = config["column"]
        method = config.get("method", "value")
        if method == "value":
            df[column] = df[column].fillna(config.get("value"))
        elif method == "mean":
            df[column] = df[column].fillna(df[column].mean())
        elif method == "median":
            df[column] = df[column].fillna(df[column].median())
        elif method == "mode":
            df[column] = df[column].fillna(
                df[column].mode().iloc[0] if not df[column].mode().empty else None
            )
        elif method == "ffill":
            df[column] = df[column].ffill()
        elif method == "bfill":
            df[column] = df[column].bfill()
        return df

    def _t_convert(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        column = config["column"]
        target_type = config["to"]
        if target_type in ("int", "integer"):
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype("int64")
        elif target_type in ("float", "decimal"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        elif target_type in ("str", "string"):
            df[column] = df[column].astype(str)
        elif target_type == "datetime":
            df[column] = pd.to_datetime(df[column], errors="coerce")
        elif target_type == "bool":
            df[column] = df[column].astype(bool)
        return df

    def _t_calculate(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        new_col = config["new_column"]
        expression = config["expression"]
        df[new_col] = df.eval(expression)
        return df

    def _t_join(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        right_df = config["right_df"]
        on = config.get("on")
        how = config.get("how", "left")
        return df.merge(right_df, on=on, how=how)

    def _t_split(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        column = config["column"]
        delimiter = config.get("delimiter", ",")
        new_columns = config.get("new_columns", [])
        parts = df[column].astype(str).str.split(delimiter, expand=True)
        for i, col_name in enumerate(new_columns):
            if i < parts.shape[1]:
                df[col_name] = parts[i]
        return df

    def _t_merge(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        columns = config["columns"]
        new_column = config["new_column"]
        separator = config.get("separator", " ")
        df[new_column] = df[columns].astype(str).agg(separator.join, axis=1)
        return df

    def _t_sort(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        by = config.get("by", [])
        ascending = config.get("ascending", True)
        return df.sort_values(by=by, ascending=ascending)

    def _t_deduplicate(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        subset = config.get("subset")
        keep = config.get("keep", "first")
        return df.drop_duplicates(subset=subset, keep=keep)

    def _t_standardize(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        column = config["column"]
        operation = config.get("operation", "trim")
        ops = {
            "trim": lambda s: s.str.strip(),
            "lower": lambda s: s.str.lower(),
            "upper": lambda s: s.str.upper(),
            "title": lambda s: s.str.title(),
            "strip_non_alnum": lambda s: s.str.replace(r"[^a-zA-Z0-9\s]", "", regex=True),
        }
        if operation in ops:
            df[column] = ops[operation](df[column].astype(str))
        return df
