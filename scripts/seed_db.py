#!/usr/bin/env python3
import asyncio, json, os, sys, hashlib, argparse, math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sqlalchemy.dialects.postgresql import insert
from app.models.models import Building, Base
from app.database import engine, AsyncSessionLocal


def make_id(cj_id: str) -> str:
    return hashlib.md5(cj_id.encode()).hexdigest()[:12]


def svy21_to_wgs84(N, E):
    """Convert SVY21 (Northing, Easting) to WGS84 (lat, lng)."""
    # SVY21 origin: lat=1.366666, lng=103.833333
    a = 6378137.0          # WGS84 semi-major axis
    f = 1 / 298.257223563
    b = a * (1 - f)
    e2 = 1 - (b/a)**2
    e_prime2 = (a/b)**2 - 1

    # SVY21 projection constants
    N0 = 38744.572         # False Northing
    E0 = 28001.642         # False Easting
    k0 = 1.0               # Scale factor
    lat0 = math.radians(1 + 22/60 + 2.9154/3600)   # 1°22'02.9154"N
    lng0 = math.radians(103 + 49/60 + 31.9987/3600) # 103°49'31.9987"E

    Nv = N - N0
    Ev = E - E0

    M0 = a * ((1 - e2/4 - 3*e2**2/64) * lat0
              - (3*e2/8 + 3*e2**2/32) * math.sin(2*lat0)
              + (15*e2**2/256) * math.sin(4*lat0))

    M = M0 + Nv / k0
    mu = M / (a * (1 - e2/4 - 3*e2**2/64))

    e1 = (1 - math.sqrt(1-e2)) / (1 + math.sqrt(1-e2))
    lat1 = (mu
            + (3*e1/2 - 27*e1**3/32) * math.sin(2*mu)
            + (21*e1**2/16 - 55*e1**4/32) * math.sin(4*mu)
            + (151*e1**3/96) * math.sin(6*mu))

    N1 = a / math.sqrt(1 - e2 * math.sin(lat1)**2)
    T1 = math.tan(lat1)**2
    C1 = e_prime2 * math.cos(lat1)**2
    R1 = a*(1-e2) / (1 - e2*math.sin(lat1)**2)**1.5
    D  = Ev / (N1 * k0)

    lat = lat1 - (N1*math.tan(lat1)/R1) * (
        D**2/2
        - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e_prime2) * D**4/24
        + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*e_prime2 - 3*C1**2) * D**6/720
    )
    lng = lng0 + (
        D
        - (1 + 2*T1 + C1) * D**3/6
        + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*e_prime2 + 24*T1**2) * D**5/120
    ) / math.cos(lat1)

    return math.degrees(lat), math.degrees(lng)


def get_centroid(city_obj, vertices):
    xs, ys = [], []

    def collect(b):
        if isinstance(b, list):
            for i in b:
                collect(i)
        elif isinstance(b, int) and b < len(vertices):
            v = vertices[b]
            xs.append(v[0])   # Easting
            ys.append(v[1])   # Northing

    for geom in city_obj.get("geometry", []):
        collect(geom.get("boundaries", []))

    if not xs:
        return None, None

    avg_e = sum(xs) / len(xs)
    avg_n = sum(ys) / len(ys)
    return svy21_to_wgs84(avg_n, avg_e)


async def seed(path: str):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"Loading {path} ...")
    with open(path) as f:
        data = json.load(f)

    city_objects = data["CityObjects"]
    vertices = data.get("vertices", [])
    print(f"Total CityObjects: {len(city_objects)}")

    buildings = []
    skipped = 0
    for cj_id, obj in city_objects.items():
        attrs = obj.get("attributes", {})
        blk    = str(attrs.get("hdb_blk_no", "")).strip()
        street = str(attrs.get("hdb_street", "")).strip()
        if not blk or not street:
            skipped += 1
            continue

        lat, lng = get_centroid(obj, vertices)
        if lat is None:
            skipped += 1
            continue

        if not (1.1 <= lat <= 1.5 and 103.5 <= lng <= 104.1):
            skipped += 1
            continue

        buildings.append(dict(
            id=make_id(cj_id),
            blk_no=blk,
            street=street,
            address=f"BLK {blk} {street}, SINGAPORE",
            dwelling_units=int(attrs.get("hdb_total_dwelling_units", 0) or 0),
            room_1=int(attrs.get("hdb_1room_sold", 0) or 0),
            room_2=int(attrs.get("hdb_2room_sold", 0) or 0),
            room_3=int(attrs.get("hdb_3room_sold", 0) or 0),
            room_4=int(attrs.get("hdb_4room_sold", 0) or 0),
            room_5=int(attrs.get("hdb_5room_sold", 0) or 0),
            latitude=lat,
            longitude=lng,
            cityjson_id=cj_id,
        ))

    print(f"Parsed {len(buildings)} buildings, skipped {skipped}")

    async with AsyncSessionLocal() as db:
        for b in buildings:
            stmt = insert(Building).values(**b).on_conflict_do_nothing(
                index_elements=["id"])
            await db.execute(stmt)
        await db.commit()

    print(f"✅ Seeded {len(buildings)} buildings.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hdb-json", default="/assets/hdb.json")
    args = parser.parse_args()
    asyncio.run(seed(args.hdb_json))
