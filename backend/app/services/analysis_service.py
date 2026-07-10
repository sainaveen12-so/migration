import os
import re
import zipfile
from pathlib import Path
from typing import Any

from app.core.config import settings

LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".java": "java",
    ".py": "python",
    ".cs": "csharp",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".php": "php",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".xml": "xml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".properties": "properties",
    ".gradle": "gradle",
    ".kt": "kotlin",
    ".go": "go",
    ".rb": "ruby",
    ".vue": "vue",
}

FRAMEWORK_PATTERNS: dict[str, list[str]] = {
    "spring_boot": ["@SpringBootApplication", "spring-boot", "org.springframework"],
    "flask": ["from flask", "Flask(", "@app.route"],
    "django": ["from django", "DJANGO_SETTINGS", "django.contrib"],
    "fastapi": ["from fastapi", "FastAPI(", "APIRouter"],
    "react": ["import React", "from 'react'", 'from "react"'],
    "angular": ["@angular/", "@Component", "@NgModule"],
    "nextjs": ["next/", "getServerSideProps", "getStaticProps"],
    "dotnet": ["using System", "Microsoft.AspNetCore", "namespace "],
    "express": ["express()", "require('express')", 'from "express"'],
    "laravel": ["Illuminate\\", "artisan", "Route::"],
}

