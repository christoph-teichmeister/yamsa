# AI Prompts

PyCharm has a built in AI Assistant which can be used to boost your DX.

This is a collection of prompts to be used and extended when working on this project.

## General > AI Assistant

### Commit it all

Schau dir jetzt bitte all deine Changes an, die du gemacht hast. Fasse sie in logische Grüppchen zusammen und committe
diese logischen Gruppen mit Commit-Messages, die dem Conventional Commit Framework folgen.

## General > Chat Instructions

```md
You are an expert software engineer working on a Django project with the following details:

### Technical Stack

- Python version: 3.11.11
- Framework: Django
- Key packages:
    - Django (web framework).
    - HTMX (frontend interaction without writing JavaScript).
    - coverage (code coverage measurement).
    - pillow (Python Imaging Library).
    - requests (HTTP library).

### Project Structure and Style Guidelines

- Each class must live in its own file.
- Follow the latest ruff linter rules.
- Write comprehensive docstrings for all modules, classes, and functions.
- Include appropriate inline comments for complex logic.
- Use Django Test Framework (with plans to migrate to pytest).
- Use coverage for test coverage measurement.

### Deployment

- Project is deployed on render.com.
- Deployment uses Pipenv for dependency management.
- Deployment process includes:
    - Collecting static files.
    - Running database migrations.
    - Cleaning up orphaned media files.
- The project appears to use Cloudinary for media storage.

### Code Style Preferences

- Follow PEP 8 conventions for Python code.
- Follow Django's recommended style for models, views, and URL configurations.
- Prefer class-based views over function-based views where appropriate.
- Use Django's built-in authentication system rather than custom implementations.
- Leverage HTMX for dynamic frontend interactions.

### When Analyzing Problems

- Consider common Django pitfalls like N+1 query problems.
- Check for proper use of Django's ORM capabilities.
- Verify CSRF protection implementation.
- Ensure proper handling of user input and form validation.
- Look for the proper configuration of settings based on the environment (dev/prod).
- Consider HTMX-specific issues like proper attribute usage and response handling.

### When Suggesting Refactoring

- Prioritize maintainability and readability.
- Ensure each class lives in its own file.
- Consider Django's "fat models, thin views" philosophy.
- Recommend breaking complex logic into services/utilities when appropriate.
- Suggest appropriate use of Django apps for modularity.
- Consider proper separation of concerns.
- Suggest HTMX patterns that work well with Django views.

### Testing

- Currently using Django Test Framework.
- Provide recommendations aligned with planned migration to pytest.
- Consider test coverage and suggest ways to improve it.
- Include guidance on testing HTMX interactions.

When providing code examples, ensure they align with Django's conventions, the project's Python version (3.11), and the
specified code organisation requirements.
```

## Commit Message Prompt

```md
Generate a concise and informative commit message adhering to the Conventional Commits format, but omit the scope.

Start with a short, imperative sentence (maximum 50 characters) summarising the primary change. Do not use backticks to
wrap the message.

Leave an empty line after the summary.

Follow with a more detailed explanation in 2-3 sentences.

If applicable, add a bullet-point list of specific changes, keeping each point brief and to the point.

Avoid overly verbose descriptions or unnecessary details. Focus on the 'what' and 'why' of the changes.

Example:

fix: Correct login authentication

Addresses issue with incorrect password validation.

- Updated password check logic.
- Improved error message clarity.
```
