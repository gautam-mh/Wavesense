# Contributing to Wavesense

Thank you for considering contributing to Wavesense! Your help is greatly appreciated. Please follow these guidelines to ensure a smooth contribution process.

## How to Contribute

1. **Fork the Repository**
   - Click the "Fork" button at the top right of the repository page.

2. **Clone Your Fork**
   - Clone your fork to your local machine:
     ```bash
     git clone https://github.com/your-username/wavesense.git
     cd wavesense
     ```

3. **Create a Branch**
   - Create a new branch for your feature or bugfix:
     ```bash
     git checkout -b feature/your-feature-name
     ```

4. **Make Your Changes**
   - Write clear, well-documented code.
   - Add or update tests as needed.
   - Ensure your code follows the existing style and conventions.

5. **Test Your Changes**
   - Run all tests to make sure nothing is broken.
   - For Python code, use `pytest` or `unittest` if available.
   - For ESP32 code, use PlatformIO's test runner if applicable.

6. **Commit and Push**
   - Commit your changes with a descriptive message:
     ```bash
     git add .
     git commit -m "Add feature: ..."
     git push origin feature/your-feature-name
     ```

7. **Open a Pull Request**
   - Go to the GitHub page for your fork and click "Compare & pull request".
   - Describe your changes and link any related issues.

## Code of Conduct

Please be respectful and considerate in all interactions. See the [Contributor Covenant](https://www.contributor-covenant.org/) for guidelines.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with as much detail as possible.

## Style Guide

- Use clear, descriptive variable and function names.
- Add docstrings and comments where necessary.
- Follow PEP8 for Python code.
- Keep commits focused and atomic.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project. 