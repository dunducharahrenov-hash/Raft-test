# Мультиагентная система анализа карьерного рынка IT

## RU
### Запуск

1. Установите переменные окружения (см. `.env.example`).
2. Выполните:

```bash
python main.py --role "Backend Python Developer"
```

Дополнительные флаги:

--role - Должность для анализа (строка)

--force - Перезаписывать существующие report.json и report.md вместо создания новых с временными метками.

```bash
python main.py --role "ML Engineer" --model "openai/gpt-4o" --output-dir "./examples/TC-02"
python main.py --role "iOS Developer (Swift)" --force
```

### Агенты

1. Агент 1 (`market_analysis`): возвращает `skill_map`.
2. Агент 2 (`paygrade_evaluation`): возвращает `salary_table`, `market_trend`, `market_trend_reason`, `top_employers`.
3. Агент 3 (`career_advice`): возвращает `learning_path`, `gap_analysis`, `portfolio_project`.
4. Агент 4 (`verification`): возвращает `quality_score`, `quality_reason`, `warnings`, `is_consistent`.

Агенты выполняются строго последовательно. Контекст передаётся явно через аргументы функций.

### Результаты

Каждый запуск сохраняет:

- `report.json`
- `report.md`
- `logs/run_<timestamp>_<role>.log`

`report.json` включает `generated_at` и `run_log_file`.

### Папка examples

Используйте ту же команду `main.py` с `--output-dir` для создания обязательных тестовых примеров:

- `examples/TC-01` для `"Backend Python Developer"`
- `examples/TC-02` для `"ML Engineer"`
- `examples/TC-03` для `"iOS Developer (Swift)"`

Или сгенерируйте все три последовательно:

```bash
python generate_examples.py
```

## EN

### Run

1. Set environment variables (see `.env.example`).
2. Run:

```bash
python main.py --role "Backend Python Developer"
```

Optional flags:

--role - Position to review (string)

--force - Include to overwrite existing report.json and report.md instead of creating new with timestamps.

```bash
python main.py --role "ML Engineer" --model "openai/gpt-4o" --output-dir "./examples/TC-02"
python main.py --role "iOS Developer (Swift)" --force
```

### Agents

1. Agent 1 (`market_analysis`): returns `skill_map`.
2. Agent 2 (`paygrade_evaluation`): returns `salary_table`, `market_trend`, `market_trend_reason`, `top_employers`.
3. Agent 3 (`career_advice`): returns `learning_path`, `gap_analysis`, `portfolio_project`.
4. Agent 4 (`verification`): returns `quality_score`, `quality_reason`, `warnings`, `is_consistent`.

Agents run strictly in sequence. Context is passed explicitly through function arguments.

### Output

Each run saves:

- `report.json`
- `report.md`
- `logs/run_<timestamp>_<role>.log`

`report.json` includes `generated_at` and `run_log_file`.

### Examples Folder

Use the same `main.py` command with `--output-dir` to generate mandatory test-case examples:

- `examples/TC-01` for `"Backend Python Developer"`
- `examples/TC-02` for `"ML Engineer"`
- `examples/TC-03` for `"iOS Developer (Swift)"`

Or generate all three in sequence:

```bash
python generate_examples.py
```
