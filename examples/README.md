# Examples

This directory contains example SQL files demonstrating the usage of dbt-inline-docs.

## Example 1: Simple Model with Inline Docs

File: `simple_model.sql`

Shows basic usage of `@moddoc` and `@coldoc` for a simple model.

## Example 2: Complex Model

File: `complex_model.sql`

Demonstrates multi-line descriptions, multiple columns, and various SQL patterns.

## Testing the Examples

To test these examples in a real dbt project:

1. Create a new dbt project or use an existing one
2. Install dbt-inline-docs: `pip install dbt-inline-docs`
3. Copy the example SQL files to your `models/` directory
4. Run `dbt parse` to verify the plugin extracts the documentation
5. Check the manifest: `cat target/manifest.json | jq '.nodes[] | select(.name=="simple_model")'`
6. Generate docs: `dbt docs generate && dbt docs serve`
