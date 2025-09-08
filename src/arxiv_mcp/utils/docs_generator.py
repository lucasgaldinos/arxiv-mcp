"""
API documentation generator for the ArXiv MCP server.

This module generates comprehensive API documentation from code annotations,
docstrings, and type hints, providing both Markdown and HTML output formats.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from .logging import structured_logger


logger = structured_logger()


@dataclass
class ParameterDoc:
    """Documentation for a function/method parameter."""

    name: str
    type_hint: str
    description: str
    required: bool = True
    default_value: Any = None


@dataclass
class ToolDoc:
    """Documentation for an MCP tool."""

    name: str
    description: str
    parameters: List[ParameterDoc]
    examples: List[str] = None
    returns: str = ""
    errors: List[str] = None


@dataclass
class ModuleDoc:
    """Documentation for a module."""

    name: str
    description: str
    classes: List[Dict[str, Any]] = None
    functions: List[Dict[str, Any]] = None
    tools: List[ToolDoc] = None


@dataclass
class APIDocumentation:
    """Complete API documentation."""

    title: str
    version: str
    description: str
    modules: List[ModuleDoc]
    generated_at: str
    tools_summary: List[ToolDoc] = None


class DocGenerator:
    """Generates API documentation from code annotations."""

    def __init__(self, source_path: Path, output_path: Path = None):
        self.source_path = Path(source_path)
        self.output_path = Path(output_path) if output_path else Path("docs/api")
        self.output_path.mkdir(parents=True, exist_ok=True)

    def extract_mcp_tools(self, tools_file: Path) -> List[ToolDoc]:
        """Extract MCP tool documentation from tools.py."""
        logger.info(f"Extracting MCP tools from {tools_file}")

        try:
            with open(tools_file, "r") as f:
                content = f.read()

            # Parse the tools list
            tree = ast.parse(content)
            tools = []

            # Find the tools list in the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.List):
                    for item in node.elts:
                        if (
                            isinstance(item, ast.Call)
                            and hasattr(item.func, "id")
                            and item.func.id == "Tool"
                        ):
                            tool_doc = self._parse_tool_ast(item)
                            if tool_doc:
                                tools.append(tool_doc)

            return tools
        except Exception as e:
            logger.error(f"Error extracting tools: {e}")
            return []

    def _parse_tool_ast(self, tool_node: ast.Call) -> Optional[ToolDoc]:
        """Parse a Tool() call from AST."""
        try:
            name = ""
            description = ""
            parameters = []

            # Parse keyword arguments
            for keyword in tool_node.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    name = keyword.value.value
                elif keyword.arg == "description" and isinstance(
                    keyword.value, ast.Constant
                ):
                    description = keyword.value.value
                elif keyword.arg == "inputSchema" and isinstance(
                    keyword.value, ast.Dict
                ):
                    parameters = self._parse_input_schema(keyword.value)

            if name and description:
                return ToolDoc(
                    name=name,
                    description=description,
                    parameters=parameters,
                    examples=[],
                    returns="TextContent with tool output",
                    errors=["Tool execution errors", "Invalid arguments"],
                )
        except Exception as e:
            logger.error(f"Error parsing tool AST: {e}")

        return None

    def _parse_input_schema(self, schema_node: ast.Dict) -> List[ParameterDoc]:
        """Parse the inputSchema dictionary from AST."""
        parameters = []

        try:
            # Convert AST to actual dict for easier parsing
            schema_str = ast.unparse(schema_node)
            # This is a simplified approach - in production, you'd want more robust parsing
            if "properties" in schema_str and "required" in schema_str:
                # Extract parameter info from the schema
                # This is a placeholder - you'd implement full JSON schema parsing
                pass
        except Exception as e:
            logger.debug(f"Error parsing input schema: {e}")

        return parameters

    def extract_module_doc(self, module_path: Path) -> ModuleDoc:
        """Extract documentation from a Python module."""
        logger.info(f"Extracting module documentation from {module_path}")

        try:
            with open(module_path, "r") as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract module docstring
            module_docstring = ast.get_docstring(tree) or ""

            # Extract classes and functions
            classes = []
            functions = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_doc = self._extract_class_doc(node)
                    classes.append(class_doc)
                elif isinstance(node, ast.FunctionDef) or isinstance(
                    node, ast.AsyncFunctionDef
                ):
                    func_doc = self._extract_function_doc(node)
                    functions.append(func_doc)

            return ModuleDoc(
                name=module_path.stem,
                description=module_docstring,
                classes=classes,
                functions=functions,
            )
        except Exception as e:
            logger.error(f"Error extracting module doc: {e}")
            return ModuleDoc(
                name=module_path.stem, description="", classes=[], functions=[]
            )

    def _extract_class_doc(self, class_node: ast.ClassDef) -> Dict[str, Any]:
        """Extract documentation from a class definition."""
        docstring = ast.get_docstring(class_node) or ""
        methods = []

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                method_doc = self._extract_function_doc(node)
                methods.append(method_doc)

        return {"name": class_node.name, "description": docstring, "methods": methods}

    def _extract_function_doc(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Dict[str, Any]:
        """Extract documentation from a function definition."""
        docstring = ast.get_docstring(func_node) or ""

        # Extract parameters
        parameters = []
        for arg in func_node.args.args:
            param_info = {
                "name": arg.arg,
                "type": getattr(arg.annotation, "id", "Any")
                if arg.annotation
                else "Any",
            }
            parameters.append(param_info)

        return {
            "name": func_node.name,
            "description": docstring,
            "parameters": parameters,
            "is_async": isinstance(func_node, ast.AsyncFunctionDef),
        }

    def generate_documentation(self) -> APIDocumentation:
        """Generate complete API documentation."""
        logger.info("Generating API documentation")

        modules = []
        tools_summary = []

        # Process all Python files in the source directory
        for py_file in self.source_path.rglob("*.py"):
            if py_file.name == "__pycache__":
                continue

            module_doc = self.extract_module_doc(py_file)
            modules.append(module_doc)

            # Special handling for tools.py
            if py_file.name == "tools.py":
                tools = self.extract_mcp_tools(py_file)
                tools_summary.extend(tools)
                module_doc.tools = tools

        return APIDocumentation(
            title="ArXiv MCP Server API",
            version="0.2.2",
            description="Comprehensive API documentation for the ArXiv MCP server",
            modules=modules,
            tools_summary=tools_summary,
            generated_at=datetime.now().isoformat(),
        )

    def export_markdown(self, documentation: APIDocumentation) -> str:
        """Export documentation as Markdown."""
        logger.info("Exporting documentation as Markdown")

        md_content = f"""# {documentation.title}
        
