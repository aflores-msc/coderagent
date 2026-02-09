import re


def run_static_analysis(file_content: str, filename: str) -> list[str]:
    """
    Analyzes Java code for Critical Bugs, Dead Code, and Modernization Opportunities.
    Returns a list of specific issues.
    """
    issues = []

    # --- 1. CRITICAL & SECURITY ---
    if re.search(r'@Autowired\s+private', file_content):
        issues.append("❌ [CRITICAL] Field Injection detected. Use Constructor Injection.")

    if "System.out.println" in file_content:
        issues.append("⚠️ [WARN] System.out.println found. Use SLF4J Logger.")

    if "e.printStackTrace()" in file_content:
        issues.append("⚠️ [WARN] e.printStackTrace() found. Use `log.error(e)`.")

    # --- 2. CLASSIC DEAD CODE (The "Clean Up" Phase) ---

    # A. Unused Imports
    # Find all imports, then check if the class name is used elsewhere in the file.
    imports = re.findall(r'import\s+[\w\.]+\.([A-Z]\w+);', file_content)
    for class_name in imports:
        # Regex: Look for the class name as a "whole word" (\b)
        # count=1 means it only appears in the import line itself.
        matches = len(re.findall(r'\b' + re.escape(class_name) + r'\b', file_content))
        if matches == 1:
            issues.append(f"🧹 [DEAD CODE] Unused Import: `{class_name}`")

    # B. Unused Private Fields
    # Skip if Lombok is used (as it generates getters/setters implicitly)
    if not any(x in file_content for x in ["@Data", "@Getter", "@Value"]):
        # Regex: private (final?) Type name;
        fields = re.findall(r'private\s+(?:final\s+)?[\w<>]+\s+(\w+)\s*[;=]', file_content)
        for field_name in fields:
            # Check if field is used anywhere else
            matches = len(re.findall(r'\b' + re.escape(field_name) + r'\b', file_content))
            if matches < 2:
                issues.append(f"🧟 [DEAD CODE] Unused Private Field: `{field_name}`")

    # --- 3. MODERN JAVA 17+ OPPORTUNITIES ---

    # A. Text Blocks (Java 15)
    # Detects: "SELECT * " + \n "FROM table"
    if file_content.count(' + "\\n" + ') > 0 or file_content.count(' + "\n" + ') > 0:
        issues.append("💡 [MODERNIZE] Multi-line string concatenation detected. Use Text Blocks (`\"\"\"`).")

    # B. Pattern Matching for Instanceof (Java 16)
    # Detects: if (obj instanceof String) ... (String) obj
    if re.search(r'instanceof\s+(\w+)', file_content) and re.search(r'\(\w+\)\s*\w+', file_content):
        issues.append("💡 [MODERNIZE] Legacy casting detected. Use Pattern Matching: `if (obj instanceof String s)`.")

    # C. Arrow Switch (Java 14)
    # Detects: case CONSTANT: ... break;
    if re.search(r'case\s+[^:]+:', file_content) and "break;" in file_content:
        issues.append("💡 [MODERNIZE] Legacy Switch detected. Use Switch Expressions (`case X -> ...`).")

    # D. Stream.toList() (Java 16)
    if ".collect(Collectors.toList())" in file_content:
        issues.append("💡 [MODERNIZE] Replace `.collect(Collectors.toList())` with `.toList()`.")

    return issues
