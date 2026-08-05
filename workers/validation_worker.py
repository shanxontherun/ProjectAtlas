"""
Atlas Validation Worker.

Validates AI-generated content before it enters the publishing queue.
"""

from __future__ import annotations

from services.ai_service import (
    fetch_pending_validation,
    mark_validation_invalid,
    mark_validation_valid,
)

from validators.ai_content_validator import validate_ai_content


def main() -> None:
    """
    Validate all pending AI-generated content.
    """

    print("=" * 60)
    print("ATLAS VALIDATION WORKER")
    print("=" * 60)

    records = fetch_pending_validation()

    print(f"Found {len(records)} AI content record(s).\n")

    valid = 0
    invalid = 0
    warning_records = 0

    for record in records:

        ai_content_id = record["ai_content_id"]

        result = validate_ai_content(record)

        if result["valid"]:

            mark_validation_valid(ai_content_id)

            valid += 1

            print(f"[{ai_content_id}] VALID")

            if result["warnings"]:

                warning_records += 1

                print("    Warnings:")

                for warning in result["warnings"]:
                    print(f"      • {warning}")

            print()

        else:

            mark_validation_invalid(
                ai_content_id,
                "; ".join(result["errors"]),
            )

            invalid += 1

            print(f"[{ai_content_id}] INVALID")

            print("    Errors:")

            for error in result["errors"]:
                print(f"      • {error}")

            if result["warnings"]:

                warning_records += 1

                print("    Warnings:")

                for warning in result["warnings"]:
                    print(f"      • {warning}")

            print()

    print("=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print(f"Valid             : {valid}")
    print(f"Invalid           : {invalid}")
    print(f"Records Warned    : {warning_records}")
    print("=" * 60)


if __name__ == "__main__":
    main()