# 🤝 Contributing to Tsukuyomi

We welcome contributions from the community! This project aims to be a high-performance, scalable simulation engine for multi-agent systems.

## 🚀 Getting Started

### 1. Setup Development Environment
1.  Fork the repository: `https://github.com/nsafouane/tsukuyomi`.
2.  Clone it locally:
    ```bash
    git clone https://github.com/nsafouane/tsukuyomi.git
    cd tsukuyomi
    ```
3.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 2. Review Project Structure
Familiarize yourself with the codebase.
- `tsukuyomi/brain/`: Agent logic and decision-making.
- `tsukuyomi/proto/`: Core engine and networking.
- `tsukuyomi/experiments/`: Simulation scenarios.
- `tests/`: Test suites.

See [RULES.md](../RULES.md) for coding standards and naming conventions.

### 3. Choose an Issue
Check the [Issues](https://github.com/nsafouane/tsukuyomi/issues) tab for a task that interests you or create a new one.

## 🧠 Coding Standards

### Style Guide
- **Language:** Python 3.8+
- **Line Length:** Keep lines under 700 characters for better readability.
- **Imports:** Always use absolute imports from `tsukuyomi` package root.
    - `from tsukuyomi.brain.AgentBrain import AgentBrain`
- **Docstrings:** Use Google-style docstrings for all public classes and methods.
- **Type Hinting:** Use modern Python type hints (`List`, `Optional`).
- **Logging:** Use `logging` module, not `print()`.

### Directory Placement
- **Tests:** All tests must be in `tests/` directory.
- **Protobufs:** Source `.proto` files go in `tsukuyomi/proto/`. Generated `_pb2.py` files go in same directory.

### Testing
- Write unit tests for new features in `tests/`.
- Ensure all existing tests pass before pushing.
- Aim for >80% test coverage on new code.

## 📝 Submitting Changes

### 1. Create a Branch
Always create a new branch for your feature or bugfix.
    ```bash
    git checkout -b feature/my-amazing-feature
    ```

### 2. Make Your Changes
- Write code following the style guide.
- Write/update tests for your changes.
- Add docstrings to new functions.

### 3. Commit Your Changes
- Use a clear, descriptive commit message.
    ```bash
    git add .
    git commit -m "feat(agent): add advanced memory recall"
    ```

### 4. Push to Branch
- Push your feature branch to GitHub.
    ```bash
    git push -u origin feature/my-amazing-feature
    ```

### 5. Create a Pull Request
1.  Go to the repository on GitHub.
2.  Click the "New Pull Request" button.
3.  Select your branch from the dropdown.
4.  Fill in the PR title and description. Use the provided template.

## 🧪 Code Review Process

### What we look for:
- **Correctness:** Does the code solve the intended problem?
- **Performance:** Is the code efficient? Does it scale well?
- **Readability:** Is the code easy to understand? Is it well-structured?
- **Maintainability:** Is it easy to modify and extend?

### Tips for a Great PR:
- Keep PRs small and focused.
- If a feature requires multiple files, mention why in the description.
- Link to related issues if your PR fixes a bug.
