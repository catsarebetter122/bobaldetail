from app import app
import routes  # noqa: F401
import os
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    app.run(host="0.0.0.0", port=port, debug=True)
