# Test Report Naming Convention

## Format
All test reports follow this naming pattern:
```
phase_<phase>_<type>_<version>_<description>.md
```

## Components

### Phase
- `phase_1`: Foundation (database models, basic setup)
- `phase_2`: Authentication (user management, JWT)
- `phase_3`: Analytics (data analysis features)
- `phase_4`: CLI (command-line interface)
- `phase_4a`: CLI Implementation
- `phase_4b`: CLI Testing & Refinement
- `phase_4c`: NLP Integration
- `phase_4d`: Political Analysis Features

### Type
- `foundation`: Core infrastructure tests
- `authentication`: Auth system tests
- `analytics`: Data analysis tests
- `cli`: Command-line interface tests
- `nlp`: Natural language processing tests
- `political`: Political analysis tests
- `execution`: Test execution reports
- `improvement`: Iterative improvement reports
- `validation`: Real-world validation tests
- `analysis`: Test analysis and findings
- `results`: Test results summaries
- `summary`: Phase summary reports
- `security`: Security audit reports

### Version
- `v1`, `v2`, `v3`, etc.: Sequential version numbers
- Higher numbers indicate later iterations or refinements

### Description
- Brief descriptor of the report's focus
- Examples: `initial_test`, `final_test`, `enhancement_report`, `real_data_test`

## Examples
- `phase_1_foundation_v1_initial_test.md` - First foundation tests
- `phase_4b_cli_v3_enhanced_test.md` - Third iteration of CLI tests with enhancements
- `phase_4d_validation_v10_real_data_test.md` - Real-world data validation tests
- `misc/security_v1_environment_audit.md` - Security audit of environment configuration

## Benefits
1. **Chronological Ordering**: Files naturally sort by phase and version
2. **Clear Purpose**: Type and description immediately convey report content
3. **Version Tracking**: Easy to see iteration history
4. **Consistent Structure**: Predictable naming across all phases

## Migration Notes
- Timestamps have been removed from filenames but preserved within report content
- Reports are now organized by logical progression rather than creation date
- All 31 existing reports successfully renamed on 2025-07-02
