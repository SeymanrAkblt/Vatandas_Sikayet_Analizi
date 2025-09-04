# Vatandas_Sikayet_Analizi
Aşağıdaki metni doğrudan **README.md** dosyana yapıştırabilirsin. İçeriği mevcut repo yapına ve dosya isimlerine göre hazırladım; bölümler pratik adımlar içerir ve staj değerlendirmesi için de düzenlidir.

---

# Vatandaş Şikâyet Analizi

Bu repo, sosyal medya/şikâyet metinlerinden **“şikâyet mi değil mi?”** ve **“hangi kategori?”** sorularına yanıt verecek doğal dil işleme (NLP) modellerinin geliştirilmesi için hazırlanmış **Jupyter/Colab not defterlerini** ve eğitilmiş model klasörlerini içerir. Repo MIT lisanslıdır. ([GitHub][1])

---

## 🔎 Neler Var?

* **Not Defterleri (Jupyter/Colab)**

  * `temizleme.ipynb`: Metin temizleme ve veri ön işleme akışları
  * `sikayet_egitim_modeli.ipynb`: “Şikâyet / değil” sınıflandırma modeli eğitimi
  * `Kategori_Eğitim_Modeli.ipynb`: Kategori sınıflandırma modeli eğitimi
  * `Model_testi.ipynb`: Eğitilen modellerin test/örnek çıkarımları
  * `Kategori_Ekleme.ipynb`: Kategori setine sınıf ekleme/ince ayar akışları
    (Not defterlerinin isimleri ve varlığı repoda listelenmektedir.) ([GitHub][1])

* **Model Klasörü**

  * `models/berturk_kategori_modeli/`: Kategori sınıflandırma için BERTurk tabanlı model çıktı dizini (Hugging Face biçiminde kaydedilmiş olabilecek dosya yapısı). ([GitHub][1])

* **Lisans**

  * `LICENSE`: MIT lisansı. ([GitHub][1])

> Not: Repo ağırlıklı olarak **Jupyter Notebook (%80+) ve Python (%20-)** dosyalarından oluşur. ([GitHub][1])

---

## 🧰 Kurulum

### 1) Ortam (venv/conda)

```bash
# Projeyi klonla
git clone https://github.com/SeymanrAkblt/Vatandas_Sikayet_Analizi.git
cd Vatandas_Sikayet_Analizi

# Sanal ortam (Python 3.10+ önerilir)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2) Gerekli paketler (önerilen)

```bash
pip install --upgrade pip
pip install jupyter pandas numpy scikit-learn matplotlib
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentencepiece
```

> GPU kullanıyorsan PyTorch’u kendi CUDA sürümüne göre kur. (Yukarıda CPU için örnek verilmiştir.)

---

## ▶️ Çalıştırma

### Seçenek A — Yerel Jupyter

```bash
jupyter notebook
```

Açılan arayüzden ilgili `.ipynb` dosyalarını (örn. `temizleme.ipynb`, `sikayet_egitim_modeli.ipynb`, `Kategori_Eğitim_Modeli.ipynb`) sırayla çalıştır.

### Seçenek B — Google Colab

* Not defterlerini Colab’a yükleyip çalıştırabilirsin.
* Kendi Drive’ındaki veri/model yollarını defter içindeki hücrelerde güncellemeyi unutma.

---

## 🚀 Hızlı Demo: Kaydedilmiş Modelden Çıkarım

Aşağıdaki örnek, **Hugging Face Transformers** ile `models/berturk_kategori_modeli/` klasöründen bir metnin kategorisini tahmin etmeyi gösterir (klasör yapısı standart HF biçimindeyse):

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_DIR = "models/berturk_kategori_modeli"

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()

text = "Park alanlarında aydınlatma yetersiz, akşamları güvensiz hissediyoruz."
inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

with torch.inference_mode():
    outputs = model(**inputs)
    pred_id = outputs.logits.argmax(dim=-1).item()

print("Tahmin edilen kategori id:", pred_id)
```

> Kategori etiket adları (örn. `0: Ulaşım`, `1: Altyapı`, …) eğitimde kullandığın etiket sıralamasına göre değişir. Notebook içindeki “label mapping” kısmını baz al.

---

## 📁 Önerilen Çalışma Sırası

1. **Veri Temizleme/Keşif:** `temizleme.ipynb`
2. **Şikâyet Tespiti Eğitimi:** `sikayet_egitim_modeli.ipynb`
3. **Kategori Eğitimi:** `Kategori_Eğitim_Modeli.ipynb`
4. **Test & Doğrulama:** `Model_testi.ipynb`
5. **Kategori Güncellemeleri:** `Kategori_Ekleme.ipynb` ([GitHub][1])

---

## 🗂️ Klasör Yapısı (Özet)

```
Vatandas_Sikayet_Analizi/
├─ models/
│  └─ berturk_kategori_modeli/      # Eğitilmiş model dizini
├─ Kategori_Ekleme.ipynb
├─ Kategori_Eğitim_Modeli.ipynb
├─ Model_testi.ipynb
├─ sikayet_egitim_modeli.ipynb
├─ temizleme.ipynb
├─ .gitignore
├─ LICENSE                          # MIT
└─ README.md
```

(İsimler repo kökündeki listeye göredir.) ([GitHub][1])

---

## 📦 Veri & Büyük Dosyalar

* Büyük veri/model dosyalarını repoya koymak yerine **Git LFS** kullanman veya **Drive linki** vermen önerilir.
* `.gitignore` ile `data/`, `models/` içindeki ağır dosyaları hariç bırakabilirsin. (Repo’da `.gitignore` mevcuttur.) ([GitHub][1])

---

## 🧪 Değerlendirme

* Not defterlerinde eğitim/validasyon adımlarını koşup metrikleri (accuracy, F1 vb.) raporla.
* `Model_testi.ipynb` ile örnek metinler üzerinde hızlı kontrol yapabilirsin. ([GitHub][1])

---

## 🛣️ Yol Haritası (Öneri)

* Arayüz (Streamlit/PyQt) ile **canlı demo**: metin gir → şikâyet & kategori sonucu
* Mahalle/Kategori bazlı **grafikler** ve **filtreler**
* **Model versiyonlama** (etiketleme, değişim günlüğü)
* **Veri gizliliği** ve anonimleştirme kontrolleri

---

## 🤝 Katkı

* Issue/Pull Request açarak katkıda bulunabilirsin.
* Kod standartları ve veri gizliliği konularına dikkat et.

---

## 📄 Lisans

* Bu proje **MIT** lisansı ile sunulmaktadır. Ayrıntılar için `LICENSE` dosyasına bakınız. ([GitHub][1])

---

İstersen, README’ye **ekran görüntüsü/gif** koyman için bir `assets/` klasörü öneririm (ör. eğitim grafikleri, model demo ekranı). Ayrıca, yerel/Colab çalıştırma sırasında **özel veri yollarını** not defterleri içinde bir hücrede **“tek noktadan tanımla”** yöntemiyle ayarlanabilir yapmanı tavsiye ederim.

[1]: https://github.com/SeymanrAkblt/Vatandas_Sikayet_Analizi "GitHub - SeymanrAkblt/Vatandas_Sikayet_Analizi"
