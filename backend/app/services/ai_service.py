from app.ai.factory import AIProviderFactory
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.job_repository import AuditRepository


class AuthService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository | None = None):
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    async def register(self, email: str, username: str, password: str, full_name: str | None = None) -> dict:
        if await self.user_repo.get_by_email(email):
            raise ValueError("Email already registered")
        if await self.user_repo.get_by_username(username):
            raise ValueError("Username already taken")

        user = await self.user_repo.create(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
        )
        if self.audit_repo:
            await self.audit_repo.log("register", "user", user.id, user.id)

        return self._create_tokens(user)

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        if self.audit_repo:
            await self.audit_repo.log("login", "user", user.id, user.id)

        return {**self._create_tokens(user), "user": user}

    async def refresh_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise ValueError("User not found")

        return self._create_tokens(user)

    async def forgot_password(self, email: str) -> str:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("If the email exists, a reset link will be sent")
        return create_password_reset_token(email)

    async def reset_password(self, token: str, new_password: str) -> None:
        payload = decode_token(token)
        if not payload or payload.get("type") != "password_reset":
            raise ValueError("Invalid or expired reset token")

        user = await self.user_repo.get_by_email(payload["sub"])
        if not user:
            raise ValueError("User not found")

        await self.user_repo.update_password(user, get_password_hash(new_password))
        if self.audit_repo:
            await self.audit_repo.log("password_reset", "user", user.id, user.id)

    def _create_tokens(self, user) -> dict:
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }


class AIService:
    EXPLAIN_SYSTEM = "You are an expert code analyst. Analyze code and return structured JSON with: purpose, business_logic, inputs, outputs, complexity, dependencies."

    REFACTOR_PROMPTS = {
        "rename": "Rename variables to meaningful names following clean code principles.",
        "extract_method": "Extract repeated logic into well-named methods/functions.",
        "performance": "Optimize for performance without changing behavior.",
        "solid": "Apply SOLID principles to improve design.",
        "clean_code": "Apply clean code principles and best practices.",
        "security": "Fix security vulnerabilities and apply security best practices.",
        "async": "Convert synchronous code to async/await pattern where beneficial.",
    }

    def __init__(self, provider_name: str | None = None):
        self.provider = AIProviderFactory.get_provider(provider_name)

    async def explain_code(self, code: str, file_path: str) -> dict:
        prompt = f"Analyze this code from {file_path}:\n\n```\n{code}\n```\n\nReturn JSON with keys: purpose, business_logic, inputs (array), outputs (array), complexity (string), dependencies (array)."
        response = await self.provider.generate(prompt, self.EXPLAIN_SYSTEM, temperature=0.2)
        try:
            import json
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
        except Exception:
            pass
        return {
            "purpose": response.content,
            "business_logic": "",
            "inputs": [],
            "outputs": [],
            "complexity": "unknown",
            "dependencies": [],
            "_tokens": {"input": response.tokens_input, "output": response.tokens_output, "cost": response.cost},
        }

    async def chat(self, messages: list[dict], project_context: str = "") -> dict:
        system = f"You are an expert software engineer helping with code migration and analysis. Project context:\n{project_context[:8000]}"
        full_messages = [{"role": "system", "content": system}] + messages
        response = await self.provider.chat(full_messages)
        return {
            "content": response.content,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "cost": response.cost,
            "provider": response.provider,
            "model": response.model,
        }

    async def refactor_code(self, code: str, refactor_type: str, file_path: str) -> dict:
        instruction = self.REFACTOR_PROMPTS.get(refactor_type, "Improve this code.")
        prompt = f"{instruction}\n\nFile: {file_path}\n\n```\n{code}\n```\n\nReturn the refactored code and a summary of changes."
        response = await self.provider.generate(prompt, "Return refactored code followed by ---CHANGES--- and a bullet list of changes.", temperature=0.2)

        parts = response.content.split("---CHANGES---")
        refactored = parts[0].strip()
        if refactored.startswith("```"):
            lines = refactored.split("\n")
            refactored = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        suggestions = [line.strip("- ").strip() for line in parts[1].split("\n") if line.strip()] if len(parts) > 1 else []

        return {
            "original_code": code,
            "refactored_code": refactored,
            "changes_summary": "\n".join(suggestions) if suggestions else "Code refactored",
            "suggestions": suggestions,
            "tokens": {"input": response.tokens_input, "output": response.tokens_output, "cost": response.cost},
        }

    async def detect_bugs(self, code: str, file_path: str) -> dict:
        prompt = f"""Analyze this code for bugs and issues. File: {file_path}

```
{code}
```

Find: null pointer issues, memory issues, performance problems, security issues, duplicate code, dead code, unused imports.

Return JSON with: issues (array of {{type, severity, line, description, fix}}), severity_summary (object), recommendations (array)."""
        response = await self.provider.generate(prompt, "You are a static analysis expert. Return valid JSON only.", temperature=0.1)
        try:
            import json
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0:
                return json.loads(response.content[start:end])
        except Exception:
            pass
        return {"issues": [], "severity_summary": {}, "recommendations": [response.content]}

    async def generate_tests(self, code: str, file_path: str, framework: str = "pytest") -> str:
        prompt = f"Generate {framework} tests for this code from {file_path}:\n\n```\n{code}\n```"
        response = await self.provider.generate(prompt, f"Generate comprehensive {framework} tests. Return only test code.", temperature=0.2)
        return response.content

    async def generate_documentation(self, project_summary: str, doc_type: str) -> str:
        prompts = {
            "readme": "Generate a comprehensive README.md",
            "api": "Generate API documentation in OpenAPI/Swagger format",
            "architecture": "Generate an architecture document",
            "deployment": "Generate a deployment guide",
            "tdd": "Generate a Technical Design Document",
        }
        prompt = f"{prompts.get(doc_type, 'Generate documentation')}\n\nProject:\n{project_summary}"
        response = await self.provider.generate(prompt, "Generate professional technical documentation in Markdown.", temperature=0.3)
        return response.content

    async def generate_diagrams(self, analysis: dict) -> dict:
        prompt = f"""Based on this project analysis, generate React Flow compatible JSON for:
1. flow_diagram - application flow
2. dependency_graph - module dependencies  
3. class_diagram - class relationships
4. sequence_diagram - key API sequences

Analysis: {str(analysis)[:6000]}

Return JSON with keys: flow_diagram, dependency_graph, class_diagram, sequence_diagram.
Each should have nodes (array of {{id, label, type}}) and edges (array of {{id, source, target, label}})."""
        response = await self.provider.generate(prompt, "Return valid JSON only for React Flow diagrams.", temperature=0.2)
        try:
            import json
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0:
                return json.loads(response.content[start:end])
        except Exception:
            pass
        return self._default_diagrams(analysis)

    def _default_diagrams(self, analysis: dict) -> dict:
        nodes = [{"id": "1", "label": "Entry Point", "type": "input"}]
        edges = []
        for i, ctrl in enumerate(analysis.get("controllers", [])[:5]):
            nodes.append({"id": f"c{i}", "label": ctrl.split("/")[-1], "type": "controller"})
            edges.append({"id": f"e{i}", "source": "1", "target": f"c{i}", "label": "routes to"})
        return {
            "flow_diagram": {"nodes": nodes, "edges": edges},
            "dependency_graph": {"nodes": nodes, "edges": edges},
            "class_diagram": {"nodes": nodes, "edges": []},
            "sequence_diagram": {"nodes": nodes, "edges": edges},
        }
