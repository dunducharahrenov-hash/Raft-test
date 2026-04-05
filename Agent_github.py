import json
import time

import requests

from Schemas import (
    SKILL_IMPORTANCE,
    SKILL_TREND,
    RESOURCE_TYPES,
    career_advice_schema,
    paygrade_schema,
    skill_schema,
    verification_schema,
)
from tokens import (
    GITHUB_API_BASE_URL,
    GITHUB_API_VERSION,
    GITHUB_MODEL,
    GITHUB_TOKEN,
    MAX_HTTP_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
    VALIDATION_RETRIES,
)


class AgentOutputError(RuntimeError):
    pass


class MultiAgentSystem:
    def __init__(self, model=None):
        self.model = model or GITHUB_MODEL
        if not GITHUB_TOKEN:
            raise RuntimeError(
                "GITHUB_TOKEN is empty. Set environment variable GITHUB_TOKEN before running."
            )

    def _post_with_retries(self, payload, stage):
        url = f"{GITHUB_API_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        }
        params = {"api-version": GITHUB_API_VERSION}

        last_error = None
        for attempt in range(1, MAX_HTTP_RETRIES + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    params=params,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                last_error = AgentOutputError(
                    f"{stage}: request error on attempt {attempt}: {exc}"
                )
                if attempt < MAX_HTTP_RETRIES:
                    time.sleep(2 * attempt)
                    continue
                raise last_error from exc

            if response.status_code == 200:
                return response

            if response.status_code == 503 and attempt < MAX_HTTP_RETRIES:
                time.sleep(3 * attempt)
                continue

            if response.status_code == 401:
                raise AgentOutputError(
                    f"{stage}: API error 401 Unauthorized. "
                    "Check GITHUB_TOKEN for GitHub Models access. "
                    f"Body: {response.text[:1200]}"
                )

            raise AgentOutputError(
                f"{stage}: API error {response.status_code}. Body: {response.text[:1200]}"
            )

        if last_error:
            raise last_error
        raise AgentOutputError(f"{stage}: request failed with unknown error.")

    @staticmethod
    def _extract_json_response(response, stage):
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise AgentOutputError(
                f"{stage}: provider returned non-JSON body: {response.text[:1200]}"
            ) from exc

        if isinstance(data, dict) and data.get("error"):
            raise AgentOutputError(f"{stage}: provider error payload: {data['error']}")

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AgentOutputError(
                f"{stage}: unexpected payload structure: {json.dumps(data)[:1200]}"
            ) from exc

        if isinstance(content, (dict, list)):
            return content

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AgentOutputError(
                f"{stage}: model did not return valid JSON content: {str(content)[:1200]}"
            ) from exc

    def _call_agent(self, stage, messages, schema, validator, max_tokens):
        working_messages = list(messages)
        last_error = None

        for attempt in range(1, VALIDATION_RETRIES + 1):
            payload = {
                "model": self.model,
                "messages": working_messages,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": f"{stage.replace(' ', '_')}_output",
                        "schema": schema,
                        "strict": True,
                    },
                },
                "temperature": 0.2,
                "max_tokens": max_tokens,
            }

            response = self._post_with_retries(payload, stage)
            data = self._extract_json_response(response, stage)

            error = validator(data)
            if not error:
                return data

            last_error = error
            if attempt < VALIDATION_RETRIES:
                working_messages = working_messages + [
                    {
                        "role": "assistant",
                        "content": json.dumps(data, ensure_ascii=False),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Проверка не пройдена.\n"
                            f"Ошибка: {error}\n"
                            "Сгенерируй полный JSON заново.\n"
                            "Верни только JSON."
                        ),
                    },
                ]

        raise AgentOutputError(f"{stage}: output validation failed: {last_error}")

    @staticmethod
    def _validate_skill_map(data):
        if not isinstance(data, dict):
            return "Top level must be an object."

        skill_map = data.get("skill_map")
        if not isinstance(skill_map, dict):
            return "Missing skill_map object."

        required_categories = ["languages", "frameworks", "infrastructure", "soft_skills"]
        for category in required_categories:
            items = skill_map.get(category)
            if not isinstance(items, list) or not items:
                return f"skill_map.{category} must be a non-empty array."
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    return f"skill_map.{category}[{idx}] must be an object."
                name = item.get("name")
                importance = item.get("importance")
                trend = item.get("trend")
                if not isinstance(name, str) or not name.strip():
                    return f"skill_map.{category}[{idx}].name must be non-empty string."
                if importance not in SKILL_IMPORTANCE:
                    return f"skill_map.{category}[{idx}].importance is invalid."
                if trend not in SKILL_TREND:
                    return f"skill_map.{category}[{idx}].trend is invalid."
        return None

    @staticmethod
    def _validate_salary_table(data):
        if not isinstance(data, dict):
            return "Top level must be an object."

        salary_table = data.get("salary_table")
        if not isinstance(salary_table, dict):
            return "Missing salary_table object."

        for region in ["Moscow", "Russian_Regions", "Remote_USD"]:
            region_data = salary_table.get(region)
            if not isinstance(region_data, dict):
                return f"salary_table.{region} must be an object."

            previous_median = None
            for grade in ["Junior", "Middle", "Senior", "Lead"]:
                cell = region_data.get(grade)
                if not isinstance(cell, dict):
                    return f"salary_table.{region}.{grade} must be an object."
                values = [cell.get("min"), cell.get("median"), cell.get("max")]
                if not all(isinstance(v, (int, float)) for v in values):
                    return f"salary_table.{region}.{grade} must contain numeric min/median/max."
                minimum, median, maximum = values
                if minimum > median or median > maximum:
                    return (
                        f"salary_table.{region}.{grade} must satisfy "
                        "min <= median <= max."
                    )
                if previous_median is not None and median <= previous_median:
                    return (
                        f"salary_table.{region} medians must strictly grow "
                        "from Junior to Lead."
                    )
                previous_median = median

        if data.get("market_trend") not in SKILL_TREND:
            return "market_trend must be one of growing/stable/declining."

        reason = data.get("market_trend_reason")
        if not isinstance(reason, str) or len(reason.strip()) < 20:
            return "market_trend_reason must be a meaningful string."

        employers = data.get("top_employers")
        if not isinstance(employers, list) or not (3 <= len(employers) <= 5):
            return "top_employers must contain 3 to 5 companies."
        if any(not isinstance(name, str) or not name.strip() for name in employers):
            return "top_employers must contain non-empty strings."
        return None

    @staticmethod
    def _validate_career_advice(data):
        if not isinstance(data, dict):
            return "Top level must be an object."

        learning_path = data.get("learning_path")
        if not isinstance(learning_path, dict):
            return "learning_path must be an object."

        for phase in ["Foundation", "Practice", "Portfolio"]:
            phase_data = learning_path.get(phase)
            if not isinstance(phase_data, dict):
                return f"learning_path.{phase} must be an object."
            if phase_data.get("duration_days") != 30:
                return f"learning_path.{phase}.duration_days must be 30."
            topics = phase_data.get("topics")
            resources = phase_data.get("resources")
            milestone = phase_data.get("milestone")
            if not isinstance(topics, list) or len(topics) < 2:
                return f"learning_path.{phase}.topics must have at least 2 items."
            if not isinstance(resources, list) or len(resources) < 2:
                return f"learning_path.{phase}.resources must have at least 2 items."
            for idx, resource in enumerate(resources):
                if not isinstance(resource, dict):
                    return f"learning_path.{phase}.resources[{idx}] must be an object."
                if not isinstance(resource.get("name"), str) or not resource["name"].strip():
                    return f"learning_path.{phase}.resources[{idx}].name must be non-empty."
                if resource.get("type") not in RESOURCE_TYPES:
                    return f"learning_path.{phase}.resources[{idx}].type is invalid."
            if not isinstance(milestone, str) or len(milestone.strip()) < 10:
                return f"learning_path.{phase}.milestone must be a meaningful string."

        gap_analysis = data.get("gap_analysis")
        if not isinstance(gap_analysis, dict):
            return "gap_analysis must be an object."

        quick_wins = gap_analysis.get("quick_wins")
        long_term = gap_analysis.get("long_term")
        if not isinstance(quick_wins, list) or len(quick_wins) < 1:
            return "gap_analysis.quick_wins must be a non-empty array."
        if not isinstance(long_term, list) or len(long_term) < 1:
            return "gap_analysis.long_term must be a non-empty array."

        for idx, item in enumerate(quick_wins):
            if not isinstance(item, dict):
                return f"gap_analysis.quick_wins[{idx}] must be an object."
            weeks = item.get("time_to_acquire_weeks")
            if not isinstance(weeks, int) or weeks < 2 or weeks > 4:
                return f"gap_analysis.quick_wins[{idx}] must be 2-4 weeks."

        for idx, item in enumerate(long_term):
            if not isinstance(item, dict):
                return f"gap_analysis.long_term[{idx}] must be an object."
            months = item.get("time_to_acquire_months")
            if not isinstance(months, int) or months < 3:
                return f"gap_analysis.long_term[{idx}] must be at least 3 months."

        project = data.get("portfolio_project")
        if not isinstance(project, dict):
            return "portfolio_project must be an object."
        for key in ["name", "description", "technologies", "skills_demonstrated"]:
            if key not in project:
                return f"portfolio_project.{key} is required."
        for key in ["technologies", "skills_demonstrated"]:
            values = project.get(key)
            if not isinstance(values, list) or len(values) < 3:
                return f"portfolio_project.{key} must contain at least 3 items."
        return None

    @staticmethod
    def _validate_verification(data):
        if not isinstance(data, dict):
            return "Top level must be an object."
        score = data.get("quality_score")
        reason = data.get("quality_reason")
        warnings = data.get("warnings")
        consistent = data.get("is_consistent")

        if not isinstance(score, int) or score < 0 or score > 100:
            return "quality_score must be integer 0..100."
        if not isinstance(reason, str) or len(reason.strip()) < 10:
            return "quality_reason must be a meaningful string."
        if not isinstance(warnings, list):
            return "warnings must be an array."
        if any(not isinstance(w, str) or not w.strip() for w in warnings):
            return "warnings must contain non-empty strings."
        if not isinstance(consistent, bool):
            return "is_consistent must be boolean."
        return None

    @staticmethod
    def _format_prompt(agent_name, objective, input_contract, output_contract, rules):
        rule_lines = "\n".join(f"- {rule}" for rule in rules)
        return (
            f"Агент: {agent_name}\n"
            f"Цель: {objective}\n"
            f"Входной контракт: {input_contract}\n"
            f"Выходной контракт: {output_contract}\n"
            f"Правила:\n{rule_lines}\n"
            "Политика формата ответа: верни только валидный JSON, полностью соответствующий схеме."
        )

    def market_analysis(self, role_name):
        system_prompt = self._format_prompt(
            agent_name="Агент 1 - Аналитик рынка",
            objective="Сформировать карту навыков для выбранной роли с фокусом на рынке.",
            input_contract="Строка с названием роли.",
            output_contract=(
                "JSON с skill_map по категориям: languages, frameworks, infrastructure, soft_skills."
            ),
            rules=[
                "Каждый навык должен содержать name, importance, trend.",
                "importance должен быть одним из critical, important, nice-to-have.",
                "trend должен быть одним из growing, stable, declining.",
                "Не добавляй пояснений вне JSON.",
            ],
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Роль: {role_name}\n"
                    "Сформируй skill_map для этой роли по выходному контракту."
                ),
            },
        ]
        return self._call_agent(
            stage="market analysis",
            messages=messages,
            schema=skill_schema,
            validator=self._validate_skill_map,
            max_tokens=2200,
        )

    def paygrade_evaluation(self, skill_data):
        system_prompt = self._format_prompt(
            agent_name="Агент 2 - Оценщик зарплат",
            objective="Оценить зарплатные вилки по грейдам и регионам на основе skill_map.",
            input_contract="JSON skill_map от Агента 1.",
            output_contract=(
                "JSON с salary_table, market_trend, market_trend_reason, top_employers."
            ),
            rules=[
                "Составь salary_table - должно включать регионы Moscow, Russian_Regions, Remote_USD.",
                "Каждый регион должен включать Junior, Middle, Senior, Lead с min/median/max.",
                "Для каждой ячейки соблюдай min <= median <= max и логический рост по грейдам.",
                "Для Moscow и Russian_Regions используй тыс. RUB (тысячи рублей), для Remote_USD — USD (доллары США).",
                "Составь оценку market_trend - должен содержать значение из growing / stable / declining.",
                "Составь пояснение оценки (market_trend) market_trend_reason - объяснять причину выбора growing / stable / declining.",
                "Составь список top_employers - должен содержать от 3 до 5 реальных компаний.",
            ],
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Входные данные skill JSON:\n"
                    f"{json.dumps(skill_data, ensure_ascii=False)}"
                ),
            },
        ]
        return self._call_agent(
            stage="salary evaluation",
            messages=messages,
            schema=paygrade_schema,
            validator=self._validate_salary_table,
            max_tokens=2600,
        )

    def career_advice(self, skill_data, salary_data):
        system_prompt = self._format_prompt(
            agent_name="Агент 3 - Карьерный советник",
            objective="Сформировать 90-дневный план обучения и портфолио на основе рынка и зарплат.",
            input_contract="skill_map от Агента 1 и salary_table от Агента 2.",
            output_contract="JSON с learning_path, gap_analysis, portfolio_project.",
            rules=[
                "Составь план learning_path - должен состоять из фаз Foundation, Practice, Portfolio.",
                "Каждая фаза в learning_path длится 30 дней и содержит минимум 2 ресурса.",
                "Составь gap_analysis - должен содержать цели quick_wins — 2–4 недели, long_term — от 3 месяцев.",
                "Подбери portfolio_project - должен включать name, description, technologies, skills_demonstrated. Предпочтительно продемонстрировать 3 и более технологий из skill_map.",
                "Не добавляй пояснений вне JSON.",
            ],
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Входной JSON от предыдущих агентов:\n"
                    f"{json.dumps({'skill_map': skill_data.get('skill_map', {}), 'salary_table': salary_data.get('salary_table', {})}, ensure_ascii=False)}"
                ),
            },
        ]
        return self._call_agent(
            stage="career advice",
            messages=messages,
            schema=career_advice_schema,
            validator=self._validate_career_advice,
            max_tokens=3200,
        )

    def verification(self, full_report_data):
        system_prompt = self._format_prompt(
            agent_name="Агент 4 - Критик и верификатор",
            objective="Оценить согласованность и качество итогового отчёта. Заполнить quality_score, quality_reason, warnings, is_consistent.",
            input_contract="Полный JSON от Агентов 1–3.",
            output_contract="JSON с quality_score, quality_reason, warnings, is_consistent.",
            rules=[
                "Проверь, есть ли в отчёте несогласованности, например: увеличиваются ли зарплаты соответственно уровню навыков.",
                "Проверь, усть ли в отчёте противоречия, например:  declining-навыки приоритизированы в learning_path. В случае обнаружения добавь предупреждение в warnings.",
                "Оцнени общее качесво отчёта с учётом warnings и согласованности целым числом от 0 до 100. Запиши оценку в  quality_score.",
                "Поясни причину оценки в quality_reason.",
                "is_consistent = true только при отсутствии серьезных противоречий и оценке quality_score .",
            ],
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Входной полный JSON отчета:\n"
                    f"{json.dumps(full_report_data, ensure_ascii=False)}"
                ),
            },
        ]
        return self._call_agent(
            stage="verification",
            messages=messages,
            schema=verification_schema,
            validator=self._validate_verification,
            max_tokens=1800,
        )
