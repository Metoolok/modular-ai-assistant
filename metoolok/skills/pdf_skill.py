import PyPDF2
import os
import re
from datetime import datetime
from collections import Counter
from .base import BaseSkill


class PDFReaderSkill(BaseSkill):
    """
    Metoolok Gelişmiş PDF Analiz Modülü

    Özellikler:
        - 🤖 AI Destekli Akıllı Özet: Gerçek içerik analizi
        - 📊 Otomatik İçindekiler Çıkarımı
        - 🔍 Gelişmiş Arama: Bağlam ile birlikte sonuçlar
        - 📈 İstatistiksel Analiz: Kelime frekansı, sayfa analizi
        - 🎯 Konu Tespit: Otomatik kategori belirleme
        - 💾 Çoklu PDF Yönetimi: Birden fazla döküman hafızası
        - 🔖 Yer İmi (Bookmark) Desteği
        - 📑 Sayfa Bazlı Okuma
    """
    name = "pdf"
    keywords = [
        "pdf", "document", "dosya", "oku", "belge", "summary", "analiz",
        "extract", "anlat", "özet", "içindekiler", "sayfa", "bölüm"
    ]
    description = "PDF dökümanlarını akıllıca okur, özetler, analiz eder ve içinde gelişmiş arama yapar."

    def __init__(self, data_manager=None):
        super().__init__(data_manager)
        self.pdf_library = {}  # Çoklu PDF saklama: {filename: {text, metadata, ...}}
        self.current_pdf = None  # Aktif döküman

    async def execute(self, args: str) -> str:
        """PDF işlemlerini yöneten ana metod."""
        args_lower = args.lower()

        # 1. HAFIZA KONTROLÜ - Otomatik PDF yükleme
        if not self.current_pdf and self.data_manager:
            last_file = self.data_manager.context_memory.get("last_uploaded_file")
            if last_file and last_file.endswith(".pdf"):
                self.load_pdf(last_file)

        try:
            # Durum A: PDF Yükleme
            if "/temp/" in args or args.endswith(".pdf") or "yükle" in args_lower or "load" in args_lower:
                file_path = args.split()[-1] if " " in args else args
                return self.load_pdf(file_path)

            # Durum B: Akıllı Özet
            if any(word in args_lower for word in ["özet", "summary", "anlat", "analiz"]):
                return self.smart_summary()

            # Durum C: İçindekiler
            if "içindekiler" in args_lower or "toc" in args_lower or "başlık" in args_lower:
                return self.extract_table_of_contents()

            # Durum D: Gelişmiş Arama
            if any(word in args_lower for word in ["search:", "ara:", "bul:"]):
                query = args.split(":", 1)[1].strip() if ":" in args else args.replace("pdf", "").strip()
                return self.advanced_search(query)

            # Durum E: Sayfa Okuma
            if "sayfa" in args_lower or "page" in args_lower:
                try:
                    page_num = int(''.join(filter(str.isdigit, args)))
                    return self.read_page(page_num)
                except:
                    return "⚠️ Sayfa numarası belirtmelisiniz. Örn: `pdf sayfa 5`"

            # Durum F: İstatistikler
            if "istatistik" in args_lower or "stats" in args_lower:
                return self.get_statistics()

            # Durum G: Konu Analizi
            if "konu" in args_lower or "topic" in args_lower or "kategori" in args_lower:
                return self.detect_topics()

            # Durum H: Döküman Listesi
            if "liste" in args_lower or "list" in args_lower:
                return self.list_documents()

            # Durum I: Döküman Değiştir
            if "değiştir" in args_lower or "switch" in args_lower:
                filename = args.split()[-1]
                return self.switch_document(filename)

            return self.show_help()

        except Exception as e:
            self.logger.error(f"PDF Execute Error: {e}")
            return self.format_error(f"İşlem hatası: {str(e)}")

    def load_pdf(self, file_path: str) -> str:
        """PDF'i yükler ve gelişmiş metadata çıkarır"""
        try:
            if not os.path.exists(file_path):
                return "❌ Dosya bulunamadı."

            filename = os.path.basename(file_path)

            # PDF okuma
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)

                # Metadata çıkarımı
                metadata = {
                    "title": reader.metadata.title if reader.metadata and reader.metadata.title else filename,
                    "author": reader.metadata.author if reader.metadata and reader.metadata.author else "Bilinmiyor",
                    "pages": len(reader.pages),
                    "created": reader.metadata.creation_date if reader.metadata and hasattr(reader.metadata,
                                                                                            'creation_date') else None
                }

                # Tam metin çıkarımı
                full_text = []
                page_texts = {}

                for i, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(page_text)
                        page_texts[i] = page_text

                combined_text = "\n".join(full_text)

                # Dökümanı kütüphaneye ekle
                self.pdf_library[filename] = {
                    "text": combined_text,
                    "pages": page_texts,
                    "metadata": metadata,
                    "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "word_count": len(combined_text.split()),
                    "char_count": len(combined_text)
                }

                self.current_pdf = filename

                return (
                    f"### ✅ PDF Başarıyla Yüklendi\n\n"
                    f"**📄 Döküman:** {metadata['title']}\n"
                    f"**✍️ Yazar:** {metadata['author']}\n"
                    f"**📑 Sayfa Sayısı:** {metadata['pages']}\n"
                    f"**📊 Kelime Sayısı:** ~{self.pdf_library[filename]['word_count']:,}\n"
                    f"**🕐 Yükleme:** {self.pdf_library[filename]['loaded_at']}\n\n"
                    f"💡 *Şimdi `pdf özet` veya `pdf içindekiler` komutlarını kullanabilirsin!*"
                )

        except Exception as e:
            self.logger.error(f"PDF Load Error: {e}")
            return f"❌ Yükleme hatası: {str(e)}"

    def smart_summary(self) -> str:
        """ULTRA GELİŞMİŞ ÖZET MOTORU - v3.0"""
        if not self.current_pdf:
            return "⚠️ Önce bir PDF yükleyin."

        doc = self.pdf_library[self.current_pdf]
        text = doc["text"]
        pages = doc["metadata"]["pages"]

        # ============ AŞAMA 1: METİN TEMİZLİĞİ ============
        # OCR hatalarını düzelt
        text = self._fix_ocr_errors(text)

        # ============ AŞAMA 2: YAPISAL ANALİZ ============
        # Başlıkları tespit et
        headers = self._detect_headers(text)

        # Bölümlere ayır
        sections = self._split_into_sections(text, headers)

        # ============ AŞAMA 3: ANLAMLI İÇERİK ÇIKARIMI ============
        meaningful_content = []

        for section_name, section_text in sections.items():
            # Her bölümden en iyi paragrafları al
            paragraphs = self._extract_quality_paragraphs(section_text)

            for para in paragraphs[:2]:  # Her bölümden max 2 paragraf
                score = self._calculate_content_quality(para, text)
                if score > 5.0:  # Kalite eşiği
                    meaningful_content.append({
                        'text': para,
                        'score': score,
                        'section': section_name
                    })

        # Skora göre sırala
        meaningful_content.sort(key=lambda x: x['score'], reverse=True)

        if not meaningful_content:
            return self._fallback_summary(doc, text)

        # ============ AŞAMA 4: AKILLI ÖZET OLUŞTURMA ============
        summary_parts = {
            'intro': None,
            'main_points': [],
            'conclusion': None
        }

        # En iyi 6 içeriği seç ve kategorize et
        top_content = meaningful_content[:6]

        # İlk içerik genelde giriş
        if top_content:
            summary_parts['intro'] = top_content[0]['text']

        # Orta içerikler ana noktalar
        if len(top_content) > 2:
            summary_parts['main_points'] = [item['text'] for item in top_content[1:-1]]

        # Son içerik sonuç
        if len(top_content) > 1:
            summary_parts['conclusion'] = top_content[-1]['text']

        # ============ AŞAMA 5: TEMA VE KAVRAM ANALİZİ ============
        themes = self._extract_themes(text)
        main_concepts = self._extract_key_concepts(text)
        timeline = self._extract_timeline(text)

        # ============ AŞAMA 6: FORMATLAMA ============
        summary = f"### 📄 {doc['metadata']['title']} - Detaylı Özet\n\n"

        # Ana tema
        if themes:
            summary += f"**🎯 Konu:** {themes[0]}\n"

        # Zaman çizelgesi varsa
        if timeline:
            summary += f"**📅 Dönem:** {', '.join(timeline[:3])}\n"

        # Ana kavramlar
        if main_concepts:
            summary += f"**💡 Anahtar Kavramlar:** {', '.join(main_concepts[:6])}\n"

        summary += "\n---\n\n"

        # GİRİŞ
        if summary_parts['intro']:
            intro_clean = self._polish_text(summary_parts['intro'])
            if len(intro_clean) > 50:  # Anlamlı mı kontrol et
                summary += f"**📖 Döküman Hakkında:**\n\n{intro_clean}\n\n"

        # ANA NOKTALAR
        if summary_parts['main_points']:
            summary += "**📝 Önemli Bilgiler:**\n\n"
            for idx, point in enumerate(summary_parts['main_points'], 1):
                point_clean = self._polish_text(point)
                if len(point_clean) > 50:
                    # Çok uzunsa kısalt
                    if len(point_clean) > 350:
                        point_clean = point_clean[:350] + "..."
                    summary += f"**{idx}.** {point_clean}\n\n"

        # SONUÇ
        if summary_parts['conclusion']:
            conclusion_clean = self._polish_text(summary_parts['conclusion'])
            if len(conclusion_clean) > 50:
                summary += f"**🎯 Önemli Sonuç:**\n\n{conclusion_clean}\n\n"

        # ============ AŞAMA 7: EK BİLGİLER ============
        summary += "---\n\n"
        summary += "**📊 Döküman Bilgileri:**\n"
        summary += f"- 📄 Sayfa: {pages}\n"
        summary += f"- 📝 Kelime: ~{doc['word_count']:,}\n"
        summary += f"- ⏱️ Okuma: ~{doc['word_count'] // 200} dk\n\n"

        # Keşfedilecek konular
        if headers:
            summary += "**📑 Başlıca Konular:**\n"
            for header in headers[:5]:
                summary += f"- {header}\n"
            summary += "\n"

        summary += (
            "💡 **Daha Fazlası İçin:**\n"
            "• `pdf içindekiler` → Tüm başlıkları gör\n"
            "• `pdf search: [konu]` → Spesifik bilgi ara\n"
            "• `pdf sayfa [no]` → Belirli sayfayı oku\n"
            "• `pdf konu` → Detaylı konu analizi"
        )

        return summary

    def _fix_ocr_errors(self, text: str) -> str:
        """OCR hatalarını düzeltir"""
        # Yaygın OCR hataları
        fixes = {
            r'\bİ ttihat\b': 'İttihat',
            r'\bT erakki\b': 'Terakki',
            r'\bK kat\b': 'Kkat',
            r'\bO smanlı\b': 'Osmanlı',
            r'\bİ stanbul\b': 'İstanbul',
            r'\b(\w)\s+(\w{1,2})\s+(\w)\b': r'\1\2\3',  # "M u stafa" -> "Mustafa"
        }

        for pattern, replacement in fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Çoklu boşlukları temizle
        text = re.sub(r'\s+', ' ', text)

        return text

    def _detect_headers(self, text: str) -> list:
        """Başlıkları tespit eder"""
        lines = text.split('\n')
        headers = []

        for line in lines:
            line = line.strip()

            # Boş veya çok uzun satırları atla
            if len(line) < 5 or len(line) > 100:
                continue

            # Başlık kriterleri
            is_header = False

            # 1. Tamamen büyük harf
            if line.isupper() and 5 < len(line) < 60:
                is_header = True

            # 2. Rakam ile başlayan (1., 2., I., II., vb.)
            if re.match(r'^[\dIVX]+[\.\)]\s+[A-ZÇĞİÖŞÜ]', line):
                is_header = True

            # 3. ÜNİTE, BÖLÜM, KONU gibi kelimeler
            header_keywords = ['ünite', 'bölüm', 'konu', 'kısım', 'fasıl', 'madde']
            if any(kw in line.lower() for kw in header_keywords) and len(line.split()) < 10:
                is_header = True

            # 4. Çok az kelime + büyük harfle başlayan her kelime
            words = line.split()
            if len(words) <= 8 and all(w[0].isupper() for w in words if len(w) > 2):
                is_header = True

            if is_header and line not in headers:
                headers.append(line)

        return headers

    def _split_into_sections(self, text: str, headers: list) -> dict:
        """Metni bölümlere ayırır"""
        if not headers:
            return {"Ana İçerik": text}

        sections = {}
        lines = text.split('\n')
        current_section = "Giriş"
        current_content = []

        for line in lines:
            # Bu satır başlık mı?
            if line.strip() in headers:
                # Önceki bölümü kaydet
                if current_content:
                    sections[current_section] = '\n'.join(current_content)

                # Yeni bölüm başlat
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)

        # Son bölümü kaydet
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _extract_quality_paragraphs(self, text: str) -> list:
        """Kaliteli paragrafları çıkarır"""
        # Hem \n\n hem de tek \n ile ayır
        potential_paras = []

        # Çift satır sonları
        for p in text.split('\n\n'):
            potential_paras.append(p.strip())

        # Tek satır sonları (kısa paragraflar için)
        for p in text.split('\n'):
            p = p.strip()
            if len(p) > 80:  # Yeterince uzun
                potential_paras.append(p)

        # Filtreleme
        quality_paras = []
        for p in potential_paras:
            # Minimum kalite kontrolleri
            if len(p) < 80:  # Çok kısa
                continue
            if len(p) > 1000:  # Çok uzun
                continue
            if self._is_junk_paragraph(p):  # Gereksiz
                continue

            # Cümle var mı?
            sentences = [s for s in re.split(r'[.!?]', p) if len(s.strip()) > 20]
            if len(sentences) < 1:
                continue

            quality_paras.append(p)

        return quality_paras

    def _calculate_content_quality(self, text: str, full_text: str) -> float:
        """İçerik kalitesini hesaplar"""
        score = 0.0

        # 1. Uzunluk skoru (ideal: 150-450 karakter)
        length = len(text)
        if 150 <= length <= 450:
            score += 3.0
        elif 100 <= length <= 600:
            score += 1.5

        # 2. Cümle yapısı
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 15]
        if 2 <= len(sentences) <= 6:
            score += 2.5
        elif len(sentences) >= 1:
            score += 1.0

        # 3. İçerik zenginliği (farklı kelime oranı)
        words = text.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            score += unique_ratio * 3

        # 4. Önemli kelimeler
        important_words = [
            'sonuç', 'önemli', 'öncelikle', 'dolayısıyla', 'böylece',
            'savaş', 'antlaşma', 'dönem', 'devlet', 'başlangıç', 'süreç'
        ]
        text_lower = text.lower()
        for word in important_words:
            if word in text_lower:
                score += 0.8

        # 5. Tarih/yıl içeriyor mu?
        if re.search(r'\b1[789]\d{2}\b|\b20\d{2}\b', text):
            score += 1.5

        # 6. İsim içeriyor mu?
        capital_words = re.findall(r'\b[A-ZÇĞİÖŞÜ][a-züçğıöşü]+\b', text)
        if len(capital_words) >= 2:
            score += 1.0

        # 7. Noktalama kullanımı
        punctuation_count = text.count('.') + text.count(',') + text.count(';')
        if punctuation_count >= 3:
            score += 1.0

        # 8. Anahtar kelime yoğunluğu
        keywords = self.extract_keywords(full_text, 15)
        keyword_matches = sum(1 for kw in keywords if kw in text_lower)
        score += keyword_matches * 0.4

        return score

    def _extract_key_concepts(self, text: str) -> list:
        """Önemli kavramları çıkarır"""
        # Büyük harfli kelime grupları (2-3 kelimelik)
        patterns = [
            r'\b[A-ZÇĞİÖŞÜ][a-züçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-züçğıöşü]+){0,2}\b',
            r'\b[A-ZÇĞİÖŞÜ][a-züçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-züçğıöşü]+\b'
        ]

        concepts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            concepts.extend(matches)

        # Frekans analizi
        concept_freq = Counter(concepts)

        # Gereksizleri filtrele
        stop_words = {'Bu', 'Bir', 'Bu Nedenle', 'Bunlar', 'Böylece', 'Sonra', 'Önce', 'İlk', 'DİKKAT', 'NOT'}

        filtered = [
            concept for concept, count in concept_freq.most_common(20)
            if count >= 2 and concept not in stop_words and len(concept) > 3
        ]

        return filtered[:10]

    def _extract_timeline(self, text: str) -> list:
        """Tarih/yıl bilgilerini çıkarır"""
        # Yıl tespiti (1800-2099)
        years = re.findall(r'\b(1[89]\d{2}|20\d{2})\b', text)
        year_freq = Counter(years)

        # En sık geçen 5 yıl
        return [year for year, _ in year_freq.most_common(5)]

    def _polish_text(self, text: str) -> str:
        """Metni cilalar, okunaklı hale getirir"""
        # Gereksiz boşlukları temizle
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Cümle başlarını düzelt
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]

        # Noktalama düzeltmeleri
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Noktalamadan önce boşluk olmasın
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)  # Noktalamadan sonra boşluk

        # Çift noktalama
        text = re.sub(r'\.{2,}', '.', text)

        # Son nokta yoksa ekle (eğer tam cümle ise)
        if text and text[-1] not in '.!?':
            if len(text.split()) > 5:  # En az 5 kelime varsa cümle sayılır
                text += '.'

        return text

    def _fallback_summary(self, doc: dict, text: str) -> str:
        """Yedek özet metodu - içerik çıkarılamazsa"""
        # İlk 1500 karakteri akıllıca al
        preview = text[:1500]

        # Tam cümlede bitir
        last_period = preview.rfind('.')
        if last_period > 500:
            preview = preview[:last_period + 1]

        preview = self._polish_text(preview)

        keywords = self.extract_keywords(text, 12)
        themes = self._extract_themes(text)

        return (
            f"### 📄 {doc['metadata']['title']} - Özet\n\n"
            f"**🎯 Konu:** {themes[0] if themes else 'Genel'}\n"
            f"**🔑 Anahtar Kelimeler:** {', '.join(keywords[:8])}\n\n"
            f"---\n\n"
            f"**📖 Döküman Önizleme:**\n\n"
            f"{preview}\n\n"
            f"---\n\n"
            f"**📊 Bilgi:** {doc['metadata']['pages']} sayfa, ~{doc['word_count']:,} kelime\n\n"
            f"💡 *Detaylı okuma: `pdf sayfa 1` veya `pdf içindekiler`*"
        )

    def _is_junk_paragraph(self, text: str) -> bool:
        """Gereksiz/anlamsız paragraf kontrolü"""
        text = text.strip()

        # Çok kısa
        if len(text) < 30:
            return True

        # Çoğunlukla rakam veya sembol
        alpha_chars = sum(c.isalpha() for c in text)
        if alpha_chars / max(len(text), 1) < 0.5:
            return True

        # Gereksiz tekrarlar
        words = text.split()
        if len(words) > 0 and len(set(words)) / len(words) < 0.3:
            return True

        # Sayfa numarası, başlık vb. kalıplar
        junk_patterns = [
            r'^\d+\s*$',  # Sadece sayfa numarası
            r'^sayfa\s+\d+',
            r'^page\s+\d+',
            r'^www\.',
            r'^http',
            r'^\[.*\]$',  # Sadece referans
            r'^DİKKAT:',  # Bilgi kutusu
            r'^NOT:',  # Not kutusu
        ]
        for pattern in junk_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        return False

    def _extract_themes(self, text: str) -> list:
        """Ana temaları çıkarır"""
        text_lower = text.lower()

        # Tema sözlüğü
        theme_dict = {
            "Tarih - Osmanlı Dönemi": ["osmanlı", "padişah", "sultan", "imparatorluk", "saray"],
            "Tarih - Cumhuriyet": ["atatürk", "mustafa kemal", "cumhuriyet", "inkılap", "meclis"],
            "Tarih - Savaşlar": ["savaş", "muharebe", "cephe", "ordu", "zafer", "mütareke", "balkan"],
            "Edebiyat": ["şair", "yazar", "roman", "şiir", "eser", "edebiyat"],
            "Bilim": ["bilim", "araştırma", "deney", "teori", "hipotez", "sonuç"],
            "Felsefe": ["düşünce", "felsefe", "mantık", "akıl", "bilgi", "hakikat"],
            "Ekonomi": ["ekonomi", "ticaret", "pazar", "para", "fiyat", "üretim"],
            "Eğitim": ["eğitim", "öğretim", "okul", "öğrenci", "ders", "müfredat"],
            "Hukuk": ["hukuk", "kanun", "yasa", "mahkeme", "hak", "adalet"],
            "Sanat": ["sanat", "resim", "müzik", "tiyatro", "eser", "sanatçı"]
        }

        theme_scores = {}
        for theme, keywords in theme_dict.items():
            score = sum(text_lower.count(kw) for kw in keywords)
            if score > 0:
                theme_scores[theme] = score

        # Sıralı tema listesi
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, _ in sorted_themes[:3]]

    def extract_table_of_contents(self) -> str:
        """Otomatik içindekiler/başlık yapısını çıkarır"""
        if not self.current_pdf:
            return "⚠️ Önce bir PDF yükleyin."

        doc = self.pdf_library[self.current_pdf]
        text = doc["text"]

        # Başlık tespit et
        headers = self._detect_headers(text)

        if not headers:
            return "📑 Otomatik içindekiler tespit edilemedi. Döküman yapılandırılmamış olabilir."

        # İçindekiler formatı
        toc_lines = ["### 📑 İçindekiler\n"]
        for idx, header in enumerate(headers[:20], 1):  # İlk 20 başlık
            toc_lines.append(f"{idx}. {header}")

        return "\n".join(toc_lines) + f"\n\n*Toplam {len(headers)} başlık tespit edildi.*"

    def advanced_search(self, query: str) -> str:
        """Gelişmiş arama - bağlam ile birlikte sonuçlar"""
        if not self.current_pdf:
            return "⚠️ Önce bir PDF yükleyin."

        doc = self.pdf_library[self.current_pdf]
        text = doc["text"]

        # Arama algoritması
        lines = text.split("\n")
        matches = []

        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                # Bağlam: Önceki ve sonraki satırlar
                context_before = lines[max(0, i - 1)] if i > 0 else ""
                context_after = lines[min(len(lines) - 1, i + 1)] if i < len(lines) - 1 else ""

                matches.append({
                    "line": line.strip(),
                    "before": context_before.strip(),
                    "after": context_after.strip(),
                    "line_num": i
                })

        if not matches:
            # Fuzzy search - benzer kelimeler
            similar = self.find_similar_words(query, text)
            if similar:
                return f"🔍 **'{query}'** bulunamadı.\n\n**Benzer:** {', '.join(similar[:5])}"
            return f"🔍 **'{query}'** döküman içinde bulunamadı."

        # Sonuçları formatla
        result = [f"### 🔍 '{query}' Arama Sonuçları ({len(matches)} eşleşme)\n"]

        for idx, match in enumerate(matches[:8], 1):  # İlk 8 sonuç
            result.append(
                f"**{idx}. Sonuç (Satır {match['line_num']}):**\n"
                f"_{match['before']}_\n"
                f"**→ {match['line']}**\n"
                f"_{match['after']}_\n"
            )

        if len(matches) > 8:
            result.append(f"\n*...ve {len(matches) - 8} sonuç daha*")

        return "\n".join(result)

    def read_page(self, page_num: int) -> str:
        """Belirli bir sayfayı okur"""
        if not self.current_pdf:
            return "⚠️ Önce bir PDF yükleyin."

        doc = self.pdf_library[self.current_pdf]

        if page_num < 1 or page_num > doc["metadata"]["pages"]:
            return f"⚠️ Geçersiz sayfa. Döküman {doc['metadata']['pages']} sayfa içeriyor."

        page_text = doc["pages"].get(page_num, "")

        if not page_text:
            return f"⚠️ Sayfa {page_num} boş veya okunamıyor."

        # Sayfa özeti
        preview = page_text[:1500] if len(page_text) > 1500 else page_text

        return (
            f"### 📄 Sayfa {page_num} / {doc['metadata']['pages']}\n\n"
            f"{preview}\n\n"
            f"{'...' if len(page_text) > 1500 else ''}\n"
            f"*Kelime sayısı: ~{len(page_text.split())}*"
        )

    def get_statistics(self) -> str:
        """Döküman istatistikleri"""
        if not self.current_pdf:
            return "⚠️ Önce bir PDF yükleyin."

        doc = self.pdf_library[self.current_pdf]
        text = doc["text"]

        # İstatistikler
        words = text.split()
        unique_words = set(word.lower() for word in words if word.isalpha())
        sentences = [s for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        paragraphs = [p for p in text.split("\n\n") if len(p.strip()) > 20]

        # En sık kullanılan kelimeler
        word_freq = Counter(word.lower() for word in words if len(word) > 3 and word.isalpha())
        top_words = word_freq.most_common(15)

        # Sayfa başına ortalama
        avg_words_per_page = doc["word_count"] // doc["metadata"]["pages"]

        return (
            f"### 📊 {doc['metadata']['title']} - İstatistikler\n\n"
            f"**📄 Genel:**\n"
            f"- Toplam Sayfa: {doc['metadata']['pages']}\n"
            f"- Toplam Kelime: {doc['word_count']:,}\n"
            f"- Benzersiz Kelime: {len(unique_words):,}\n"
            f"- Toplam Cümle: ~{len(sentences):,}\n"
            f"- Toplam Paragraf: ~{len(paragraphs):,}\n\n"
            f"**📈 Ortalamalar:**\n"
            f"- Sayfa Başına Kelime: ~{avg_words_per_page}\n"
            f"- Cümle Başına Kelime: ~{doc['word_count'] // max(len(sentences), 1)}\n\n"
            f"**🔝 En Sık Kullanılan Kelimeler:**\n"
            + "\n".join([f"- {word}: {count}x" for word, count in top_words[:10]])
        )

    def detect_topics(self) -> str:
        """Otomatik konu/kategori tespiti"""
        if not self.current_pdf:
            return "⚠️ Önce bir PDF yükleyin."

        doc = self.pdf_library[self.current_pdf]
        text = doc["text"].lower()

        # Konu kategorileri
        topics = {
            "Matematik": ["matematik", "denklem", "formül", "sayı", "hesap", "geometri", "algebra"],
            "Fizik": ["fizik", "kuvvet", "enerji", "hareket", "hız", "momentum"],
            "Kimya": ["kimya", "molekül", "atom", "reaksiyon", "element", "bileşik"],
            "Biyoloji": ["biyoloji", "hücre", "dna", "protein", "organizma", "evrim"],
            "Tarih": ["tarih", "savaş", "devlet", "imparatorluk", "kültür", "uygarlık"],
            "Edebiyat": ["edebiyat", "roman", "şiir", "öykü", "yazar", "eser"],
            "Teknoloji": ["teknoloji", "bilgisayar", "yazılım", "internet", "dijital", "ai", "yapay zeka"],
            "İşletme": ["şirket", "pazarlama", "yönetim", "strateji", "müşteri", "satış"],
            "Hukuk": ["hukuk", "kanun", "mahkeme", "dava", "yargı", "suç"],
            "Tıp": ["tıp", "hastalık", "tedavi", "ilaç", "doktor", "sağlık"]
        }

        detected = {}
        for topic, keywords in topics.items():
            score = sum(text.count(kw) for kw in keywords)
            if score > 0:
                detected[topic] = score

        if not detected:
            return "🎯 Belirgin bir konu kategorisi tespit edilemedi."

        # Sıralama
        sorted_topics = sorted(detected.items(), key=lambda x: x[1], reverse=True)

        result = ["### 🎯 Döküman Konu Analizi\n"]
        for topic, score in sorted_topics[:5]:
            percentage = (score / sum(detected.values())) * 100
            result.append(f"- **{topic}**: %{percentage:.1f} (skor: {score})")

        primary_topic = sorted_topics[0][0]
        result.append(f"\n💡 *Birincil konu: **{primary_topic}***")

        return "\n".join(result)

    def extract_keywords(self, text: str, top_n: int = 20) -> list:
        """Anahtar kelime çıkarımı"""
        # Stop words (gereksiz kelimeler)
        stop_words = {
            "bir", "bu", "şu", "ve", "veya", "ile", "için", "gibi", "da", "de",
            "ki", "mi", "mu", "mı", "mü", "daha", "çok", "az", "var", "yok",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "olan", "olarak", "sonra", "için", "kadar", "göre", "karşı"
        }

        words = re.findall(r'\b[a-züçğıöşA-ZÜÇĞİÖŞ]{4,}\b', text.lower())
        filtered = [w for w in words if w not in stop_words]

        word_freq = Counter(filtered)
        return [word for word, _ in word_freq.most_common(top_n)]

    def find_similar_words(self, query: str, text: str) -> list:
        """Benzer kelime önerileri (basit fuzzy search)"""
        words = set(re.findall(r'\b[a-züçğıöşA-ZÜÇĞİÖŞ]{3,}\b', text.lower()))
        query = query.lower()

        similar = []
        for word in words:
            # Basit benzerlik: ortak harfler
            if len(set(query) & set(word)) >= min(len(query), len(word)) * 0.6:
                similar.append(word)

        return sorted(similar)[:10]

    def list_documents(self) -> str:
        """Yüklü dökümanları listeler"""
        if not self.pdf_library:
            return "📚 Henüz yüklü döküman yok."

        result = ["### 📚 Yüklü Dökümanlar\n"]
        for filename, doc in self.pdf_library.items():
            active = "✅" if filename == self.current_pdf else "  "
            result.append(
                f"{active} **{doc['metadata']['title']}**\n"
                f"   ↳ {doc['metadata']['pages']} sayfa, {doc['word_count']:,} kelime\n"
                f"   ↳ {doc['loaded_at']}\n"
            )

        return "\n".join(result) + "\n\n💡 *Döküman değiştir: `pdf değiştir dosya_adı.pdf`*"

    def switch_document(self, filename: str) -> str:
        """Aktif dökümanı değiştirir"""
        if filename not in self.pdf_library:
            available = ", ".join(self.pdf_library.keys())
            return f"⚠️ '{filename}' bulunamadı.\n\n**Mevcut:** {available}"

        self.current_pdf = filename
        doc = self.pdf_library[filename]
        return f"✅ Aktif döküman: **{doc['metadata']['title']}**"

    def show_help(self) -> str:
        """Yardım menüsü"""
        return (
            "### 📚 Metoolok PDF - Kullanım Kılavuzu\n\n"
            "**📥 Yükleme:**\n"
            "`pdf yükle dosya.pdf` - PDF yükle\n\n"
            "**📖 Okuma:**\n"
            "`pdf özet` - Akıllı özet çıkar\n"
            "`pdf içindekiler` - Başlıkları listele\n"
            "`pdf sayfa 5` - Belirli sayfayı oku\n\n"
            "**🔍 Arama:**\n"
            "`pdf search: konu` - Gelişmiş arama\n"
            "`pdf ara: kelime` - Bağlamıyla ara\n\n"
            "**📊 Analiz:**\n"
            "`pdf istatistik` - Detaylı istatistikler\n"
            "`pdf konu` - Otomatik konu tespiti\n\n"
            "**📚 Yönetim:**\n"
            "`pdf liste` - Yüklü dökümanlar\n"
            "`pdf değiştir dosya.pdf` - Döküman değiştir\n\n"
            "💡 *Tüm komutlar için 'pdf' ön eki kullan!*"
        )