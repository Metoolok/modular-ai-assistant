import math
from datetime import datetime, timedelta
from .base import BaseSkill

class FitnessSkill(BaseSkill):
    """
    Metoolok Gelişmiş Fitness ve Sağlık Modülü.
    Özellikler:
    - VKI / BMI ve Vücut Yağ Oranı Tahmini (cinsiyet ve yaş desteği)
    - Kişiselleştirilmiş Antrenman Programı
    - Günlük Kalori ve Makro Takibi
    - Tarih Bazlı Özetler ve AI Önerileri
    - İlerleme Grafiği ve Hedef Takibi
    """
    name = "fitness"
    keywords = [
        "fitness", "kalori", "diet", "spor", "workout",
        "antrenman", "vki", "bmi", "boy", "kilo", "protein", "makro",
        "yağ", "kas", "hedef", "progress", "ilerleme"
    ]
    description = "Vücut metriklerini takip eder, bilimsel spor danışmanlığı yapar ve AI önerileri sunar."

    async def execute(self, args: str) -> str:
        args_lower = args.lower()
        metrics = self.safe_read_dict("fitness_metrics") or {}

        # --- Profil Oluşturma (ilk kullanım) ---
        if "profil" in args_lower or "setup" in args_lower:
            return self.setup_profile_guide()

        # --- VKI / BMI ve Vücut Yağ Oranı ---
        if any(term in args_lower for term in ["vki", "bmi", "vücut kitle"]):
            return await self.calculate_bmi(args, metrics)

        # --- Antrenman Programı Önerisi ---
        if any(word in args_lower for word in ["program", "antrenman", "ne yapayım", "workout"]):
            return self.get_workout_plan(metrics)

        # --- Kalori Hesaplama ---
        if "kalori" in args_lower or "tdee" in args_lower:
            return self.calculate_calories(metrics)

        # --- Veri Ekleme (Makro, Su, Kilo vb.) ---
        if "add:" in args_lower or "ekle:" in args_lower:
            return self.add_metric(args, metrics)

        # --- İlerleme / Tarih Bazlı Görüntüleme ---
        if any(word in args_lower for word in ["ilerleme", "progress", "grafik"]):
            return self.show_progress(metrics)

        # --- Özet / Tüm Veriler ---
        if any(word in args_lower for word in ["show", "göster", "özet", "rapor"]):
            return self.show_metrics(metrics)

        # --- Hedef Belirleme ---
        if "hedef" in args_lower or "goal" in args_lower:
            return self.set_goal(args, metrics)

        # --- Varsayılan Yardım ---
        return self.show_help()

    # ------------------- Fonksiyonlar -------------------

    def setup_profile_guide(self) -> str:
        """İlk kullanım için profil oluşturma rehberi"""
        return (
            "### 👤 Profil Oluşturma Rehberi\n\n"
            "**Adım 1:** Temel bilgilerini gir:\n"
            "`fitness add:yaş 25`\n"
            "`fitness add:cinsiyet erkek` (veya kadın)\n"
            "`fitness add:aktivite orta` (düşük/orta/yüksek)\n\n"
            "**Adım 2:** VKI hesapla:\n"
            "`fitness vki boy:175 kilo:70`\n\n"
            "**Adım 3:** Hedef belirle:\n"
            "`fitness hedef:yağ yakımı` (veya kas kazanımı/kilo alma)\n\n"
            "💡 Sonra `fitness show` ile tüm bilgilerini görebilirsin!"
        )

    async def calculate_bmi(self, args: str, metrics: dict) -> str:
        """
        VKI/BMI hesaplar, vücut yağ oranını tahmin eder ve risk analizi sunar.
        Cinsiyet ve yaş bilgisini dikkate alır.
        """
        try:
            # Boy ve kilo çıkarma
            weight = None
            height_cm = None

            for part in args.split():
                if "kilo:" in part:
                    weight = float(part.split(":")[1])
                elif "boy:" in part:
                    height_cm = float(part.split(":")[1])

            if not weight or not height_cm:
                raise ValueError("Boy veya kilo eksik")

            height = height_cm / 100

            # BMI / VKI
            bmi = weight / (height ** 2)
            status = (
                "Zayıf" if bmi < 18.5 else
                "Normal" if bmi < 25 else
                "Fazla Kilolu" if bmi < 30 else
                "Obez"
            )

            # Vücut Yağ Oranı (geliştirilmiş tahmin - cinsiyet ve yaş bazlı)
            age = metrics.get("yaş", {}).get(max(metrics.get("yaş", {"2000-01-01": 30}).keys(), default="2000-01-01"), 30)
            if isinstance(age, str):
                age = int(''.join(filter(str.isdigit, age))) or 30

            gender = metrics.get("cinsiyet", {}).get(max(metrics.get("cinsiyet", {"2000-01-01": "erkek"}).keys(), default="2000-01-01"), "erkek")
            if isinstance(gender, str):
                gender = gender.lower()

            # Durnin-Womersley formülü yaklaşımı
            if "kadın" in str(gender):
                body_fat = round(1.20 * bmi + 0.23 * age - 5.4, 1)
            else:
                body_fat = round(1.20 * bmi + 0.23 * age - 16.2, 1)

            # Risk analizi
            risk_note = "Düşük Risk" if bmi < 25 else "Orta Risk" if bmi < 30 else "Yüksek Risk"

            # İdeal yağ oranı
            if "kadın" in str(gender):
                ideal_fat = "20-25% (fitness için 18-20%)"
            else:
                ideal_fat = "10-15% (fitness için 8-12%)"

            # Hafızaya kaydet
            today = datetime.now().strftime("%Y-%m-%d")
            if "kilo_history" not in metrics:
                metrics["kilo_history"] = {}
            metrics["kilo_history"][today] = weight

            metrics.update({
                "weight": weight,
                "height": height_cm,
                "last_bmi": round(bmi, 2),
                "body_fat": body_fat,
                "last_update": today
            })
            self.save_to_memory("fitness_metrics", metrics)

            return (
                f"### 📊 Vücut Analizi ({today})\n\n"
                f"**Temel Metrikler:**\n"
                f"- Boy: {height_cm} cm\n"
                f"- Kilo: {weight} kg\n"
                f"- VKI/BMI: **{bmi:.2f}**\n"
                f"- Durum: **{status}**\n\n"
                f"**Vücut Kompozisyonu:**\n"
                f"- Yağ Oranı Tahmini: **{body_fat}%**\n"
                f"- İdeal Yağ Oranı: {ideal_fat}\n"
                f"- Risk Seviyesi: **{risk_note}**\n\n"
                f"**İdeal Kilo Aralığı:**\n"
                f"- {round(18.5 * (height**2), 1)} kg - {round(24.9 * (height**2), 1)} kg\n\n"
                f"💡 *Sağlıklı bir kilo değişimi için haftada 0.5-1 kg hedefle!*\n"
                f"📈 İlerleme için: `fitness ilerleme`"
            )
        except Exception as e:
            return (
                "⚠️ **Hata:** Lütfen boy ve kilonu doğru formatta belirt.\n\n"
                "**Örnek:** `fitness vki boy:180 kilo:85`\n"
                "**Not:** Noktalı sayı kullanabilirsin (örn: boy:175.5)"
            )

    def calculate_calories(self, metrics: dict) -> str:
        """
        TDEE (Günlük kalori ihtiyacı) ve makro besin hesaplama
        """
        try:
            weight = metrics.get("weight", 0)
            height = metrics.get("height", 0)

            # Yaş ve cinsiyet bilgisi al
            age = 30  # varsayılan
            if "yaş" in metrics and isinstance(metrics["yaş"], dict):
                age_val = list(metrics["yaş"].values())[-1]
                age = int(''.join(filter(str.isdigit, str(age_val)))) or 30

            gender = "erkek"
            if "cinsiyet" in metrics and isinstance(metrics["cinsiyet"], dict):
                gender = list(metrics["cinsiyet"].values())[-1].lower()

            if not weight or not height:
                return "⚠️ Önce VKI hesapla: `fitness vki boy:175 kilo:70`"

            # Mifflin-St Jeor Formülü (BMR)
            if "kadın" in gender:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age + 5

            # Aktivite seviyesi
            activity = "orta"
            if "aktivite" in metrics and isinstance(metrics["aktivite"], dict):
                activity = list(metrics["aktivite"].values())[-1].lower()

            activity_multiplier = {
                "düşük": 1.2,
                "orta": 1.55,
                "yüksek": 1.9
            }.get(activity, 1.55)

            tdee = round(bmr * activity_multiplier)

            # Hedef bazlı kalori ayarı
            goal_calories = tdee
            goal_text = "Kilo Koruma"

            if "hedef" in metrics:
                goal = list(metrics["hedef"].values())[-1].lower() if isinstance(metrics["hedef"], dict) else str(metrics["hedef"]).lower()
                if "yağ" in goal or "zayıf" in goal or "yakım" in goal:
                    goal_calories = tdee - 500
                    goal_text = "Yağ Yakımı (-500 kal)"
                elif "kas" in goal or "bulk" in goal or "alma" in goal:
                    goal_calories = tdee + 300
                    goal_text = "Kas Kazanımı (+300 kal)"

            # Makro besin hesaplama
            protein = round(weight * 2.2)  # 2.2g/kg
            fat = round((goal_calories * 0.25) / 9)  # Kalorilerin %25'i yağdan
            carbs = round((goal_calories - (protein * 4) - (fat * 9)) / 4)

            return (
                f"### 🔥 Günlük Kalori ve Makro İhtiyacın\n\n"
                f"**Temel Metabolizma (BMR):** {round(bmr)} kal\n"
                f"**Günlük İhtiyaç (TDEE):** {tdee} kal\n"
                f"**Hedef ({goal_text}):** **{goal_calories} kal**\n\n"
                f"**Makro Besinler:**\n"
                f"- 🥩 Protein: **{protein}g** ({round(protein*4)} kal)\n"
                f"- 🥑 Yağ: **{fat}g** ({round(fat*9)} kal)\n"
                f"- 🍚 Karbonhidrat: **{carbs}g** ({round(carbs*4)} kal)\n\n"
                f"💡 *Günlük {weight * 0.035:.1f}L su içmeyi unutma!*\n"
                f"📊 Makro takibi: `fitness add:protein 150g`"
            )
        except Exception as e:
            return f"⚠️ Kalori hesaplamada hata: {str(e)}"

    def get_workout_plan(self, metrics: dict) -> str:
        """
        Kullanıcının hedeflerine göre detaylı antrenman önerir
        """
        # Hedef belirleme
        target = "dengeli"
        if "hedef" in metrics:
            goal = list(metrics["hedef"].values())[-1].lower() if isinstance(metrics["hedef"], dict) else str(metrics["hedef"]).lower()
            if "yağ" in goal or "zayıf" in goal:
                target = "yağ yakımı"
            elif "kas" in goal or "bulk" in goal:
                target = "kas kazanımı"

        body_fat = metrics.get("body_fat", 20)

        if target == "yağ yakımı":
            return (
                f"### 🔥 Antrenman Programı: Yağ Yakımı\n\n"
                f"**📅 Haftalık Plan:**\n\n"
                f"**Pazartesi - Push (İtiş):**\n"
                f"- Barbell Bench Press: 4x8-10\n"
                f"- Incline Dumbbell Press: 3x10-12\n"
                f"- Shoulder Press: 3x10\n"
                f"- Lateral Raises: 3x12-15\n"
                f"- Triceps Dips: 3x10-12\n"
                f"- Cable Triceps Extension: 3x12\n"
                f"🏃 Kardiyo: 25 dk HIIT (1 dk sprint, 2 dk yürüyüş)\n\n"
                f"**Çarşamba - Pull (Çekiş):**\n"
                f"- Deadlift: 4x6-8\n"
                f"- Pull-ups/Lat Pulldown: 4x8-10\n"
                f"- Barbell Row: 3x10\n"
                f"- Face Pulls: 3x15\n"
                f"- Dumbbell Curl: 3x10-12\n"
                f"- Hammer Curl: 3x12\n"
                f"🏃 Kardiyo: 20 dk LISS (hafif tempo koşu)\n\n"
                f"**Cuma - Legs (Bacak):**\n"
                f"- Barbell Squat: 4x8-10\n"
                f"- Romanian Deadlift: 3x10\n"
                f"- Leg Press: 3x12\n"
                f"- Walking Lunges: 3x10 (her bacak)\n"
                f"- Leg Curl: 3x12\n"
                f"- Calf Raises: 4x15\n"
                f"🏃 Kardiyo: 30 dk LISS\n\n"
                f"**Pazar - Full Body HIIT:**\n"
                f"- Circuit: Burpees, Mountain Climbers, Jump Squats\n"
                f"- 4 tur, her hareket 45 sn, 15 sn dinlenme\n\n"
                f"💪 *Her antrenman 60-75 dk sürmeli*\n"
                f"💡 *Haftada toplam 150+ dk kardiyo hedefle*"
            )

        elif target == "kas kazanımı":
            return (
                f"### 💪 Antrenman Programı: Kas Kazanımı (Hypertrophy)\n\n"
                f"**📅 Haftalık Plan (PPL - 6 Gün):**\n\n"
                f"**Gün 1 - Push:**\n"
                f"- Barbell Bench Press: 5x5 (ağır)\n"
                f"- Incline Barbell Press: 4x8\n"
                f"- Dumbbell Flyes: 3x12\n"
                f"- Military Press: 4x8\n"
                f"- Lateral Raises: 4x15\n"
                f"- Overhead Triceps Extension: 3x10\n"
                f"- Cable Pushdowns: 3x12\n\n"
                f"**Gün 2 - Pull:**\n"
                f"- Deadlift: 5x5 (ağır)\n"
                f"- Weighted Pull-ups: 4x6-8\n"
                f"- Barbell Row: 4x8\n"
                f"- T-Bar Row: 3x10\n"
                f"- Face Pulls: 3x15\n"
                f"- Barbell Curl: 3x10\n"
                f"- Preacher Curl: 3x12\n\n"
                f"**Gün 3 - Legs:**\n"
                f"- Back Squat: 5x5 (ağır)\n"
                f"- Front Squat: 3x8\n"
                f"- Leg Press: 4x12\n"
                f"- Romanian Deadlift: 4x10\n"
                f"- Leg Curl: 3x12\n"
                f"- Calf Raises: 5x15\n\n"
                f"**Gün 4-6:** Tekrar (farklı varyasyonlar)\n\n"
                f"🔥 *Minimal kardiyo: Haftada 2x15 dk LISS*\n"
                f"⚡ *Progressive overload: Her hafta ağırlık veya tekrar arttır*\n"
                f"😴 *8+ saat uyku ve yeterli protein şart!*"
            )

        else:
            return (
                f"### ⚖️ Antrenman Programı: Dengeli Fitness\n\n"
                f"**Pazartesi & Perşembe - Upper Body:**\n"
                f"- Push-ups / Bench Press: 3x10-12\n"
                f"- Pull-ups / Rows: 3x10\n"
                f"- Shoulder Press: 3x10\n"
                f"- Bicep & Tricep Supersets: 3x12\n\n"
                f"**Salı & Cuma - Lower Body:**\n"
                f"- Squats: 4x10\n"
                f"- Deadlifts: 3x8\n"
                f"- Lunges: 3x10 (her bacak)\n"
                f"- Calf Raises: 3x15\n\n"
                f"**Çarşamba & Cumartesi - Kardiyo + Core:**\n"
                f"- 30 dk orta tempolu koşu\n"
                f"- Plank: 3x60 sn\n"
                f"- Russian Twists: 3x20\n"
                f"- Leg Raises: 3x15\n\n"
                f"💡 *Hedef belirle: `fitness hedef:yağ yakımı` veya `fitness hedef:kas kazanımı`*"
            )

    def add_metric(self, args: str, metrics: dict) -> str:
        """
        Kullanıcının yeni verilerini ekler (protein, su, kilo vb.)
        """
        try:
            # add: veya ekle: ayırma
            separator = "add:" if "add:" in args else "ekle:"
            _, val_part = args.split(separator, 1)
            val_part = val_part.strip()

            # Metrik adı ve değer ayırma
            parts = val_part.split(maxsplit=1)
            if len(parts) < 2:
                # Eğer tek kelime ise (örn: "protein 150" yerine "protein150")
                metric_name = parts[0]
                value = "Evet"
            else:
                metric_name, value = parts

            # Tarih bazlı kayıt
            today = datetime.now().strftime("%Y-%m-%d")

            if metric_name not in metrics:
                metrics[metric_name] = {}

            # Özel durumlar için düzenlemeler
            if metric_name.lower() in ["kilo", "weight"]:
                # Kilo güncellemesi aynı zamanda kilo_history'e de eklenir
                if "kilo_history" not in metrics:
                    metrics["kilo_history"] = {}
                try:
                    weight_val = float(''.join(filter(lambda x: x.isdigit() or x == '.', value)))
                    metrics["kilo_history"][today] = weight_val
                    metrics["weight"] = weight_val
                except:
                    pass

            metrics[metric_name][today] = value
            self.save_to_memory("fitness_metrics", metrics)

            return f"✅ **{metric_name.capitalize()}** kaydedildi: **{value}** ({today})"

        except Exception as e:
            return (
                "⚠️ **Format Hatası!**\n\n"
                "**Doğru kullanım:**\n"
                "- `fitness add:protein 150g`\n"
                "- `fitness add:su 3litre`\n"
                "- `fitness add:kilo 75.5`\n"
                "- `fitness add:aktivite yüksek`"
            )

    def show_progress(self, metrics: dict) -> str:
        """
        Kilo ve vücut kompozisyonu ilerlemesini gösterir
        """
        if "kilo_history" not in metrics or not metrics["kilo_history"]:
            return "📊 Henüz kilo geçmişi yok. `fitness vki boy:X kilo:Y` ile başla!"

        kilo_data = metrics["kilo_history"]
        sorted_dates = sorted(kilo_data.keys())

        if len(sorted_dates) < 2:
            return f"📊 İlk ölçüm: {sorted_dates[0]} - {kilo_data[sorted_dates[0]]} kg\n\n💡 Düzenli ölçüm yap!"

        # İlk ve son ölçüm
        first_date = sorted_dates[0]
        last_date = sorted_dates[-1]
        first_weight = kilo_data[first_date]
        last_weight = kilo_data[last_date]

        change = last_weight - first_weight
        change_text = f"{'📉' if change < 0 else '📈'} {abs(change):.1f} kg"

        # Haftalık ortalama
        days_diff = (datetime.strptime(last_date, "%Y-%m-%d") -
                     datetime.strptime(first_date, "%Y-%m-%d")).days
        weekly_avg = (change / max(days_diff, 1)) * 7 if days_diff > 0 else 0

        # Son 7 günlük özet
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_entries = [f"- {date}: {weight} kg"
                          for date, weight in sorted(kilo_data.items())
                          if date >= week_ago]

        result = (
            f"### 📈 İlerleme Raporu\n\n"
            f"**Genel Özet:**\n"
            f"- Başlangıç ({first_date}): {first_weight} kg\n"
            f"- Güncel ({last_date}): {last_weight} kg\n"
            f"- Toplam Değişim: {change_text}\n"
            f"- Haftalık Ortalama: {abs(weekly_avg):.2f} kg/hafta\n\n"
        )

        if recent_entries:
            result += f"**Son 7 Gün:**\n" + "\n".join(recent_entries) + "\n\n"

        # Motivasyon mesajı
        if change < 0:
            result += "🎉 *Harika gidiyorsun! Yağ yakımında başarılı oluyorsun!*"
        elif change > 0:
            result += "💪 *Kas kazanımı sürecinde ilerliyorsun!*"
        else:
            result += "⚖️ *Kilonu dengede tutuyorsun.*"

        return result

    def show_metrics(self, metrics: dict) -> str:
        """
        Kayıtlı tüm verileri organize bir şekilde özetler
        """
        if not metrics:
            return (
                "📊 Henüz kayıtlı veri yok.\n\n"
                "**Başlamak için:**\n"
                "`fitness profil` - Profil oluştur\n"
                "`fitness vki boy:175 kilo:70` - VKI hesapla"
            )

        result = ["### 📋 Fitness Profilin\n"]

        # Temel bilgiler
        basics = []
        if "weight" in metrics:
            basics.append(f"- Kilo: **{metrics['weight']} kg**")
        if "height" in metrics:
            basics.append(f"- Boy: **{metrics['height']} cm**")
        if "last_bmi" in metrics:
            basics.append(f"- VKI: **{metrics['last_bmi']}**")
        if "body_fat" in metrics:
            basics.append(f"- Yağ Oranı: **{metrics['body_fat']}%**")

        if basics:
            result.append("**📊 Temel Metrikler:**")
            result.extend(basics)
            result.append("")

        # Profil bilgileri
        profile_keys = ["yaş", "cinsiyet", "aktivite", "hedef"]
        profile_data = []
        for key in profile_keys:
            if key in metrics:
                if isinstance(metrics[key], dict):
                    val = list(metrics[key].values())[-1]
                else:
                    val = metrics[key]
                profile_data.append(f"- {key.capitalize()}: **{val}**")

        if profile_data:
            result.append("**👤 Profil:**")
            result.extend(profile_data)
            result.append("")

        # Günlük kayıtlar (son 3 gün)
        daily_keys = [k for k in metrics.keys()
                      if k not in ["weight", "height", "last_bmi", "body_fat",
                                   "last_update", "kilo_history", "yaş", "cinsiyet",
                                   "aktivite", "hedef"]]

        if daily_keys:
            result.append("**📅 Son Kayıtlar:**")
            for key in daily_keys:
                if isinstance(metrics[key], dict):
                    recent = sorted(metrics[key].items())[-3:]  # Son 3 kayıt
                    for date, val in recent:
                        result.append(f"- {key.capitalize()} ({date}): {val}")
            result.append("")

        # Son güncelleme
        if "last_update" in metrics:
            result.append(f"*Son güncelleme: {metrics['last_update']}*")

        result.append("\n💡 **Komutlar:** `fitness kalori`, `fitness program`, `fitness ilerleme`")

        return "\n".join(result)

    def set_goal(self, args: str, metrics: dict) -> str:
        """Hedef belirleme"""
        try:
            goal = args.split("hedef:")[-1].strip() if "hedef:" in args else args.split("goal:")[-1].strip()

            today = datetime.now().strftime("%Y-%m-%d")
            if "hedef" not in metrics:
                metrics["hedef"] = {}

            metrics["hedef"][today] = goal
            self.save_to_memory("fitness_metrics", metrics)

            return (
                f"✅ **Hedef belirlendi:** {goal}\n\n"
                f"💡 Şimdi önerilen kalorini öğren: `fitness kalori`\n"
                f"🏋️ Antrenman programı için: `fitness program`"
            )
        except:
            return (
                "**Hedef Örnekleri:**\n"
                "- `fitness hedef:yağ yakımı`\n"
                "- `fitness hedef:kas kazanımı`\n"
                "- `fitness hedef:kilo alma`"
            )

    def show_help(self) -> str:
        """Yardım menüsü"""
        return (
            "### 💪 Metoolok Fitness - Kullanım Kılavuzu\n\n"
            "**🎯 Başlangıç:**\n"
            "`fitness profil` - İlk kurulum rehberi\n"
            "`fitness vki boy:175 kilo:70` - VKI/BMI hesapla\n"
            "`fitness hedef:yağ yakımı` - Hedef belirle\n\n"
            "**📊 Hesaplamalar:**\n"
            "`fitness kalori` - Günlük kalori ve makro hesapla\n"
            "`fitness program` - Antrenman programı öner\n\n"
            "**📝 Veri Girişi:**\n"
            "`fitness add:protein 150g` - Günlük protein kaydet\n"
            "`fitness add:su 3litre` - Su tüketimi kaydet\n"
            "`fitness add:kilo 72.5` - Kilo güncelle\n\n"
            "**📈 Raporlar:**\n"
            "`fitness show` - Tüm verileri göster\n"
            "`fitness ilerleme` - Kilo grafiği ve ilerleme\n\n"
            "💡 *Her komutta 'fitness' ön ekini kullan!*"
        )