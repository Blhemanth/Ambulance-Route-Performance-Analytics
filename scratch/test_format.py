import pandas as pd
df = pd.read_csv('data/processed/bengaluru_hospitals.csv')
labels = []
for _, r in df.iterrows():
    a = r.get("address")
    a_str = str(a).strip() if pd.notna(a) and str(a).strip() else "Bengaluru"
    labels.append(f"{r['hospital_name']} — {a_str[:35]}")
print(f"Successfully formatted all {len(labels)} labels without any TypeError!")
