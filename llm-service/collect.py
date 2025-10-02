import os

def collect_code(output_file="all_code.txt", extensions=None):
    if extensions is None:
        # можно ограничить, чтобы не собирать бинарники
        extensions = [".py", ".js", ".ts", ".html", ".css", ".json", ".md", ".txt", ".java", ".cpp", ".c", ".cs"]

    root_dir = os.getcwd()
    with open(output_file, "w", encoding="utf-8") as out:
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(fpath, root_dir)

                # проверка расширения
                if not any(fname.endswith(ext) for ext in extensions):
                    continue

                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"⚠️ Пропускаю {rel_path}: {e}")
                    continue

                out.write(f"# path: {rel_path}\n")
                out.write(content)
                out.write("\n\n")  # разделитель

if __name__ == "__main__":
    collect_code()
    print("✅ Код собран в all_code.txt")
