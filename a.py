from databricks.sdk import WorkspaceClient

# This uses env vars or ~/.databrickscfg under the hood
w = WorkspaceClient()

# List files in your Volume
files = w.dbfs.list("/Volumes/pnc/pnc_volume/pnc")

for file_info in files:
    print(file_info.path)
