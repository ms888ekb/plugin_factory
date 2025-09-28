import os, shutil, zipfile, sys, pathlib

def zip_plugin(plugin_dir):
    plugin_dir = pathlib.Path(plugin_dir).resolve()
    name = plugin_dir.name
    out = plugin_dir.parent / f"{name}.zip"
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(plugin_dir):
            for f in files:
                if f.endswith((".pyc",)) or "__pycache__" in root:
                    continue
                fp = pathlib.Path(root) / f
                z.write(fp, arcname=str(fp.relative_to(plugin_dir)))
    print(f"Built: {out}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/build_zip.py plugins/hello_world")
        sys.exit(1)
    zip_plugin(sys.argv[1])