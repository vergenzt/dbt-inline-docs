"""
Functions which will have to hook into dbt project *parsing* in order to extract [model
properties](https://docs.getdbt.com/reference/model-properties) which are specified in @*doc
comments.
"""

import re
from dataclasses import dataclass
from typing import Optional


# Regex patterns for finding doc comments
# Matches: /** @moddoc or /** @coldoc
# Captures content between the tag and the closing **/
DOC_COMMENT_PATTERN = re.compile(
    r'/\*\*\s*@(moddoc|coldoc)\s+(.*?)\*+/',
    re.DOTALL | re.MULTILINE
)

# Pattern to find column name before a coldoc comment
# Matches identifiers (including after 'as') near the end of text
# Not using MULTILINE so $ only matches end of string
COLUMN_NAME_PATTERN = re.compile(
    r'(?:as\s+)?(\w+)\s*$',
    re.IGNORECASE
)


@dataclass
class DocComment:
    """Represents a parsed documentation comment."""
    tag: str  # 'moddoc' or 'coldoc'
    description: str
    column_name: Optional[str] = None  # Only for coldoc
    yaml_properties: Optional[str] = None  # For future use


def extract_description(content: str) -> str:
    """
    Extract the description part from doc comment content.
    Description is everything before a standalone '---' line (if present).
    """
    lines = content.strip().split('\n')
    description_lines = []
    
    for line in lines:
        # Stop at separator line
        if line.strip() == '---':
            break
        description_lines.append(line)
    
    # Join and clean up the description
    description = '\n'.join(description_lines).strip()
    return description


def parse_doc_comments(sql: str) -> list[DocComment]:
    """
    Parse all @moddoc and @coldoc comments from raw SQL.
    
    Returns a list of DocComment objects with extracted information.
    """
    results = []
    
    # Find all doc comments
    for match in DOC_COMMENT_PATTERN.finditer(sql):
        tag = match.group(1)  # 'moddoc' or 'coldoc'
        content = match.group(2)  # Everything after the tag
        
        description = extract_description(content)
        
        doc_comment = DocComment(
            tag=tag,
            description=description
        )
        
        # For coldoc, try to find the column name
        if tag == 'coldoc':
            # Look backwards from the comment position to find column name
            sql_before = sql[:match.start()]
            
            # Take only the last ~50 chars which should be the immediate column definition
            # This avoids matching identifiers from earlier in the SQL
            relevant_text = sql_before[-50:]
            
            # Look for the last identifier, optionally after 'as'
            # This handles: "col_name " or "as col_name "
            column_match = COLUMN_NAME_PATTERN.search(relevant_text)
            
            if column_match:
                doc_comment.column_name = column_match.group(1)
        
        results.append(doc_comment)
    
    return results

