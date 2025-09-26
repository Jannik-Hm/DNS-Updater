from pydantic import ValidationError

def handleValidationError(e: ValidationError, additionalLocationInfo: str | None = None):
  # note: using print as logger might not be configured yet
  for error in e.errors():
    match error['type']:
      case "missing":
        print(f"Missing field(s) {".".join([str(item) for item in error['loc']])}" + (f" in {additionalLocationInfo}" if additionalLocationInfo else ""))
      case "int_parsing":
        print(f"Malformed number value `{error['input']}` at {".".join([str(item) for item in error['loc']])}")
      case "bool_parsing":
        print(f"Malformed boolean value `{error['input']}` at {".".join([str(item) for item in error['loc']])}")
      case _:
        # TODO: extend handlers as required
        print(f"Unknown config validation error: {error["type"]}; Message: {error['msg']}; Field: {", ".join([str(item) for item in error['loc']])}")
  exit(1)