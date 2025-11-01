# tools/echo_compile.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Compile a human-readable pipeline (DSL) into YAML.
Usage: python echo_compile.py input.echo -o output.yaml
"""
import sys
import yaml

def compile_pipeline(input_path, output_path):
    steps = []
    with open(input_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                name, module = line.split(":", 1)
                name = name.strip()
                module = module.strip()
                call = f"modules.{module}.run"
                steps.append({"name": name, "call": call})
    pipeline = {"steps": steps}
    with open(output_path, "w") as out:
        yaml.safe_dump(pipeline, out, sort_keys=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compile ArkEcho pipeline DSL to YAML.")
    parser.add_argument("input", help="Path to .echo pipeline file")
    parser.add_argument("-o", "--output", help="Path to output YAML file", required=True)
    args = parser.parse_args()
    compile_pipeline(args.input, args.output)