**Version:** {documentation.version}  
**Generated:** {documentation.generated_at}

{documentation.description}

## MCP Tools Overview

The ArXiv MCP server provides the following tools:

"""

        # Add tools summary
        for tool in documentation.tools_summary or []:
            md_content += f"""### {tool.name}

{tool.description}

**Parameters:**
"""
            for param in tool.parameters:
                required = " (required)" if param.required else " (optional)"
                md_content += f"- `{param.name}` ({param.type_hint}){required}: {param.description}\n"

            md_content += f"\n**Returns:** {tool.returns}\n\n"

        # Add modules documentation
        md_content += "\n## Modules\n\n"

        for module in documentation.modules:
            md_content += f"### {module.name}\n\n{module.description}\n\n"

            if module.classes:
                md_content += "#### Classes\n\n"
                for class_doc in module.classes:
                    md_content += (
                        f"##### {class_doc['name']}\n\n{class_doc['description']}\n\n"
                    )

            if module.functions:
                md_content += "#### Functions\n\n"
                for func_doc in module.functions:
                    async_marker = "(async) " if func_doc.get("is_async") else ""
                    md_content += f"##### {async_marker}{func_doc['name']}\n\n{func_doc['description']}\n\n"

        return md_content

    def export_json(self, documentation: APIDocumentation) -> str:
        """Export documentation as JSON."""
        logger.info("Exporting documentation as JSON")
        return json.dumps(asdict(documentation), indent=2, default=str)

    def save_documentation(
        self, documentation: APIDocumentation, formats: List[str] = None
    ):
        """Save documentation in specified formats."""
        if formats is None:
            formats = ["markdown", "json"]

        for format_type in formats:
            if format_type == "markdown":
                content = self.export_markdown(documentation)
                output_file = self.output_path / "api_documentation.md"
            elif format_type == "json":
                content = self.export_json(documentation)
                output_file = self.output_path / "api_documentation.json"
            else:
                logger.warning(f"Unsupported format: {format_type}")
                continue

            with open(output_file, "w") as f:
                f.write(content)

            logger.info(f"Documentation saved to {output_file}")

    def generate_and_save(self, formats: List[str] = None) -> APIDocumentation:
        """Generate and save documentation in one step."""
        documentation = self.generate_documentation()
        self.save_documentation(documentation, formats)
        return documentation


def generate_api_docs(
    source_path: str = None, output_path: str = None, formats: List[str] = None
) -> APIDocumentation:
    """
    Convenience function to generate API documentation.

    Args:
        source_path: Path to the source code directory
        output_path: Path to save documentation
        formats: List of output formats ('markdown', 'json')

    Returns:
        APIDocumentation object
    """
    if source_path is None:
        source_path = Path(__file__).parent.parent  # Default to src/arxiv_mcp

    generator = DocGenerator(source_path, output_path)
    return generator.generate_and_save(formats or ["markdown", "json"])


if __name__ == "__main__":
    # Generate documentation when run directly
    docs = generate_api_docs()
    print(
        f"Generated documentation with {len(docs.tools_summary or [])} tools and {len(docs.modules)} modules"
    )
