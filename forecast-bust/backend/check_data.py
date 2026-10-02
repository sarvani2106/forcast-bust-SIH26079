import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as connection:

    result = connection.execute(
        text("SELECT COUNT(*) FROM forecast_data")
    )

    count = result.scalar()

    print("Rows in database:", count)