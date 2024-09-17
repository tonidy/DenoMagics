import subprocess
import shlex
import tempfile
import os
import json
from IPython.display import display, HTML, Markdown  # type: ignore
from IPython.core.magic import register_cell_magic  # type: ignore


# Determine if running on Google Colab
def is_google_colab():
    try:
        import google.colab  # type: ignore  # noqa: F401

        return True
    except ImportError:
        return False


# Deno command
def get_deno_cmd():
    if is_google_colab():
        return "/root/.deno/bin/deno"
    else:
        return "deno"


def install_deno_colab():
    """
    Install Deno (for Google Colab)
    """
    if not is_google_colab():
        print("Not running in Google Colab. Skipping Deno installation.")
        return

    # Deno installation command
    command = "curl -fsSL https://deno.land/x/install/install.sh | sh"

    # Execute shell command
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()

    # Display output
    if process.returncode == 0:
        print("Deno installed successfully.")
        print(stdout.decode())
    else:
        print("Error occurred during Deno installation.")
        print(stderr.decode())


def register_deno_magics():
    """
    Register Deno cell magic commands
    """
    from IPython import get_ipython  # type: ignore

    ipy = get_ipython()
    ipy.register_magic_function(d)
    ipy.register_magic_function(run_deno)
    ipy.register_magic_function(run_deno_iframe)
    ipy.register_magic_function(view_deno_iframe)
    ipy.register_magic_function(run_deno_bundle_iframe)
    ipy.register_magic_function(view_deno_bundle_iframe)
    print("Deno cell magic commands registered.")


@register_cell_magic
def d(line, cell):
    run_deno(line, cell)


