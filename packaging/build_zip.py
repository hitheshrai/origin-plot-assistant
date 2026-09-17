from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
wheel = root / 'dist/origin_plot_assistant-0.1.0-py3-none-any.whl'
if not wheel.exists():
    raise SystemExit('Build the wheel first.')
destination = root / 'dist/Origin-Plot-Assistant-0.1.0-Windows.zip'
with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for source, name in [(wheel, wheel.name), (root/'packaging/Start.cmd', 'Start.cmd'),
                         (root/'packaging/Start.ps1', 'Start.ps1'),
                         (root/'packaging/constraints.txt', 'constraints.txt'),
                         (root/'PACKAGE_GUIDE.md', 'README.md'),
                         (root/'examples/example.csv', 'example.csv')]:
        archive.write(source, 'Origin-Plot-Assistant/' + name)
print(destination)
