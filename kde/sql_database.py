from sqlalchemy import create_engine, types
import pandas as pd

sample_file = 'data/gps-data/part-00001-498c167d-fb29-4098-a9f9-682631b98b93-c000.snappy'
all_data = pd.read_parquet(sample_file)
all_data['timestamp'] = all_data['timestamp'].apply(lambda x: str(x))
all_data['way_id'] = all_data['way_id'].apply(lambda x: str(x))
all_data['record_index'] = all_data.index
all_data = all_data[['record_index', 'accuracy', 'altitude', 'bearing', 'location', 'route_slug', 'speed', 'timestamp', 'dest_session', 'device_id', 'way_id', 'dir']]
engine = create_engine(f'mysql://root:Peyman_Bi101@127.0.0.1/gps_data')

all_data.to_sql(name='gps_records', con=engine, if_exists='append', dtype={
    'record_index': types.Integer(),
    'accuracy': types.Float(),
    'altitude': types.Float(),
    'bearing': types.Float(),
    'location': types.String(64),
    'route_slug': types.String(64),
    'speed': types.Float(),
    'timestamp': types.String(16),
    'dest_session': types.String(32),
    'device_id': types.String(64),
    'way_id': types.String(16),
    'dir': types.Integer()
},index=False)

with engine.connect() as con:
    con.execute('ALTER TABLE gps_records ADD PRIMARY KEY (record_index);')


