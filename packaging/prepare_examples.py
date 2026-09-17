"""Generate redistributable synthetic example and backend validation cases."""
import csv
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
examples = root / 'examples'
examples.mkdir(exist_ok=True)
with (examples/'example.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['Time_s', 'Signal_A', 'Signal_B'])
    for i in range(1001):
        x = i/100
        writer.writerow([x, round(math.sin(x), 8), round(0.6*math.cos(x), 8)])
validation = root / 'package-validation'
validation.mkdir(exist_ok=True)
(validation/'positive.csv').write_text('X,Y,Z\n1,2,3\n2,4,9\n3,8,27\n4,16,81\n', encoding='utf-8')
for name, kind, ys, scale in [('scatter', 'scatter', ['Y'], 'linear'),
                               ('log-lines', 'line_scatter', ['Y','Z'], 'log10')]:
    recipe = {'schema_version': 1, 'x_column': 'X', 'y_columns': ys,
              'kind': kind, 'x_scale': scale, 'y_scale': scale,
              'x_label': 'X', 'y_label': 'Response'}
    (validation/(name+'.json')).write_text(json.dumps(recipe), encoding='utf-8')
print('Synthetic example and validation recipes prepared.')
