# Challenge 1: Docstring Generator

## Task

Generate a comprehensive Google-style docstring for the `process_transaction_batch` function in `function.py`.

## Requirements

Save your output to `outputs/output1.md`. The output MUST contain ALL of the following:

1. **Function description** — A clear explanation of what the function does
2. **Args section** — Every parameter listed with its type and description:
   - `transactions`
   - `currency_rates`
   - `base_currency`
   - `filters`
   - `include_metadata`
   - `max_retries`
3. **Returns section** — Description of the return value with type
4. **Examples section** — At least 2 usage examples with code
5. **Raises section** — All exceptions the function can raise (`ValueError`, `KeyError`)

## Validation Checks

The validator will check for:
- The word "Args" or "Parameters"
- The word "Returns"
- At least 2 code blocks (``` markers)
- The word "Raises" or "Exceptions"
- All 6 parameter names mentioned
- Both `ValueError` and `KeyError` mentioned
