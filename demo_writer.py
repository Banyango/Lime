#!/usr/bin/env python3
"""
Demo script to showcase the Claude-like textual renderer
"""

from src.app.writers.writer import CliWriter

# Create a writer instance
writer = CliWriter()

# Demo 1: Render code with file path (like Claude)
print("=== Demo 1: Code rendering with filepath ===\n")
sample_code = '''def hello_world():
    """A simple hello world function"""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()'''

writer.render_code(sample_code, language="python", filepath="/example/hello.py")

# Demo 2: Render code without filepath
print("\n=== Demo 2: Code rendering without filepath ===\n")
writer.render_code("const greeting = 'Hello from JavaScript!';", language="javascript")

# Demo 3: Render markdown
print("\n=== Demo 3: Markdown rendering ===\n")
markdown_content = """
# Welcome to the Demo

This is a **bold statement** and this is *italic*.

## Features
- Syntax highlighting
- File path display
- Rich text formatting
"""
writer.render_markdown(markdown_content)

# Demo 4: Render header
print("\n=== Demo 4: Headers ===\n")
writer.render_header("Main Title", level=1)
writer.render_header("Subtitle", level=2)
writer.render_header("Section", level=3)

# Demo 5: Render panel
print("\n\n=== Demo 5: Panel rendering ===\n")
writer.render_panel("This is important information!", title="Info", border_style="green")

# Demo 6: Styled text
print("\n=== Demo 6: Styled text ===\n")
writer.render_text("This is regular text")
writer.render_text("This is bold text", style="bold")
writer.render_text("This is red text", style="red")
writer.render_text("This is bold cyan text", style="bold cyan")

# Demo 7: Divider
print("\n=== Demo 7: Divider ===\n")
writer.render_text("Content above")
writer.render_divider()
writer.render_text("Content below")

# Demo 8: Different languages
print("\n\n=== Demo 8: Multiple language support ===\n")
writer.render_code("SELECT * FROM users WHERE active = true;", language="sql", filepath="/queries/users.sql")
writer.render_code('{"name": "example", "value": 42}', language="json", filepath="/config/settings.json")

print("\n\n✨ Demo complete! The textual renderer supports Claude-like code formatting.")

