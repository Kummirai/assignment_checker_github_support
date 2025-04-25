import io
import contextlib

def run_user_code(user_code: str, input_values: list[str]) -> str:
    input_iterator = iter(input_values)
    
    def mock_input(prompt=None):
        return next(input_iterator)
    
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            exec(user_code, {'input': mock_input})
        except Exception as e:
            return f"Error: {e}"
    return output.getvalue().strip()

def parse_test_file(content: str):
    lines = content.strip().split('\n')
    split_index = lines.index("===")
    inputs = lines[:split_index]
    expected_output = "\n".join(lines[split_index + 1:])
    return inputs, expected_output