@register_cell_magic
def run_deno(line, cell):
    """
    Magic command to run Deno code
    """
    args = shlex.split(line)

    useval = args[0] if len(args) > 0 else "False"
    verbose = args[1] if len(args) > 1 else ""

    isVerbose = False
    if verbose.lower() == "v" or verbose.lower() == "verbose":
        isVerbose = True

    # Retrieve Jupyter user variables and make them available in the Deno script
    if useval.lower() == "true":
        curdir = os.getcwd()
        curdir = curdir.replace("\\", "/")

        # Retrieve Jupyter user variables, convert them to a JSON file, and save them as a temporary file
        with tempfile.NamedTemporaryFile(
            dir=curdir, suffix=".json", delete=False
        ) as json_file:
            # Retrieve IPython user namespace
            from IPython import get_ipython  # type: ignore

            ipython = get_ipython()
            variables = ipython.user_ns

            # Filter only serializable variables
            def is_serializable(obj):
                try:
                    json.dumps(obj)
                    return True
                except (TypeError, OverflowError):
                    return False

            filtered_vars = {
                name: value
                for name, value in variables.items()
                if is_serializable(value)
            }

            # Convert to JSON format
            json_data = json.dumps(filtered_vars)
            json_file.write(json_data.encode("utf-8"))
            json_file_path = json_file.name

            esc_json_file_path = json_file_path.replace("\\", "\\\\")

        # Deno script to retrieve, modify, and add Jupyter global variables
        pre_script = f"""
globalThis.isJupyterCell = true;
globalThis.jupyter = JSON.parse(Deno.readTextFileSync('{esc_json_file_path}'));
globalThis.jupyterExit = function(code = 0) {{
    Deno.writeTextFileSync('{esc_json_file_path}', JSON.stringify(globalThis.jupyter));
    Deno.exit(code);
}}
        """

        after_script = """
jupyterExit();
        """

    else:
        pre_script = """
globalThis.isJupyterCell = true;
globalThis.jupyterExit = function(code = 0) {
    Deno.exit(code);
}
        """

        after_script = ""

    cell = pre_script + cell + after_script

    if isVerbose:
        print("Cell: ", cell)

    # Execute Deno command
    denocmd = get_deno_cmd()
    process = subprocess.Popen(
        [denocmd, "eval", cell],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # subprocess.run([denocmd, "eval", "--help"], capture_output=True)

    stdout, stderr = process.communicate()

    if useval.lower() == "true":
        # Restore global variables from the temporary JSON file
        with open(json_file_path, "r") as f:
            # Retrieve IPython user namespace
            from IPython import get_ipython  # type: ignore

            ipython = get_ipython()
            variables = ipython.user_ns

            external_data = json.load(f)

            # Update user_ns
            for key, value in external_data.items():
                variables[key] = value
        os.remove(json_file_path)

    # Display results using the enhanced display function
    display_result(stdout, stderr, process.returncode)

    # Display results
    # if process.returncode == 0:
    #     print(stdout.decode("utf-8"))
    # else:
    #     print(stderr.decode("utf-8"))


@register_cell_magic
def run_deno_iframe(line, cell):
    """
    Magic command to transpile and display Deno code in an iframe
    """
    run_iframe(line, cell, "transpile", False)


@register_cell_magic
def view_deno_iframe(line, cell):
    """
    Magic command to transpile and display Deno code along with HTML
    """
    run_iframe(line, cell, "transpile", True)


@register_cell_magic
def run_deno_bundle_iframe(line, cell):
    """
    Magic command to bundle Deno code and libraries and display them in an iframe
    """
    run_iframe(line, cell, "bundle", False)


@register_cell_magic
def view_deno_bundle_iframe(line, cell):
    """
    Magic command to display bundled Deno code, libraries, and HTML
    """
    run_iframe(line, cell, "bundle", True)


# Common logic for magic commands
def run_iframe(line, cell, type, viewmode):
    args = shlex.split(line)
    width = args[0] if len(args) > 0 else 500
    height = args[1] if len(args) > 1 else 500
    srcs = args[2:] if len(args) > 2 else []

    js_code = deno_transpile(cell, type)

    if js_code is None:
        return

    output_iframe(js_code, width, height, srcs, viewmode)


# Transpile Deno code
def deno_transpile(code, type):
    curdir = os.getcwd()

    curdir = curdir.replace("\\", "/")

    with tempfile.NamedTemporaryFile(dir=curdir, suffix=".ts", delete=False) as ts_file:
        ts_file.write(code.encode("utf-8"))
        ts_file_base_path = ts_file.name
        ts_file_path = ts_file_base_path.replace("\\", "/")

    deno_script = f"""
import {{ {type} }} from "https://deno.land/x/emit/mod.ts";

const url = new URL("file://{ts_file_path}", import.meta.url);
const result = await {type}(url.href);

let code = "";
if ("{type}" === "transpile") {{
    code = result.get(url.href);
}} else if ("{type}" === "bundle"){{
    code = result.code;
}}

console.log(code);
    """.strip()

    with tempfile.NamedTemporaryFile(
        dir=curdir, suffix=".ts", delete=False
    ) as deno_file:
        deno_file.write(deno_script.encode("utf-8"))
        deno_file_path = deno_file.name

    # Execute Deno script and capture output
    denocmd = get_deno_cmd()
    process = subprocess.Popen(
        [denocmd, "run", "--allow-all", deno_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process.communicate()

    os.remove(ts_file_base_path)
    os.remove(deno_file_path)

    if process.returncode == 0:
        return stdout.decode("utf-8")
    else:
        # Error message if an error occurred
        print("Error occurred during transpiling:")
        print(stderr.decode("utf-8"))
        return None


# Display in an IFrame
def output_iframe(js_code, width, height, srcs, viewmode):
    # Convert the files specified by srcs into script tags
    if len(srcs) > 0:
        src_tags = "\n".join([f"""    <script src="{src}"></script>""" for src in srcs])
        src_tags = f"\n{src_tags}"
    else:
        src_tags = ""

    # Create the HTML to display in the iframe
    base_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">{src_tags}
</head>
<body>
    <div id="error" style="color: red; font-weight: bold; display: none;"></div>
    <script>
        window.addEventListener('error', function(event) {{
            document.getElementById('error').innerHTML = "Error: " + event.message;
            document.getElementById('error').style.display = 'block';
            return false;
        }});
    </script>
    <script type="module">
{js_code}
    </script>
</body>
</html>
    """


def display_result(stdout, stderr, returncode):
    """
    Enhanced result display function for Jupyter Notebook.
    """
    # Success case
    if returncode == 0:
        if is_json(stdout.decode("utf-8")):
            # Pretty print JSON output if it's JSON
            json_output = json.loads(stdout.decode("utf-8"))
            display(Markdown("### Output:"))
            display(Markdown(f"```json\n{json.dumps(json_output, indent=4)}\n```"))
        else:
            # Plain text output with success style
            # display(
            #     HTML(
            #         f"<div style='color: green; font-weight: bold;'>Execution successful:</div>"
            #     )
            # )
            display(HTML(f"<pre>{stdout.decode('utf-8')}</pre>"))
    else:
        # Error case with error styling
        display(
            HTML(
                f"<div style='color: red; font-weight: bold;'>Error occurred during execution:</div>"
            )
        )
        display(HTML(f"<pre style='color: red;'>{stderr.decode('utf-8')}</pre>"))


def is_json(myjson):
    """
    Check if a string is valid JSON
    """
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True
