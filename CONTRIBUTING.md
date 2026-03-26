# Contributing Guidelines

This is an academic project created for a cloud computing assignment. While this is primarily a student project, feedback and suggestions are welcome!

## Code of Conduct

- Be respectful and constructive
- Focus on technical improvements
- Respect academic integrity

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists
2. Create a detailed issue report including:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

### Suggesting Enhancements

For feature suggestions:

1. Explain the use case
2. Describe the proposed solution
3. Consider impact on existing functionality
4. Discuss cost implications (for cloud features)

### Pull Requests

For code contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Update documentation
6. Submit pull request with clear description

## Development Setup

```bash
# Clone repository
git clone <repository-url>
cd autoscale-vm-cloud

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt

# Run tests
./scripts/setup.sh
```

## Code Style

- Python: Follow PEP 8
- Bash: ShellCheck compliant
- Comments: Clear and concise
- Documentation: Keep updated

## Testing

All changes should:

- Not break existing functionality
- Include appropriate tests
- Be documented
- Work within budget constraints

## Questions?

For questions or discussions, please open an issue.

Thank you for your interest in improving this project!
