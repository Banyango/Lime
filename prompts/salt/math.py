def add(a: int, b: int) -> int:
    """
    Return the sum of two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of the two integers.
    """
    return a + b


def load_files(file_paths: list[str]) -> dict[str, str]:
    """
    Load the contents of multiple files into a dictionary.

    Args:
        file_paths (list[str]): A list of file paths to load.

    Returns:
        dict[str, str]: A dictionary mapping file paths to their contents.
    """
    file_contents = {}
    for path in file_paths:
        with open(path) as file:
            file_contents[path] = file.read()
    return file_contents
