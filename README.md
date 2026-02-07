# dbt-inline-docs

> *Write inline Javadoc-style dbt model & column docs (no more separate YAML files!)*

**Status:** MVP implementation complete! ✅

Advantages:
 - Reduce risk of docs getting out of sync with implementation by keeping documentation next to the code.
 - Reduce repetition by specifying model/column names in only one place.
 - Simplify your dbt project structure by eliminating separate YAML files for basic documentation.

Original prototype described at [dbt-labs/dbt-core#5093 (comment)](https://github.com/dbt-labs/dbt-core/discussions/5093#discussioncomment-3159441).

## Installation

```bash
pip install dbt-inline-docs
```

The plugin is automatically discovered by dbt when installed. No configuration needed!

## Usage

### Model Documentation with `@moddoc`

Add a `/** @moddoc ... */` comment at the top of your SQL file to document the model:

```sql
-- file: models/my_model.sql

/** @moddoc
This is my super cool model! It does cool things!

Have as many lines as you want. The description supports **markdown** formatting.
**/

select
  id,
  name,
  email
from {{ ref('raw_users') }}
```

### Column Documentation with `@coldoc`

Add a `/** @coldoc ... */` comment after a column to document it:

```sql
select
  id /** @coldoc The unique identifier for the user **/,
  name /** @coldoc The user's full name **/,
  age /** @coldoc The user's age in years **/
from {{ ref('raw_users') }}
```

The plugin automatically detects the column name from the SQL identifier before the comment.

### Complete Example

```sql
-- file: models/users.sql

/** @moddoc
This model cleans and standardizes user data from the raw users table.

It performs the following transformations:
- Normalizes email addresses to lowercase
- Calculates age from birth_date
- Filters out test accounts
**/

select
  id /** @coldoc Primary key for the users table **/,
  lower(email) as email /** @coldoc Normalized email address **/,
  concat(first_name, ' ', last_name) as full_name /** @coldoc 
    User's full name, concatenated from first and last name.
    
    Multi-line descriptions are supported!
  **/,
  date_diff('year', birth_date, current_date) as age /** @coldoc Calculated age in years **/
from {{ ref('raw_users') }}
where is_test_account = false
```

## Current Features (MVP)

- ✅ **Model descriptions** via `@moddoc` comments
- ✅ **Column descriptions** via `@coldoc` comments  
- ✅ **Automatic column name detection** from SQL
- ✅ **Multi-line descriptions** with markdown support
- ✅ **Parse-time integration** - works with full dbt workflow

## Roadmap (Future Features)

- [ ] Support for YAML properties after `---` separator (tests, tags, meta, etc.)
- [ ] Support for macros documentation
- [ ] Support for `@sourcedoc` for sources
- [ ] Schema validation for inline properties
- [ ] IDE autocomplete support

## How It Works

The plugin hooks into dbt's parsing phase via the `ManifestLoader.process_docs` method. It:

1. Scans all SQL files for `@moddoc` and `@coldoc` comments
2. Extracts descriptions using regex pattern matching
3. Injects the descriptions into the dbt manifest before compilation
4. Works seamlessly with existing dbt workflows (`dbt run`, `dbt docs generate`, etc.)

## Vision (Original Prototype)

```sql
-- file: mymodel.sql

/** @moddoc
This is my super cool model! It does cool things!

Have as many lines as you want.

You can even define tests and other model properties too by adding `---` on a line of its own,
then specifying yaml properties, except for:
- `name`, which is automatically set to the model name; and
- `description`, which is pulled from this comment itself (up to and excluding a standalone `---` line).
**/

select
  ... as my_cool_column /** @coldoc
    This is my description of a cool column in my model. This whole paragraph gets extracted into a
    yaml file as the description for the column.

    Similar to the top-level @moddoc, you can define *column* tests and other column properties by
    adding `---` on a line of its own, then specifying yaml properties for the column, except for:
     - `name`, which is automatically pulled from the SQL identifier just before this comment; and
     - `description`, which is pulled from the comment itself (up to and excluding a standalone `---` line).

    ---
    data_type: text
    data_tests:
    - not_null
    - accepted_values
        arguments:
          values: ["Cool", "Cooler", "Coolest"]
  **/
  ... 
```
