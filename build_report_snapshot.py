#!/usr/bin/env python3
"""Materialize artifact.json snapshot datasets into a queryable SQLite file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def sqlite_type(values: list[object]) -> str:
    present = [value for value in values if value is not None]
    if not present:
        return "TEXT"
    if all(isinstance(value, (bool, int)) for value in present):
        return "INTEGER"
    if all(isinstance(value, (bool, int, float)) for value in present):
        return "REAL"
    return "TEXT"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    datasets = artifact["snapshot"]["datasets"]
    with sqlite3.connect(args.output) as connection:
        for table_name, rows in datasets.items():
            columns: list[str] = []
            for row in rows:
                for column in row:
                    if column not in columns:
                        columns.append(column)
            connection.execute(f"DROP TABLE IF EXISTS {quote(table_name)}")
            definitions = ", ".join(
                f"{quote(column)} {sqlite_type([row.get(column) for row in rows])}"
                for column in columns
            )
            connection.execute(f"CREATE TABLE {quote(table_name)} ({definitions})")
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {quote(table_name)} VALUES ({placeholders})",
                [[row.get(column) for column in columns] for row in rows],
            )
        connection.commit()


if __name__ == "__main__":
    main()
