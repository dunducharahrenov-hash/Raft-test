import argparse
import datetime as dt
import json
import re
from pathlib import Path

from Agent_github import MultiAgentSystem
from tokens import GITHUB_MODEL


def utc_now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def role_slug(role):
    return re.sub(r"[^a-z0-9]+", "_", role.lower()).strip("_")


def save_log(log_path, lines):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_markdown(report):
    role = report["role"]
    skills = report["market_analysis"]["skill_map"]
    salary = report["salary_analysis"]["salary_table"]
    career = report["career_advice"]
    verification = report["verification"]

    lines = []
    lines.append(f"# Career Market Report: {role}")
    lines.append("")
    lines.append(f"- Generated at (UTC): {report['generated_at']}")
    lines.append(f"- Model: {report['model']}")
    lines.append(f"- Quality score: {verification['quality_score']}")
    lines.append(f"- Is consistent: {verification['is_consistent']}")
    lines.append("")

    lines.append("## 1. Skill Map")
    for category in ["languages", "frameworks", "infrastructure", "soft_skills"]:
        lines.append(f"### {category}")
        for item in skills.get(category, []):
            lines.append(
                f"- {item['name']} | importance: {item['importance']} | trend: {item['trend']}"
            )
        lines.append("")

    lines.append("## 2. Salary Table")
    for region in ["Moscow", "Russian_Regions", "Remote_USD"]:
        lines.append(f"### {region}")
        region_data = salary[region]
        for grade in ["Junior", "Middle", "Senior", "Lead"]:
            cell = region_data[grade]
            lines.append(
                f"- {grade}: min={cell['min']}, median={cell['median']}, max={cell['max']}"
            )
        lines.append("")
    lines.append(f"Market trend: {report['salary_analysis']['market_trend']}")
    lines.append(f"Reason: {report['salary_analysis']['market_trend_reason']}")
    lines.append(
        f"Top employers: {', '.join(report['salary_analysis']['top_employers'])}"
    )
    lines.append("")

    lines.append("## 3. Learning Path")
    learning_path = career["learning_path"]
    for phase in ["Foundation", "Practice", "Portfolio"]:
        phase_data = learning_path[phase]
        lines.append(f"### {phase} ({phase_data['duration_days']} days)")
        lines.append(f"Milestone: {phase_data['milestone']}")
        lines.append("Topics:")
        for topic in phase_data["topics"]:
            lines.append(f"- {topic}")
        lines.append("Resources:")
        for resource in phase_data["resources"]:
            lines.append(f"- {resource['name']} ({resource['type']})")
        lines.append("")

    lines.append("## 4. Gap Analysis")
    lines.append("### quick_wins")
    for item in career["gap_analysis"]["quick_wins"]:
        lines.append(
            f"- {item['skill']} ({item['time_to_acquire_weeks']} weeks): {item['reason']}"
        )
    lines.append("")
    lines.append("### long_term")
    for item in career["gap_analysis"]["long_term"]:
        lines.append(
            f"- {item['skill']} ({item['time_to_acquire_months']} months): {item['reason']}"
        )
    lines.append("")

    lines.append("## 5. Portfolio Project")
    project = career["portfolio_project"]
    lines.append(f"- Name: {project['name']}")
    lines.append(f"- Description: {project['description']}")
    lines.append(f"- Technologies: {', '.join(project['technologies'])}")
    lines.append(
        f"- Skills demonstrated: {', '.join(project['skills_demonstrated'])}"
    )
    if "dataset_or_problem" in project:
        lines.append(f"- Dataset/problem: {project['dataset_or_problem']}")
    lines.append("")

    lines.append("## 6. Verification")
    lines.append(f"- quality_score: {verification['quality_score']}")
    lines.append(f"- quality_reason: {verification['quality_reason']}")
    lines.append(f"- is_consistent: {verification['is_consistent']}")
    lines.append("- warnings:")
    for warning in verification["warnings"]:
        lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def build_report(role, model, skills, salary, career, verification, log_file):
    return {
        "generated_at": utc_now_iso(),
        "role": role,
        "provider": "github_models_inference",
        "model": model,
        "market_analysis": skills,
        "salary_analysis": salary,
        "career_advice": career,
        "verification": verification,
        "run_log_file": log_file,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Multi-agent IT career market analyzer"
    )
    parser.add_argument("--role", type=str, required=True, help="Role name to analyze")
    parser.add_argument("--model", type=str, default=GITHUB_MODEL, help="Model id")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory for report.json/report.md and logs",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite report.json/report.md if they exist"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    report_json = output_dir / "report.json"
    report_md = output_dir / "report.md"
    if not args.force and (report_json.exists() or report_md.exists()):
        suffix = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_json = output_dir / f"report_{suffix}.json"
        report_md = output_dir / f"report_{suffix}.md"

    log_path = logs_dir / (
        f"run_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{role_slug(args.role)}.log"
    )
    logs = []

    def log(message):
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        logs.append(line)
        print(line)

    try:
        log(f"Start run for role: {args.role}")
        log(f"Model: {args.model}")

        agent_system = MultiAgentSystem(model=args.model)

        log("Agent 1 started: market analysis")
        market_data = agent_system.market_analysis(args.role)
        log("Agent 1 done")

        log("Agent 2 started: salary evaluation")
        salary_data = agent_system.paygrade_evaluation(market_data)
        log("Agent 2 done")

        log("Agent 3 started: career advice")
        career_data = agent_system.career_advice(market_data, salary_data)
        log("Agent 3 done")

        verification_input = {
            "skill_map": market_data["skill_map"],
            "salary_table": salary_data["salary_table"],
            "market_trend": salary_data["market_trend"],
            "market_trend_reason": salary_data["market_trend_reason"],
            "top_employers": salary_data["top_employers"],
            "learning_path": career_data["learning_path"],
            "gap_analysis": career_data["gap_analysis"],
            "portfolio_project": career_data["portfolio_project"],
        }

        log("Agent 4 started: verification")
        verification_data = agent_system.verification(verification_input)
        log("Agent 4 done")

        report = build_report(
            role=args.role,
            model=args.model,
            skills=market_data,
            salary=salary_data,
            career=career_data,
            verification=verification_data,
            log_file=str(log_path.name),
        )

        report_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report_md.write_text(render_markdown(report), encoding="utf-8")

        log(f"Saved JSON: {report_json}")
        log(f"Saved Markdown: {report_md}")
        log(f"Saved log: {log_path}")
        save_log(log_path, logs)
    except Exception as exc:
        log(f"Run failed: {type(exc).__name__}: {exc}")
        save_log(log_path, logs)
        raise


if __name__ == "__main__":
    main()
