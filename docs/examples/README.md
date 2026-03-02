Effect Input Example
=====================

Arrange:
- The example .mgx declares two inputs: `user_name` and `items` using
  `@effect input`.

Act:
- Run the example using the CLI:

  uv run python src/main.py execute --file-name docs/examples/effect-input-example.mgx

Assert:
- The execution completes without errors and the prompt content includes
  the substituted `user_name` and `items` values (visible in the run
  output). This is the observable result to validate behavior.

Notes:
- Use this example for manual Red/Green/Refactor cycles: start with the
  example as-is (Red), run and observe output (Green), then change the
  inputs and re-run (Refactor).
