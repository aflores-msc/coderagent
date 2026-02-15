import pandas as pd
import os
import requests

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class DependencyInspectorAgent:
    def __init__(self, provider=None):
        self.provider = provider
        self.struct_template = {
            'version': None,
            'latest_version': 'Checking...',
            'status': 'unknown',
            'mvn_link': None,  # <--- NEW FIELD
            'error': None
        }

    def _get_latest_maven_version(self, group, name):
        """Queries Maven Central API for the latest version string."""
        try:
            url = f"https://search.maven.org/solrsearch/select?q=g:{group}+AND+a:{name}&rows=1&wt=json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                docs = data.get("response", {}).get("docs", [])
                if docs:
                    return docs[0].get("latestVersion")
            return "Not Found"
        except Exception:
            return "Connection Error"

    def check_project_dependencies(self, repo_path):
        """Parses libs.versions.toml and checks for updates."""
        catalog_path = os.path.join(repo_path, "gradle", "libs.versions.toml")
        if not os.path.exists(catalog_path):
            return pd.DataFrame()

        with open(catalog_path, "rb") as f:
            data = tomllib.load(f)

        versions = data.get("versions", {})
        libraries = data.get("libraries", {})
        results = []

        for alias, info in libraries.items():
            clean_status = self.struct_template.copy()
            group, name, local_version = None, None, "unknown"

            # Parse String format: "group:artifact:version"
            if isinstance(info, str):
                parts = info.split(":")
                if len(parts) == 3:
                    group, name, local_version = parts[0], parts[1], parts[2]

            # Parse Dictionary format
            elif isinstance(info, dict):
                module = info.get("module")
                if module:
                    m_parts = module.split(":")
                    group, name = m_parts[0], m_parts[1]
                else:
                    group = info.get("group")
                    name = info.get("name")

                v_data = info.get("version")
                if isinstance(v_data, dict) and "ref" in v_data:
                    local_version = versions.get(v_data["ref"], "unknown")
                else:
                    local_version = str(v_data) if v_data else "unknown"

            latest = self._get_latest_maven_version(group, name) if group and name else "unknown"

            # --- NEW: Generate MVNRepository Link ---
            mvn_link = None
            if group and name:
                mvn_link = f"https://mvnrepository.com/artifact/{group}/{name}"

            status = "up-to-date"
            if latest not in ["Not Found", "Connection Error", "unknown"] and latest != local_version:
                status = "outdated"

            clean_status.update({
                'version': local_version,
                'latest_version': latest,
                'status': status,
                'mvn_link': mvn_link  # <--- Save Link
            })
            results.append({'Package': alias, 'Current': clean_status, 'Required': 'Catalog defined'})

        return pd.DataFrame(results)

    def interpret_report(self, report_path):
        df = pd.read_parquet(report_path)
        details = pd.json_normalize(df['Current'])
        outdated_count = len(details[details['status'] == 'outdated'])
        return f"Audit complete. Found {outdated_count} libraries with newer versions available on Maven Central."

    def ask(self, prompt):
        return f"Response to: {prompt}"
