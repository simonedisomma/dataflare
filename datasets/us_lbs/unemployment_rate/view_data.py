import os
import duckdb

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the data.parquet file
data_path = os.path.join(current_dir, 'data', 'data.parquet')

# Connect to an in-memory DuckDB database
conn = duckdb.connect(':memory:')

# Register the Parquet file directly with DuckDB
conn.execute(f"CREATE TABLE unemployment_rate AS SELECT * FROM parquet_scan('{data_path}')")

# Format the date column and round the unemployment_rate
conn.execute("""
    UPDATE unemployment_rate
    SET date = strftime(date, '%Y-%m-%d'),
        unemployment_rate = ROUND(unemployment_rate, 2)
""")

# Display the data in a simple tabular view
print(conn.execute("SELECT * FROM unemployment_rate ORDER BY date LIMIT 10").fetchdf())


# Execute the query
query = "SELECT unemployment_rate, date as time FROM unemployment_rate ORDER BY date LIMIT 12"
result = conn.execute(query).fetchall()

# Print the query results
print("\nDuckDB Query Results:")
print("Unemployment Rate | Time")
print("-" * 30)
for row in result:
    print(f"{row[0]:.2f}             | {row[1]}")

# Close the connection
conn.close()
