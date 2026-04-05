SKILL_IMPORTANCE = ["critical", "important", "nice-to-have"]
SKILL_TREND = ["growing", "stable", "declining"]
RESOURCE_TYPES = [
    "course",
    "book",
    "documentation",
    "official",
    "курс",
    "книга",
    "документация",
]


skill_item_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "importance": {"type": "string", "enum": SKILL_IMPORTANCE},
        "trend": {"type": "string", "enum": SKILL_TREND},
    },
    "required": ["name", "importance", "trend"],
}


skill_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "skill_map": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "languages": {"type": "array", "items": skill_item_schema, "minItems": 1},
                "frameworks": {"type": "array", "items": skill_item_schema, "minItems": 1},
                "infrastructure": {"type": "array", "items": skill_item_schema, "minItems": 1},
                "soft_skills": {"type": "array", "items": skill_item_schema, "minItems": 1},
            },
            "required": ["languages", "frameworks", "infrastructure", "soft_skills"],
        }
    },
    "required": ["skill_map"],
}


salary_cell_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "min": {"type": "number", "minimum": 0},
        "median": {"type": "number", "minimum": 0},
        "max": {"type": "number", "minimum": 0},
    },
    "required": ["min", "median", "max"],
}


region_salary_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "Junior": salary_cell_schema,
        "Middle": salary_cell_schema,
        "Senior": salary_cell_schema,
        "Lead": salary_cell_schema,
    },
    "required": ["Junior", "Middle", "Senior", "Lead"],
}


paygrade_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "salary_table": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "Moscow": region_salary_schema,
                "Russian_Regions": region_salary_schema,
                "Remote_USD": region_salary_schema,
            },
            "required": ["Moscow", "Russian_Regions", "Remote_USD"],
        },
        "market_trend": {"type": "string", "enum": SKILL_TREND},
        "market_trend_reason": {"type": "string", "minLength": 20, "maxLength": 500},
        "top_employers": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {"type": "string", "minLength": 1},
        },
    },
    "required": ["salary_table", "market_trend", "market_trend_reason", "top_employers"],
}


resource_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "type": {"type": "string", "enum": RESOURCE_TYPES},
    },
    "required": ["name", "type"],
}


phase_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "duration_days": {"type": "integer", "const": 30},
        "topics": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 2},
        "resources": {"type": "array", "items": resource_schema, "minItems": 2},
        "milestone": {"type": "string", "minLength": 10, "maxLength": 400},
    },
    "required": ["duration_days", "topics", "resources", "milestone"],
}


learning_path_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "Foundation": phase_schema,
        "Practice": phase_schema,
        "Portfolio": phase_schema,
    },
    "required": ["Foundation", "Practice", "Portfolio"],
}


gap_analysis_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "quick_wins": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "skill": {"type": "string", "minLength": 1},
                    "time_to_acquire_weeks": {"type": "integer", "minimum": 2, "maximum": 4},
                    "reason": {"type": "string", "minLength": 10, "maxLength": 250},
                },
                "required": ["skill", "time_to_acquire_weeks", "reason"],
            },
        },
        "long_term": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "skill": {"type": "string", "minLength": 1},
                    "time_to_acquire_months": {"type": "integer", "minimum": 3},
                    "reason": {"type": "string", "minLength": 10, "maxLength": 250},
                },
                "required": ["skill", "time_to_acquire_months", "reason"],
            },
        },
    },
    "required": ["quick_wins", "long_term"],
}


portfolio_project_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 5, "maxLength": 120},
        "description": {"type": "string", "minLength": 30, "maxLength": 1000},
        "technologies": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 3,
        },
        "skills_demonstrated": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 3,
        },
        "dataset_or_problem": {"type": "string", "minLength": 10, "maxLength": 500},
    },
    "required": [
        "name",
        "description",
        "technologies",
        "skills_demonstrated",
        "dataset_or_problem",
    ],
}


career_advice_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "learning_path": learning_path_schema,
        "gap_analysis": gap_analysis_schema,
        "portfolio_project": portfolio_project_schema,
    },
    "required": ["learning_path", "gap_analysis", "portfolio_project"],
}


verification_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "quality_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "quality_reason": {"type": "string", "minLength": 10, "maxLength": 700},
        "warnings": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "is_consistent": {"type": "boolean"},
    },
    "required": ["quality_score", "quality_reason", "warnings", "is_consistent"],
}
