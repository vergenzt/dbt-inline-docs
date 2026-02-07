"""
Tests for the parse module that extracts inline documentation from SQL.
"""

from dbt_inline_docs.parse import parse_doc_comments, extract_description


def test_extract_description_simple():
    """Test extracting a simple description."""
    content = "This is a simple description"
    result = extract_description(content)
    assert result == "This is a simple description"


def test_extract_description_multiline():
    """Test extracting a multi-line description."""
    content = """This is a multi-line description.
    
It has multiple paragraphs."""
    result = extract_description(content)
    assert "multi-line description" in result
    assert "multiple paragraphs" in result


def test_extract_description_with_separator():
    """Test that description stops at --- separator."""
    content = """This is the description.

---
data_type: text
tests:
  - not_null"""
    result = extract_description(content)
    assert result == "This is the description."
    assert "data_type" not in result


def test_parse_moddoc():
    """Test parsing @moddoc comments."""
    sql = """
/** @moddoc
This is my model description.
**/

select 1 as id
"""
    comments = parse_doc_comments(sql)
    assert len(comments) == 1
    assert comments[0].tag == "moddoc"
    assert comments[0].description == "This is my model description."
    assert comments[0].column_name is None


def test_parse_coldoc_with_column_name():
    """Test parsing @coldoc comments with column name detection."""
    sql = """
select
  id /** @coldoc The unique identifier **/,
  name as user_name /** @coldoc The user's name **/
"""
    comments = parse_doc_comments(sql)
    assert len(comments) == 2
    
    # First column
    assert comments[0].tag == "coldoc"
    assert comments[0].column_name == "id"
    assert comments[0].description == "The unique identifier"
    
    # Second column
    assert comments[1].tag == "coldoc"
    assert comments[1].column_name == "user_name"
    assert comments[1].description == "The user's name"


def test_parse_multiple_comments():
    """Test parsing both @moddoc and @coldoc in the same file."""
    sql = """
/** @moddoc
My model description
**/

select
  col1 /** @coldoc Column 1 description **/,
  col2 /** @coldoc Column 2 description **/
from table1
"""
    comments = parse_doc_comments(sql)
    assert len(comments) == 3
    assert comments[0].tag == "moddoc"
    assert comments[1].tag == "coldoc"
    assert comments[2].tag == "coldoc"


def test_no_trailing_asterisks():
    """Test that trailing asterisks from */ are not captured."""
    sql = "select id /** @coldoc Test description **/"
    comments = parse_doc_comments(sql)
    assert len(comments) == 1
    # Should not have trailing asterisks
    assert not comments[0].description.endswith("*")
    assert comments[0].description == "Test description"


def test_multiline_coldoc():
    """Test multi-line column documentation."""
    sql = """
select
  status /** @coldoc
    The current status of the record.
    
    Can be: active, inactive, or pending.
  **/
"""
    comments = parse_doc_comments(sql)
    assert len(comments) == 1
    assert "current status" in comments[0].description
    assert "active, inactive" in comments[0].description


if __name__ == "__main__":
    # Run tests
    import sys
    
    tests = [
        test_extract_description_simple,
        test_extract_description_multiline,
        test_extract_description_with_separator,
        test_parse_moddoc,
        test_parse_coldoc_with_column_name,
        test_parse_multiple_comments,
        test_no_trailing_asterisks,
        test_multiline_coldoc,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
