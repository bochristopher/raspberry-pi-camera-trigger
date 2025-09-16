# Contributing to Raspberry Pi Camera Trigger System

We welcome contributions to this project! This document provides guidelines for contributing.

## Development Setup

### Prerequisites

- Raspberry Pi with Raspberry Pi OS Bookworm
- Python 3.9 or higher
- Git

### Local Development

1. **Fork and clone the repository:**
```bash
git clone https://github.com/your-username/camera-trigger.git
cd camera-trigger
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install development dependencies:**
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock black flake8 isort bandit safety
```

4. **Run tests:**
```bash
./scripts/test.sh
```

### Development Workflow

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
```bash
# Run all tests
./scripts/test.sh

# Test dry-run mode
python main.py --dry-run --trigger-test

# Run specific tests
python -m pytest tests/test_hardware.py -v
```

4. **Format and lint code:**
```bash
# Format code
black src/ main.py

# Sort imports
isort src/ main.py

# Run linter
flake8 src/ main.py
```

5. **Commit and push:**
```bash
git add .
git commit -m "Add feature: your feature description"
git push origin feature/your-feature-name
```

6. **Create a Pull Request**

## Code Style

### Python Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 127 characters
- Use type hints where appropriate

### Documentation Style

- Use docstrings for all classes and functions
- Follow Google-style docstrings
- Keep README.md up to date
- Add inline comments for complex logic

### Example Function Documentation

```python
def capture_frame(self, method: str = "opencv") -> Optional[Dict[str, Any]]:
    """
    Capture a frame using specified method

    Args:
        method: Capture method ("opencv" or "fswebcam")

    Returns:
        Dictionary containing image data and metadata, or None if failed

    Raises:
        RuntimeError: If camera is not initialized
    """
```

## Testing

### Test Categories

1. **Unit Tests** (`tests/test_*.py`)
   - Test individual components
   - Use mocking for hardware dependencies
   - Fast execution

2. **Integration Tests**
   - Test component interactions
   - Use dry-run mode for hardware simulation

3. **Hardware Tests**
   - Test actual hardware functionality
   - Run on target hardware only

### Writing Tests

- Use pytest framework
- Mock external dependencies
- Test both success and failure cases
- Aim for high test coverage

### Example Test

```python
def test_mock_sensor_initialization(self):
    """Test mock sensor initializes correctly"""
    sensor = MockLIS3DHSensor()
    result = sensor.initialize()

    self.assertTrue(result)
    self.assertTrue(sensor.is_connected())
```

## Security Considerations

### Code Security

- Never commit secrets or credentials
- Use proper error handling to avoid information leakage
- Validate all inputs
- Follow secure coding practices

### Hardware Security

- Ensure proper access control for hardware interfaces
- Use secure communication protocols
- Implement proper authentication and authorization

## Issue Reporting

### Bug Reports

Please include:

- Operating system and version
- Python version
- Hardware configuration
- Steps to reproduce
- Expected vs actual behavior
- Log output (with sensitive data removed)

### Feature Requests

Please include:

- Use case description
- Proposed solution
- Alternative approaches considered
- Impact on existing functionality

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Update documentation
3. Add appropriate test coverage
4. Follow code style guidelines
5. Rebase on latest main branch

### Pull Request Template

- **Description:** Brief description of changes
- **Type:** Bug fix / Feature / Documentation / etc.
- **Testing:** How you tested the changes
- **Checklist:**
  - [ ] Tests pass
  - [ ] Documentation updated
  - [ ] Code follows style guidelines
  - [ ] No breaking changes (or properly documented)

### Review Process

1. Automated CI checks must pass
2. Code review by maintainers
3. Security review for sensitive changes
4. Testing on target hardware if applicable

## Hardware Testing

### Required Hardware

For full testing, you need:

- Raspberry Pi 4 (recommended)
- LIS3DH accelerometer (I²C address 0x18)
- ATECC608 secure element (I²C address 0x60)
- DS3231 RTC (I²C address 0x68)
- USB UVC camera

### Test Procedure

1. **Wiring verification:**
```bash
sudo i2cdetect -y 1
# Should show devices at 0x18, 0x60, 0x68
```

2. **Camera test:**
```bash
fswebcam test.jpg
```

3. **Full system test:**
```bash
sudo ./scripts/setup.sh
sudo systemctl start camera-trigger
camera-trigger-status
```

## Release Process

### Version Numbering

We use Semantic Versioning (SemVer):

- MAJOR.MINOR.PATCH
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Test on target hardware
5. Create release tag
6. Update documentation
7. Publish release notes

## Getting Help

- **Documentation:** Check README.md and inline docs
- **Issues:** Search existing issues first
- **Discussion:** Use GitHub Discussions for questions
- **Security:** Report security issues privately

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow GitHub Community Guidelines

Thank you for contributing to this project!