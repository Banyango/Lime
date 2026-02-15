import ast
import importlib

from core.agents.models import ExecutionModel


class ImportPlugin:
    @staticmethod
    def execute_import(import_stmt: str, execution_model: ExecutionModel, globals_dict=None) -> dict:
        """Execute an import statement and update the provided globals dictionary.

        Args:
            import_stmt (str): The import statement to execute.
            execution_model (ExecutionModel): The execution model for the current agent run.
            globals_dict (dict): The dictionary to update with the imported modules or objects.
        """
        if globals_dict is None:
            globals_dict = globals()

        tree = ast.parse(import_stmt)

        try:
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = importlib.import_module(alias.name)
                        name = alias.asname or alias.name
                        globals_dict[name] = module

                elif isinstance(node, ast.ImportFrom):
                    module = importlib.import_module(node.module)
                    for alias in node.names:
                        obj = getattr(module, alias.name)
                        name = alias.asname or alias.name
                        globals_dict[name] = obj
                else:
                    raise ValueError("Only import statements are allowed")
        except Exception as e:
            execution_model.add_import_error(str(e))

        return globals_dict
