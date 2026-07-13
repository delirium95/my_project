"""AWS Lambda entry point for API Gateway or a Lambda Function URL."""

from mangum import Mangum

from boutique.main import app

# The container and database engine are created once per warm Lambda environment. The
# FastAPI shutdown lifespan is disabled because Lambda has no reliable process-shutdown
# signal; SERVERLESS=true selects SQLAlchemy NullPool for this adapter.
handler = Mangum(app, lifespan="off")
