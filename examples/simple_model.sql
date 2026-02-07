/** @moddoc
A simple example model demonstrating inline documentation.

This model shows the basic usage of @moddoc for model-level documentation
and @coldoc for column-level documentation.
**/

select
  1 as id /** @coldoc The unique identifier **/,
  'Alice' as name /** @coldoc The user's name **/,
  25 as age /** @coldoc The user's age in years **/,
  'alice@example.com' as email /** @coldoc The user's email address **/