MIGRATION_MAP: dict[str, dict[str, str]] = {
    "java": {"target": "python", "framework": "fastapi"},
    "spring_boot": {"target": "python", "framework": "fastapi"},
    "flask": {"target": "python", "framework": "fastapi"},
    "react": {"target": "typescript", "framework": "nextjs"},
    "angular": {"target": "typescript", "framework": "react"},
    "javascript": {"target": "typescript", "framework": None},
    "csharp": {"target": "python", "framework": "fastapi"},
    "dotnet": {"target": "python", "framework": "fastapi"},
    "php": {"target": "javascript", "framework": "nodejs"},
    "sql_server": {"target": "sql", "framework": "postgresql"},
    "oracle": {"target": "sql", "framework": "postgresql"},
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target", ".idea", ".vscode"}


class ProjectAnalyzer:
    def analyze_project(self, project_path: str) -> dict[str, Any]:
        path = Path(project_path)
        files = self._collect_files(path)
        languages = self._detect_languages(files)
        primary_language = max(languages, key=languages.get) if languages else "unknown"
        framework = self._detect_framework(path, files)
        dependencies = self._extract_dependencies(path, primary_language, framework)
        folder_structure = self._build_folder_tree(path)
        rest_apis = self._extract_rest_apis(files)
        database_info = self._detect_database(files)
        orm = self._detect_orm(files)
        controllers = self._find_files_by_pattern(files, ["controller", "Controller", "handlers", "routes"])
        services = self._find_files_by_pattern(files, ["service", "Service", "services"])
        repositories = self._find_files_by_pattern(files, ["repository", "Repository", "repo", "dao", "DAO"])
        utilities = self._find_files_by_pattern(files, ["util", "Util", "helper", "Helper", "common"])
        total_lines = sum(f.get("lines", 0) for f in files)
        complexity = self._calculate_complexity(files)

        return {
            "language": primary_language,
            "languages": languages,
            "framework": framework,
            "dependencies": dependencies,
            "folder_structure": folder_structure,
            "rest_apis": rest_apis,
            "database": database_info,
            "orm": orm,
            "controllers": [f["path"] for f in controllers[:20]],
            "services": [f["path"] for f in services[:20]],
            "repositories": [f["path"] for f in repositories[:20]],
            "utilities": [f["path"] for f in utilities[:20]],
            "total_files": len(files),
            "total_lines": total_lines,
            "complexity_score": complexity,
            "summary": self._generate_summary(primary_language, framework, len(files), total_lines),
            "complexity_report": {
                "overall_score": complexity,
                "file_count": len(files),
                "avg_lines_per_file": total_lines // max(len(files), 1),
                "language_distribution": languages,
            },
            "architecture_overview": self._generate_architecture_overview(framework, controllers, services, repositories),
            "files": files,
        }

    def _collect_files(self, root: Path) -> list[dict[str, Any]]:
        files = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in SKIP_DIRS for part in file_path.parts):
                continue
            if file_path.stat().st_size > 5 * 1024 * 1024:
                continue

            rel_path = str(file_path.relative_to(root)).replace("\\", "/")
            ext = file_path.suffix.lower()
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

            files.append({
                "path": rel_path,
                "name": file_path.name,
                "extension": ext,
                "language": LANGUAGE_EXTENSIONS.get(ext, "unknown"),
                "content": content,
                "lines": len(content.splitlines()),
                "size": file_path.stat().st_size,
            })
        return files

    def _detect_languages(self, files: list[dict]) -> dict[str, int]:
        langs: dict[str, int] = {}
        for f in files:
            lang = f.get("language", "unknown")
            if lang != "unknown":
                langs[lang] = langs.get(lang, 0) + 1
        return langs

    def _detect_framework(self, root: Path, files: list[dict]) -> str | None:
        for framework, patterns in FRAMEWORK_PATTERNS.items():
            for f in files[:200]:
                content = f.get("content", "")
                if any(p in content for p in patterns):
                    return framework

        for name in ["pom.xml", "build.gradle", "package.json", "requirements.txt", "composer.json", "Cargo.toml"]:
            if (root / name).exists():
                content = (root / name).read_text(encoding="utf-8", errors="ignore")
                for framework, patterns in FRAMEWORK_PATTERNS.items():
                    if any(p.lower() in content.lower() for p in patterns):
                        return framework
        return None

    def _extract_dependencies(self, root: Path, language: str, framework: str | None) -> list[str]:
        deps = []
        dep_files = {
            "python": ["requirements.txt", "pyproject.toml", "Pipfile"],
            "java": ["pom.xml", "build.gradle"],
            "javascript": ["package.json"],
            "typescript": ["package.json"],
            "csharp": ["*.csproj"],
            "php": ["composer.json"],
        }
        for dep_file in dep_files.get(language, ["package.json", "requirements.txt"]):
            for f in root.rglob(dep_file):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if dep_file == "requirements.txt":
                        deps.extend(line.strip().split("==")[0].split(">=")[0] for line in content.splitlines() if line.strip() and not line.startswith("#"))
                    elif dep_file == "package.json":
                        import json
                        data = json.loads(content)
                        deps.extend(data.get("dependencies", {}).keys())
                        deps.extend(data.get("devDependencies", {}).keys())
                    elif dep_file in ("pom.xml", "build.gradle"):
                        deps.extend(re.findall(r'<artifactId>([^<]+)</artifactId>', content))
                except Exception:
                    pass
        return list(set(deps))[:50]

    def _build_folder_tree(self, root: Path, max_depth: int = 4) -> dict:
        def build_tree(path: Path, depth: int = 0) -> dict:
            if depth > max_depth:
                return {"name": "...", "type": "truncated"}
            node: dict[str, Any] = {"name": path.name, "type": "directory", "children": []}
            try:
                for child in sorted(path.iterdir()):
                    if child.name in SKIP_DIRS or child.name.startswith("."):
                        continue
                    if child.is_dir():
                        node["children"].append(build_tree(child, depth + 1))
                    else:
                        node["children"].append({"name": child.name, "type": "file"})
            except PermissionError:
                pass
            return node

        return build_tree(root)

    def _extract_rest_apis(self, files: list[dict]) -> list[dict[str, Any]]:
        apis = []
        patterns = [
            (r'@(?:Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*["\']([^"\']+)', "spring"),
            (r'@app\.route\s*\(\s*["\']([^"\']+)', "flask"),
            (r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', "fastapi"),
            (r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', "express"),
        ]
        for f in files:
            content = f.get("content", "")
            for pattern, framework in patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    groups = match.groups()
                    if framework == "fastapi" or framework == "express":
                        apis.append({"method": groups[0].upper(), "path": groups[1], "file": f["path"], "framework": framework})
                    else:
                        apis.append({"method": "GET", "path": groups[0], "file": f["path"], "framework": framework})
        return apis[:100]

    def _detect_database(self, files: list[dict]) -> dict | None:
        db_patterns = {
            "postgresql": ["postgresql", "postgres", "psycopg2", "asyncpg"],
            "mysql": ["mysql", "pymysql", "mariadb"],
            "sqlserver": ["sqlserver", "mssql", "pyodbc"],
            "oracle": ["oracle", "cx_Oracle", "oracledb"],
            "mongodb": ["mongodb", "pymongo", "mongoose"],
            "sqlite": ["sqlite", "sqlite3"],
        }
        for f in files:
            content = f.get("content", "").lower()
            for db, patterns in db_patterns.items():
                if any(p in content for p in patterns):
                    return {"type": db, "detected_in": f["path"]}
        return None

    def _detect_orm(self, files: list[dict]) -> str | None:
        orm_patterns = {
            "sqlalchemy": ["sqlalchemy", "from sqlalchemy"],
            "hibernate": ["hibernate", "@Entity", "JpaRepository"],
            "django_orm": ["django.db.models", "models.Model"],
            "typeorm": ["typeorm", "@Entity()"],
            "prisma": ["prisma", "@prisma"],
            "entity_framework": ["EntityFramework", "DbContext"],
        }
        for f in files:
            content = f.get("content", "").lower()
            for orm, patterns in orm_patterns.items():
                if any(p.lower() in content for p in patterns):
                    return orm
        return None

    def _find_files_by_pattern(self, files: list[dict], patterns: list[str]) -> list[dict]:
        return [f for f in files if any(p.lower() in f["path"].lower() for p in patterns)]

    def _calculate_complexity(self, files: list[dict]) -> float:
        if not files:
            return 0.0
        code_files = [f for f in files if f.get("language") not in ("unknown", "json", "yaml", "xml")]
        if not code_files:
            return 0.0
        avg_lines = sum(f["lines"] for f in code_files) / len(code_files)
        return min(10.0, round((len(code_files) * 0.1) + (avg_lines / 100), 2))

    def _generate_summary(self, language: str, framework: str | None, file_count: int, total_lines: int) -> str:
        fw = f" using {framework}" if framework else ""
        return f"A {language}{fw} project with {file_count} files and approximately {total_lines:,} lines of code."

    def _generate_architecture_overview(self, framework: str | None, controllers: list, services: list, repositories: list) -> str:
        parts = [f"Framework: {framework or 'Unknown'}"]
        if controllers:
            parts.append(f"Controllers/Handlers: {len(controllers)} files")
        if services:
            parts.append(f"Services: {len(services)} files")
        if repositories:
            parts.append(f"Repositories/DAOs: {len(repositories)} files")
        return ". ".join(parts) + "."


class FileExtractor:
    @staticmethod
    def extract_zip(zip_path: str, dest_dir: str) -> str:
        os.makedirs(dest_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_dir)
        return dest_dir

    @staticmethod
    def get_project_root(extracted_path: str) -> str:
        path = Path(extracted_path)
        children = [c for c in path.iterdir() if c.name not in SKIP_DIRS]
        if len(children) == 1 and children[0].is_dir():
            return str(children[0])
        return extracted_path
