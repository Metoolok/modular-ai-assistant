

🤖 Modular AI Personal Assistant: Metoolok Engine



<a name="english-description"></a>

🇬🇧 English Description
🚀 Overview
Metoolok is a high-performance personal assistant ecosystem designed with a Modular Skill Architecture. Unlike monolithic assistants, this project treats every functionality (PDF analysis, fitness, news, etc.) as an independent, pluggable module. Developed on Ubuntu Linux, it leverages asynchronous processing to ensure a smooth and responsive user experience.

🛠 Technical Architecture
Core Engine: An asynchronous Python-based core that manages skill registration and execution.

Modular Design: New "Skills" can be added by simply dropping a new script into the skills/ directory.

UI Layer: A modern, reactive Dark-UI built with Streamlit for cross-platform compatibility.

Containerization: Fully Dockerized for seamless deployment across different environments.

🧩 Core Modules (Skills)
📄 PDF Intelligence: Uses advanced parsing to extract text, provide automated summaries, and calculate word frequency statistics.

🏋️ Fitness Analytics: A comprehensive health tracker that calculates BMI and tracks progress based on user-defined hypertrophy or fat loss goals.

📰 Live Data Stream: Real-time integration with global APIs for the latest tech news and weather conditions.

📋 Async Task Manager: A robust Todo system that handles tasks without blocking the main UI thread.

📥 Installation & Usage[Ekran kaydı - 2026-01-29 22-42-24.webm](https://github.com/user-attachments/assets/f9197641-725c-4406-abef-0c927536c367)


[Ekran kaydı - 2026-01-29 22-40-22.webm](https://github.com/user-attachments/assets/533717a4-e056-4007-b661-7a359e857d75)


[Ekran kaydı - 2026-01-29 21-30-26.webm](https://github.com/user-attachments/assets/9ae4feec-8da5-42c9-a130-d7d8c3884acd)


[Ekran kaydı - 2026-01-29 21-29-11.webm](https://github.com/user-attachments/assets/df5dd0d1-8dfe-4597-9a32-ac50db5793ee)



[Ekran kaydı - 2026-01-29 21-28-30.webm](https://github.com/user-attachments/assets/e03e3346-06b8-4bee-9b14-9dbc827ed842)




Bash
# Clone the repository
git clone https://github.com/Metoolok/modular-ai-assistant.git

# Method 1: Docker (Recommended)
docker build -t modular-ai-assistant .
docker run -p 8501:8501 modular-ai-assistant

# Method 2: Manual Setup
pip install -r requirements.txt
streamlit run app.py



🇹🇷 Türkçe Açıklama
🚀 Genel Bakış
Metoolok, Modüler Yetenek Mimarisi (Modular Skill Architecture) ile tasarlanmış yüksek performanslı bir kişisel asistan ekosistemidir. Monolitik asistanların aksine, bu proje her bir fonksiyonu (PDF analizi, fitness, haberler vb.) bağımsız ve tak-çıkar yapılabilir bir modül olarak ele alır. Ubuntu Linux üzerinde geliştirilen sistem, akıcı bir kullanıcı deneyimi için asenkron işlem yapısını kullanır.

🛠 Teknik Mimari
Çekirdek Motor: Yeteneklerin sisteme kaydedilmesini ve yürütülmesini yöneten, Python tabanlı asenkron bir çekirdek.

Modüler Tasarım: skills/ dizinine yeni bir script eklenerek sisteme kolayca yeni yetenekler dahil edilebilir.

Arayüz Katmanı: Platform bağımsız çalışma için Streamlit ile geliştirilmiş modern ve reaktif "Dark-UI".

Konteynerleştirme: Farklı ortamlarda sorunsuz dağıtım (deployment) için tam Docker desteği.

🧩 Temel Modüller (Yetenekler)
📄 PDF Zekası: Metin çıkarma, otomatik özetleme ve kelime frekansı istatistikleri için gelişmiş ayrıştırma yöntemleri kullanır.

🏋️ Fitness Analitiği: VKI hesaplayan ve kullanıcı tarafından belirlenen kas kazanımı/yağ yakımı hedeflerini takip eden kapsamlı bir sağlık takipçisi.

📰 Canlı Veri Akışı: En güncel teknoloji haberleri ve hava durumu koşulları için küresel API'lerle gerçek zamanlı entegrasyon.

📋 Asenkron Görev Yöneticisi: Ana arayüzü dondurmadan görevleri yöneten güçlü bir Todo sistemi.

📥 Kurulum ve Kullanım
Bash
# Projeyi klonlayın
git clone https://github.com/Metoolok/modular-ai-assistant.git

# Yöntem 1: Docker (Önerilen)
docker build -t modular-ai-assistant .
docker run -p 8501:8501 modular-ai-assistant

# Yöntem 2: Manuel Kurulum
pip install -r requirements.txt
streamlit run app.py
👨‍💻 Developer / Geliştirici


Metin Mert Turan - Artificial Intelligence Engineering Student
