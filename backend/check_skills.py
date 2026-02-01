from sqlalchemy import create_engine, text
from app.db.session import DATABASE_URL

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) as cnt, COUNT(subcategory_id) as with_subcat FROM skills'))
    row = result.fetchone()
    total = row[0]
    with_subcat = row[1]
    null_subcat = total - with_subcat
    print(f'Total skills: {total}')
    print(f'With subcategory: {with_subcat}')
    print(f'NULL subcategory: {null_subcat}')
