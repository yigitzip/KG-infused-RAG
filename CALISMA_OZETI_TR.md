# KG-Infused RAG — Wikidata5M ve Neo4j: Şu Ana Kadar Yapılanlar

Bu belge, projenin veri katmanı (Phase 1 odaklı) için yapılan işleri özetler. **Phase 2** (alan yoğunluğu raporları, görselleştirme) ekip arkadaşı tarafından devam ettirilecek.

---

## 1. Veri kaynağı

- **Wikidata5M** ham dosyalar (`Downloads` altındaki `wikidata5m_raw_data`):
  - `wikidata5m_all_triplet.txt` — üçlüler (`head`, `property`, `tail`, tab ile ayrılmış)
  - `wikidata5m_text.txt` — varlık açıklamaları
  - `wikidata5m_alias/wikidata5m_entity.txt` — varlık takma adları

---

## 2. Tam graf yerine proje odaklı alt küme

Ders slaytlarına uygun olarak **tüm 21M tripleti** doğrudan Neo4j’e almak yerine:

1. **`scripts/build_turkey_project_subset.py`** çalıştırıldı:
   - Metin ve alias içinde *turkey / türkiye / …* anahtar kelimeleri
   - **Q43**’ün özne veya nesne olduğu tüm üçlülerin uçları
   - Futbol, sinema, şirket, müzik, akademi için birleşik **Wikidata P-id** listesiyle iç kenar süzme
   - İsteğe bağlı genişleme (`--expand-hops`)
2. Çıktı: **`turkey_project_triplets.tsv`** ve **`turkey_project_report.json`** (ilişki sayıları, alan grupları, şehir kabulleri)

Böylece Neo4j tarafı **daha hafif ve proje kapsamına uygun** bir alt graf ile yüklendi.

---

## 3. Neo4j bulk import için CSV üretimi

- **`scripts/wikidata5m_triplets_to_neo4j_csv.py`**:
  - Girdi: filtrelenmiş `.tsv` (+ isteğe bağlı `wikidata5m_text.txt` isimleri için)
  - Çıktı: **`entities.csv`**, **`relationships.csv`**
  - Açıklama metinlerindeki tırnak/satır sonu sorunları için **`csv.writer`** ve metin sadeleştirme kullanıldı (Neo4j import hatasını önlemek için)

Bu CSV’ler masaüstünde örneğin:

`~/Desktop/neo4j_import_turkey_project/`

---

## 4. Neo4j Desktop ve içe aktarma

- Yerel instance: **wikidata5m** (Neo4j Desktop, `neo4j-desktop` veri yolu altındaki `dbms-…` klasörü).
- **Java 21** (Temurin) kuruldu; `neo4j-admin` terminalden çalıştırıldı.
- Veritabanı **durdurulmuş**ken:

  `neo4j-admin database import full neo4j … --nodes=Entity=…/entities.csv --relationships=…/relationships.csv`

- Yaklaşık **2.41M düğüm**, **~10.46M ilişki** başarıyla içe aktarıldı.

---

## 5. Sorgu ve test

- Desktop’ta **Connect → Query** ile Cypher çalıştırıldı.
- **Q43** ve ilişki dağılımı için örnek sorgular verildi; **`cypher/q43_analysis.cypher`** dosyasında özet sorgular var.

---

## 6. Repodaki betikler ve dosyalar

| Yol | Amaç |
|-----|------|
| `scripts/wikidata5m_triplets_to_neo4j_csv.py` | Triplet TSV → Neo4j import CSV |
| `scripts/build_turkey_project_subset.py` | Slayt uyumlu Türkiye/proje alt kümesi + JSON rapor |
| `scripts/filter_subgraph_by_seed.py` | Yalnızca Q43’ten k-hop alt graf (alternatif) |
| `scripts/verify_reasoning_paths.py` | JSON’daki `reasoning_path` ifadelerini triplet dosyasında doğrulama |
| `scripts/domain_verify_turkish_cinema.py` | Türk sineması tohum metrikleri (ham/filtre triplet üzerinde) |
| `scripts/run_neo4j_admin_import.sh` | `neo4j-admin` komut hatırlatması |
| `cypher/q43_analysis.cypher` | Q43 örnek analiz sorguları |
| `data/verified_questions.sample.json` | Çoklu-atımlı soru JSON formatı için **örnek** (tam 50 soruluk set repoda ayrıca tamamlanmalı) |

---

## 7. Bilinçli tercihler ve notlar

- **Tam 21M** yerine **filtrelenmiş** alt küme: disk, süre ve ödev kapsamı için.
- **`verified_questions.json` (50 soru)** bir süre repo dışında kaldı; teslim için **`data/`** altına tam liste konmalı ve `verify_reasoning_paths.py` ile triplet dosyasına karşı doğrulanmalı.
- Phase 2 raporu (10 tohum, ortalama komşu, 30+ iki-atımlı yol, grafikler) — **arkadaşın sorumluluğunda**; bu özet Phase 1 + altyapıyı anlatır.

---
