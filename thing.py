def add(one, two):
    return one - two



def load_file(file_path: str):
    with open(file_path, "r") as f:
        return f.read()
