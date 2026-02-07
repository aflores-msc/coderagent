import re

def run_static_analysis(file_content: str, filename: str) -> list[str]:
    """
    Returns a list of strict errors found in the code using Regex.
    """
    issues = []

    # RULE 1: NO FIELD INJECTION
    # Regex explanation:
    # 1. Look for @Autowired
    # 2. Followed by whitespace/newlines
    # 3. Followed by 'private' (without a constructor or method in between)
    if re.search(r'@Autowired\s+private', file_content):
        issues.append(f"❌ [CRITICAL] Field Injection detected in {filename}. "
                      "Use Constructor Injection instead.")

    # RULE 2: NO SYSTEM OUT
    if "System.out.println" in file_content:
        issues.append(f"⚠️ [WARN] System.out.println found in {filename}. "
                      "Use a Logger (Slf4j) instead.")

    # RULE 3: GENERIC EXCEPTIONS
    if "throws Exception" in file_content:
        issues.append(f"⚠️ [WARN] Generic 'throws Exception' found in {filename}. "
                      "Be specific.")

    return issues
