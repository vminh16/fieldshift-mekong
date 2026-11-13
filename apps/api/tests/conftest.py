import os
import tempfile

# Isolate DB + writable cache before fieldshift.settings is first read.
os.environ.setdefault("FIELDSHIFT_DATA_DIR", tempfile.mkdtemp(prefix="fieldshift-test-"))
