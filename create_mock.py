import asyncio, hashlib, os, random
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert
from app.database import Base
from app.models.models import Building

engine = create_async_engine(os.getenv('DATABASE_URL'))
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

# Real Singapore HDB towns with approximate lat/lng centres
TOWNS = [
    ('ANG MO KIO', 1.3691, 103.8454),
    ('BEDOK', 1.3236, 103.9273),
    ('BISHAN', 1.3526, 103.8352),
    ('BUKIT BATOK', 1.3490, 103.7490),
    ('BUKIT MERAH', 1.2819, 103.8239),
    ('BUKIT PANJANG', 1.3774, 103.7719),
    ('BUKIT TIMAH', 1.3294, 103.7964),
    ('CENTRAL AREA', 1.2897, 103.8501),
    ('CHOA CHU KANG', 1.3840, 103.7470),
    ('CLEMENTI', 1.3152, 103.7649),
    ('GEYLANG', 1.3201, 103.8918),
    ('HOUGANG', 1.3612, 103.8863),
    ('JURONG EAST', 1.3329, 103.7436),
    ('JURONG WEST', 1.3404, 103.7090),
    ('KALLANG', 1.3100, 103.8700),
    ('MARINE PARADE', 1.3021, 103.9071),
    ('PASIR RIS', 1.3721, 103.9474),
    ('PUNGGOL', 1.4019, 103.9022),
    ('QUEENSTOWN', 1.2942, 103.7861),
    ('SEMBAWANG', 1.4491, 103.8200),
    ('SENGKANG', 1.3868, 103.8914),
    ('SERANGOON', 1.3554, 103.8679),
    ('TAMPINES', 1.3496, 103.9568),
    ('TOA PAYOH', 1.3343, 103.8563),
    ('WOODLANDS', 1.4382, 103.7891),
    ('YISHUN', 1.4304, 103.8354),
]

STREET_SUFFIXES = ['AVE', 'STREET', 'ROAD', 'DRIVE', 'CRESCENT', 'CLOSE', 'PLACE', 'WALK']

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    buildings = []
    for town, base_lat, base_lng in TOWNS:
        # Generate 30-80 blocks per town
        num_blocks = random.randint(30, 80)
        for i in range(1, num_blocks + 1):
            blk = str(random.randint(100, 999)) + random.choice(['', 'A', 'B', 'C'])
            street_num = random.randint(1, 20)
            suffix = random.choice(STREET_SUFFIXES)
            street = f'{town} {suffix} {street_num}'

            # Scatter blocks around town centre
            lat = base_lat + random.uniform(-0.015, 0.015)
            lng = base_lng + random.uniform(-0.015, 0.015)

            # Realistic unit counts
            floors = random.randint(4, 40)
            units_per_floor = random.choice([4, 6, 8, 10])
            total_units = floors * units_per_floor

            r1 = random.randint(0, total_units // 10)
            r2 = random.randint(0, total_units // 8)
            r3 = random.randint(0, total_units // 4)
            r4 = random.randint(0, total_units // 3)
            r5 = max(0, total_units - r1 - r2 - r3 - r4)

            bid = hashlib.md5(f'{blk}_{street}'.upper().replace(' ','_').encode()).hexdigest()[:12]
            buildings.append(dict(
                id=bid, blk_no=blk, street=street,
                address=f'BLK {blk} {street}, SINGAPORE',
                dwelling_units=total_units,
                room_1=r1, room_2=r2, room_3=r3, room_4=r4, room_5=r5,
                latitude=lat, longitude=lng,
                cityjson_id=None,
            ))

    async with AsyncSession() as db:
        for b in buildings:
            stmt = insert(Building).values(**b).on_conflict_do_nothing(index_elements=['id'])
            await db.execute(stmt)
        await db.commit()

    print(f'Seeded {len(buildings)} synthetic HDB buildings across {len(TOWNS)} towns.')

asyncio.run(seed())