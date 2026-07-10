import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from app.core.config import settings
from app.services.analysis_service import MIGRATION_MAP, ProjectAnalyzer


class MigrationService:
    MIGRATION_PROMPTS = {
        "java_to_fastapi": "Convert this Java code to Python FastAPI. Maintain business logic, use Pydantic models, async where appropriate.",
        "spring_boot_to_fastapi": "Convert this Spring Boot Java code to Python FastAPI. Map controllers to routers, services to service classes, repositories to SQLAlchemy.",
        "flask_to_fastapi": "Convert this Flask code to FastAPI. Use Pydantic models, dependency injection, and async endpoints.",
        "react_to_nextjs": "Convert this React component to Next.js 15 with App Router. Use TypeScript, server components where appropriate.",
        "angular_to_react": "Convert this Angular component to React with TypeScript and hooks.",
        "javascript_to_typescript": "Convert this JavaScript code to TypeScript with proper types and interfaces.",
        "dotnet_to_python": "Convert this C# .NET code to Python FastAPI with equivalent functionality.",
        "sql_server_to_postgresql": "Convert this SQL Server T-SQL to PostgreSQL compatible SQL.",
        "oracle_to_postgresql": "Convert this Oracle PL/SQL to PostgreSQL compatible SQL.",
        "php_to_nodejs": "Convert this PHP code to Node.js with Express.",
    }

    def __init__(self, ai_provider):
        self.ai = ai_provider
        self.analyzer = ProjectAnalyzer()

    def get_migration_key(self, source_lang: str, target_lang: str, source_fw: str | None = None, target_fw: str | None = None) -> str:
        if source_fw == "spring_boot":
            return "spring_boot_to_fastapi"
        if source_fw == "flask" and target_fw == "fastapi":
            return "flask_to_fastapi"
        if source_fw == "react" and target_fw == "nextjs":
            return "react_to_nextjs"
        if source_fw == "angular" and target_fw == "react":
            return "angular_to_react"
        return f"{source_lang}_to_{target_lang}"

    async def migrate_file(self, content: str, migration_key: str, file_path: str) -> str:
        prompt = self.MIGRATION_PROMPTS.get(
            migration_key,
            f"Migrate this code from the source to target technology. File: {file_path}",
        )
        system = "You are an expert code migration engineer. Return ONLY the migrated code without explanations or markdown fences."
        response = await self.ai.generate(
            prompt=f"{prompt}\n\nSource file: {file_path}\n\n```\n{content}\n```",
            system_prompt=system,
            temperature=0.2,
            max_tokens=8192,
        )
        result = response.content.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return result

    async def migrate_project(self, project_path: str, target_language: str, target_framework: str | None, source_analysis: dict, progress_callback=None) -> dict:
        source_lang = source_analysis.get("language", "unknown")
        source_fw = source_analysis.get("framework")
        migration_key = self.get_migration_key(source_lang, target_language, source_fw, target_framework)

        migrated_dir = os.path.join(settings.UPLOAD_DIR, "migrated", os.path.basename(project_path))
        os.makedirs(migrated_dir, exist_ok=True)

        files = source_analysis.get("files", [])
        migrated_files = []
        total = len(files)

        for i, file_info in enumerate(files):
            src_path = os.path.join(project_path, file_info["path"])
            dest_path = os.path.join(migrated_dir, file_info["path"])
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            if file_info.get("language") in ("unknown", "json", "yaml", "xml", "properties", "html", "css"):
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dest_path)
                migrated_files.append({"path": file_info["path"], "migrated": False, "reason": "config/static"})
            else:
                content = file_info.get("content", "")
                if content and len(content) < 50000:
                    try:
                        migrated_content = await self.migrate_file(content, migration_key, file_info["path"])
                        Path(dest_path).write_text(migrated_content, encoding="utf-8")
                        migrated_files.append({"path": file_info["path"], "migrated": True})
                    except Exception as e:
                        shutil.copy2(src_path, dest_path) if os.path.exists(src_path) else None
                        migrated_files.append({"path": file_info["path"], "migrated": False, "error": str(e)})
                else:
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dest_path)

            if progress_callback:
                progress_callback(int((i + 1) / total * 100))

        self._generate_project_structure(migrated_dir, target_language, target_framework)

        return {
            "migrated_path": migrated_dir,
            "migration_key": migration_key,
            "files_migrated": sum(1 for f in migrated_files if f.get("migrated")),
            "total_files": total,
            "details": migrated_files,
        }

    def _generate_project_structure(self, project_dir: str, language: str, framework: str | None) -> None:
        if framework == "fastapi" or (language == "python" and framework in (None, "fastapi")):
            dirs = ["app/api", "app/models", "app/services", "app/core", "tests"]
            for d in dirs:
                os.makedirs(os.path.join(project_dir, d), exist_ok=True)
            req_file = os.path.join(project_dir, "requirements.txt")
            if not os.path.exists(req_file):
                Path(req_file).write_text("fastapi\nuvicorn\nsqlalchemy\npydantic\n", encoding="utf-8")

        if framework == "nextjs":
            dirs = ["src/app", "src/components", "src/lib", "public"]
            for d in dirs:
                os.makedirs(os.path.join(project_dir, d), exist_ok=True)

    def create_zip(self, project_dir: str, output_path: str) -> str:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zf.write(file_path, arcname)
        return output_path

    @staticmethod
    def clone_github_repo(url: str, dest_dir: str, branch: str = "main", token: str | None = None) -> str:
        os.makedirs(dest_dir, exist_ok=True)
        clone_url = url
        if token and "github.com" in url:
            clone_url = url.replace("https://", f"https://{token}@")

        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, clone_url, dest_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        return dest_dir
