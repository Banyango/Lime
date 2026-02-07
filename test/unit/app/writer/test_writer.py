from src.app.writers.writer import CliWriter


def test_on_text_added_should_append_text_to_output():
    # Arrange
    writer = CliWriter()

    # Act
    writer.on_text_added("Hello, ")
    writer.on_text_terminated()
    writer.on_text_added("World, ")
    writer.on_text_terminated()

    # Assert
    assert writer.output_text[0] == "Hello, "
