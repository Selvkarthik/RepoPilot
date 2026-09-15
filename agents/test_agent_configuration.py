import ast
from pathlib import Path
import unittest


class AgentConfigurationTests(unittest.TestCase):
    def test_agent_does_not_expose_direct_file_content_tool(self):
        agent_path = Path(__file__).with_name("agent.py")
        tree = ast.parse(agent_path.read_text(encoding="utf-8"))

        tools_assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "tools"
                for target in node.targets
            )
        )
        tool_names = [element.id for element in tools_assignment.value.elts]

        self.assertNotIn("get_file_content", tool_names)
        self.assertIn("search_repository_code", tool_names)

    def test_agent_prompt_requires_rag_for_code_questions(self):
        agent_path = Path(__file__).with_name("agent.py")
        source = agent_path.read_text(encoding="utf-8")

        self.assertIn("Never retrieve source code directly", source)
        self.assertIn("use only search_repository_code", source)


if __name__ == "__main__":
    unittest.main()
