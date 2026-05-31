# Contributing

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the guidelines below
4. Run tests and linting: `make lint test`
5. Commit with conventional commits: `feat:`, `fix:`, `docs:`, `chore:`
6. Push and open a Pull Request

## Code Standards

- **Terraform**: Run `terraform fmt` and `terraform validate` before committing
- **Python**: Follow PEP 8, use Black formatter, type hints required
- **YAML**: Validate with `yamllint`
- **Shell**: Run `shellcheck` on all bash scripts

## Pull Request Guidelines

- Keep PRs focused and small — one concern per PR
- Include a description of what changed and why
- Reference any related issues
- All CI checks must pass before merge

## Reporting Issues

Use the issue templates provided. Include:
- Environment details
- Steps to reproduce
- Expected vs actual behavior

## Author

**Sai Babji Kommera** · saibabji1@gmail.com
