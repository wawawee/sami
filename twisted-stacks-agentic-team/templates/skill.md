# Skill Template (agentskills.io compliant)

## Metadata
- **skill_id**: `[unique-identifier]` (e.g., `web-research-v1`)
- **name**: `[Human-readable skill name]`
- **description**: `[Brief description of what the skill does]`
- **version**: `1.0.0`
- **created**: `YYYY-MM-DD`
- **updated**: `YYYY-MM-DD`
- **author**: `[Agent ID or creator]`
- **tags**: `[keyword1, keyword2, ...]`
- **models**: `[list of compatible models]` (optional)
- **dependencies**: `[list of required skills or tools]` (optional)

## Parameters
[Define the input parameters for the skill]
```json
{
  "param1": {
    "type": "string|number|boolean|array|object",
    "description": "What this parameter is for",
    "required": [true/false],
    "default": [default value if not required],
    "enum": [["option1", "option2"]] (optional for strings)
  },
  "param2": { ... }
}
```

## Return Value
[Define what the skill returns]
```json
{
  "result": {
    "type": "string|number|boolean|array|object",
    "description": "What the result represents"
  },
  "metadata": {
    "type": "object",
    "description": "Additional information about the execution"
  }
}
```

## Side Effects
[List any side effects of executing this skill]
- May make external HTTP requests
- May modify files in `[directory]`
- May consume API credits
- May create temporary files
- May send notifications

## Performance
- **Average Execution Time**: `[time]` (e.g., 2.5s)
- **Token Cost**: `[estimate]` (e.g., 150 tokens)
- **Success Rate**: `[percentage]` (e.g., 95%)
- **Retry Count**: `[number]` (e.g., 3)

## Usage Example
[Show how to use the skill in agent code]
```python
# Pseudocode for using this skill
result = await use_skill(
    "skill-id",
    {
        "param1": "value1",
        "param2": 42
    }
)

# Handle the result
if result.success:
    # Process result.data
    pass
else:
    # Handle error
    pass
```

## Implementation Notes
[Any special considerations for implementing or using this skill]
- Requires specific API keys or credentials
- Works best with certain model types
- Has known limitations in `[scenario]`
- Should be combined with `[other skill]` for best results

## Changelog
- **1.0.0** (YYYY-MM-DD): Initial release
- **0.1.0** (YYYY-MM-DD): Prototype version

## Related Skills
- `[skill-id]`: [Brief description of relationship]
- `[skill-id]`: [Brief description of relationship]

## References
- [Link to documentation or source]
- [Link to related research or standards]