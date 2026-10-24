"""Regional Indian cohorts for the synthetic generator: the six ICMR-INDIAB regions, each with its own plates,
body size, glycaemic mix and activity. Sources and every assumption are listed in research/DATASETS.md section 4.

Foods: per serving unit, available carbohydrate, protein, fat, fibre, free sugars (g) and the GI of the
carbohydrate that is not free sugar (free sugars get sucrose's 65).
- INDB codes: Indian Nutrient Databank, Vijayakumar et al., Curr Dev Nutr 2024 (github.com/lindsayjaacks/
  Indian-Nutrient-Databank-INDB-, commit fbdb62b). INDB carbohydrate is available carbohydrate, as in IFCT 2017,
  so total carbohydrate = carb + fibre. For deep-fried recipes INDB counts all frying oil as eaten (60-80 g fat
  per samosa or vada); for those three, fat is set so it supplies half the energy (our assumption).
- Upper-case keys: Shobana et al., Indian J Med Res 2022 (cooked composition and measured GI), USDA (banana).
- GI: measured value for that dish where one exists (Shobana 2022; NIN 2022 South Indian breakfasts; PSG idli),
  otherwise the class value of its main carbohydrate from Atkinson et al., Diabetes Care 2008, Table 1.
Regions: ICMR-INDIAB-21 (Anjana et al., Nat Med 2025), Table 2 and Extended Data Tables 1-2; state weights are
Census 2011 populations (millions)."""

FOODS = {
    # INDB: wheat breads (wheat roti 62, A08; NIN chapati 62.4, parota 62.5; methi paratha 60.2, Shobana)
    "ASC096": ("chapati", 12.8, 2.1, 1.3, 2.3, 0.4, 62),
    "ASC097": ("plain paratha", 17.1, 2.8, 9.4, 3.0, 0.5, 62),
    "ASC098": ("aloo paratha", 22.3, 3.5, 9.5, 3.9, 1.1, 62),
    "BFP110": ("methi paratha", 20.2, 3.9, 4.0, 4.6, 2.2, 60),
    "OSR104": ("methi thepla", 15.1, 3.3, 5.8, 2.8, 1.1, 60),
    "OSR102": ("khakhra", 20.9, 3.6, 4.0, 4.1, 0.7, 62),
    "ASC150": ("makki ki roti", 20.6, 3.0, 14.3, 4.4, 0.6, 75),  # maize roti 74.8, Shobana
    # INDB: rice (white rice 73, A08; lemon rice 79.3, veg biryani 74.5, NIN; khichdi = 2:1 rice and lentils)
    "ASC113": ("boiled rice", 77.2, 7.8, 0.6, 3.7, 0.7, 73),
    "BFP144": ("khichdi", 57.6, 9.9, 5.8, 4.9, 0.7, 59),
    "ASC126": ("curd rice", 71.2, 12.4, 9.3, 4.6, 0.0, 73),
    "ASC124": ("lemon rice", 69.0, 13.6, 25.1, 8.1, 2.5, 79),
    "ASC127": ("tamarind rice", 83.2, 9.5, 10.9, 6.5, 14.9, 73),
    "BFP132": ("vangi bhat", 92.4, 15.4, 10.7, 12.9, 12.7, 73),
    "ASC123": ("vegetable biryani", 56.0, 9.5, 28.7, 10.0, 6.5, 75),
    "ASC122": ("mutton biryani", 46.7, 15.3, 16.1, 5.0, 5.0, 75),
    "OSR105": ("rice puttu", 49.7, 5.3, 13.1, 3.2, 1.4, 73),
    # INDB: fermented rice and pulse batters (rice idli 78, PSG 2022; plain dosa 79.4, pesarattu 60.7, NIN)
    "ASC144": ("idli", 7.1, 1.2, 0.1, 0.6, 0.1, 78),
    "BFP148": ("plain dosa", 23.1, 3.7, 3.0, 1.9, 0.3, 79),
    "ASC146": ("masala dosa", 41.0, 6.9, 16.4, 5.3, 2.8, 79),
    "BFP152": ("uttapam", 24.7, 4.2, 6.1, 3.0, 1.0, 79),
    "OSR103": ("pesarattu", 8.5, 3.3, 3.1, 1.6, 0.8, 61),
    "BFP046": ("moong dal cheela", 44.2, 15.9, 11.6, 9.7, 2.5, 61),
    # INDB: breakfast cereals (upma 71, Henry et al.; flattened rice: no Indian value found, 70 assumed;
    # puffed rice 80 assumed, between boiled rice 73 and rice crackers 87, A08; broken wheat 51.7, Shobana)
    "BFP039": ("rava upma", 17.3, 3.5, 8.0, 3.4, 1.4, 71),
    "BFP045": ("vegetable poha", 21.1, 4.8, 7.9, 3.7, 1.4, 70),
    "ASC052": ("chiwda with milk", 43.3, 10.1, 11.1, 1.0, 20.2, 70),
    "ASC054": ("puffed rice with milk", 43.6, 10.1, 11.2, 0.8, 20.3, 80),
    "ASC047": ("meetha daliya", 35.8, 10.6, 16.4, 2.5, 20.6, 52),
    # INDB: pulses (lentils 32, chickpeas 28, kidney beans 24, A08; dhokla 35 and dal dhokli 47 assumed)
    "ASC155": ("mixed dal", 17.3, 7.5, 9.2, 4.8, 1.0, 32),
    "OSR139": ("dal makhani", 28.1, 11.7, 10.8, 8.0, 2.8, 28),
    "OSR155": ("maa chaane ki dal", 35.0, 16.1, 7.7, 10.9, 0.9, 30),
    "BFP170": ("khatti dal", 21.9, 8.0, 0.5, 4.4, 4.5, 32),
    "BFP172": ("arhar dal with spinach", 19.2, 8.3, 11.1, 5.2, 0.9, 32),
    "ASC167": ("sambar", 27.2, 8.6, 11.3, 9.1, 8.5, 32),
    "BFP176": ("rasam", 13.1, 4.4, 3.4, 6.2, 3.2, 50),
    "ASC165": ("rajma", 19.6, 7.1, 6.9, 7.0, 3.0, 24),
    "OSR142": ("chana dal", 29.2, 12.1, 13.5, 10.9, 2.9, 28),
    "OSR143": ("horsegram dal", 29.6, 10.5, 4.1, 5.5, 2.6, 32),
    "OSR144": ("panchmel dal", 32.2, 13.9, 16.1, 9.6, 2.2, 32),
    "OSR141": ("dalma", 39.7, 12.9, 12.1, 5.7, 8.2, 32),
    "OSR145": ("dal dhokli", 28.8, 10.0, 8.3, 6.3, 3.8, 47),
    "BFP439": ("khaman dhokla", 6.4, 2.3, 3.3, 1.8, 1.6, 35),
    # INDB: vegetables (boiled potato 78, A08; other vegetables 50 assumed)
    "ASC171": ("aloo gobhi", 10.5, 3.3, 14.3, 5.3, 0.8, 78),
    "BFP239": ("aloo sabzi", 21.0, 3.1, 9.0, 4.9, 3.2, 78),
    "ASC178": ("dry potato (chokha)", 15.2, 1.7, 4.4, 2.0, 0.3, 78),
    "ASC190": ("aloo matar", 27.0, 9.7, 14.2, 10.0, 5.2, 78),
    "BFP257": ("palak aloo", 19.8, 5.5, 9.4, 6.8, 3.1, 78),
    "BFP269": ("bhindi sabzi", 7.5, 3.0, 15.4, 5.9, 2.4, 50),
    "ASC215": ("palak paneer", 13.1, 11.9, 14.1, 5.6, 0.0, 50),
    "ASC191": ("matar paneer", 25.8, 18.3, 21.5, 9.2, 0.0, 50),
    "ASC219": ("avial", 28.4, 8.2, 29.9, 18.2, 0.0, 50),
    # INDB: fish, meat, egg (gravy carbohydrate: 50 assumed)
    "ASC240": ("chicken curry", 8.4, 29.2, 18.8, 3.5, 4.4, 50),
    "ASC246": ("fish curry", 9.6, 22.3, 17.0, 4.8, 5.1, 50),
    "BFP223": ("Bengali fish curry", 13.7, 22.5, 21.8, 6.0, 7.4, 50),
    "BFP229": ("fish in coconut milk", 8.9, 28.2, 14.4, 4.9, 5.0, 50),
    "BFP240": ("egg curry", 6.1, 8.2, 13.4, 3.2, 2.9, 50),
    "ASC056": ("boiled egg", 0.2, 6.7, 4.6, 0.2, 0.0, 50),
    "ASC232": ("meat stew (mutton yakhni)", 2.0, 19.2, 17.9, 1.6, 0.3, 50),
    # INDB: dairy, drinks, sweets (milk 39, sucrose 65, white bread 75, A08). Milk sugars set to 0 free sugar.
    "ASC273": ("curd raita", 9.7, 6.2, 3.2, 1.3, 0.0, 39),
    "ASC022": ("salted lassi / chaas", 7.9, 5.7, 3.0, 0.1, 0.0, 39),
    "ASC021": ("sweet lassi", 28.8, 5.7, 3.0, 0.0, 21.0, 39),
    "ASC001": ("chai", 5.4, 0.8, 1.1, 0.0, 5.4, 65),
    "ASC002": ("milky coffee", 16.4, 2.9, 3.4, 0.0, 16.3, 65),
    "ASC441": ("sweet biscuit", 7.2, 0.8, 2.5, 0.2, 3.1, 75),
    "ASC282": ("rice kheer", 40.3, 9.2, 11.9, 0.7, 32.2, 73),
    "OSR011": ("chak-hao (black rice) kheer", 47.6, 9.1, 10.2, 1.6, 26.1, 73),
    "ASC293": ("suji halwa", 39.4, 3.5, 21.4, 3.0, 22.3, 71),
    "ASC467": ("puran poli", 33.4, 5.1, 4.2, 4.4, 13.2, 45),
    "OSR112": ("pav bhaji", 69.7, 15.5, 25.1, 11.5, 12.0, 70),
    # INDB, deep fried: fat reset to half the energy (see docstring). GI: french fries 63 (A08); vada sambar 36.9 (NIN)
    "ASC361": ("samosa", 13.0, 2.4, 6.8, 1.7, 0.4, 63),
    "BFP436": ("medu vada", 7.7, 3.5, 5.0, 1.8, 0.1, 37),
    "BFP118": ("matar kachori", 14.3, 3.5, 7.9, 2.2, 0.5, 63),
    # Shobana et al. 2022, Table I (per 100 g cooked) x unit weight; GI from its Table III
    "RAGI_MUDDE": ("ragi mudde (187 g ball)", 50.0, 7.3, 0.9, 10.2, 0.0, 98),
    "JOWAR_BHAKRI": ("jowar bhakri (50 g)", 24.7, 2.1, 0.5, 3.5, 0.0, 84),
    "BAJRA_ROTLA": ("bajra rotla (50 g)", 23.9, 3.3, 1.1, 3.5, 0.0, 70),
    "ADAI": ("adai (80 g)", 26.1, 6.0, 1.9, 5.2, 0.0, 66),
    "SUNDAL": ("chickpea sundal (100 g)", 22.3, 8.7, 2.7, 6.5, 0.0, 24),
    # USDA FoodData Central 09040, banana raw, 118 g; A08 banana 51
    "BANANA": ("banana", 23.9, 1.3, 0.4, 3.1, 0.0, 51),
    "SUGAR": ("table sugar (1 tsp, 5 g)", 5.0, 0.0, 0.0, 0.0, 5.0, 65),
    "GHEE": ("ghee (1 tsp, 5 g)", 0.0, 0.0, 5.0, 0.0, 0.0, 50),
}
ANIMAL = {"ASC240", "ASC246", "BFP223", "BFP229", "BFP240", "ASC056", "ASC232", "ASC122"}  # plates with these are non-vegetarian

# (meal, plate name, [(food, units)], weight within its meal slot, states it is confined to or None)
PLATES = {
    "north": [
        ("breakfast", "aloo paratha, curd, chai", [("ASC098", 2), ("ASC273", 1), ("ASC001", 1), ("SUGAR", 1)], 2, None),
        ("breakfast", "methi paratha, chai", [("BFP110", 2), ("ASC001", 1), ("SUGAR", 1)], 2, None),
        ("breakfast", "moong dal cheela, chai", [("BFP046", 1), ("ASC001", 1), ("SUGAR", 1)], 1, None),
        ("breakfast", "roti, aloo sabzi, chai", [("ASC096", 3), ("BFP239", 0.5), ("ASC001", 1), ("SUGAR", 1)], 2, None),
        ("breakfast", "meetha daliya, chai", [("ASC047", 1), ("ASC001", 1)], 1, None),
        ("lunch", "roti, dal, aloo gobhi, raita", [("ASC096", 4), ("ASC155", 1), ("ASC171", 0.5), ("ASC273", 1)], 3, None),
        ("lunch", "rajma chawal, raita", [("ASC165", 1.5), ("ASC113", 1), ("ASC273", 1)], 3, None),
        ("lunch", "roti, maa chaane ki dal, bhindi", [("ASC096", 3), ("OSR155", 1), ("BFP269", 0.5)], 2, ("Punjab", "Haryana", "Chandigarh", "Himachal Pradesh")),
        ("lunch", "bajra roti, panchmel dal", [("BAJRA_ROTLA", 2), ("OSR144", 1)], 2, ("Rajasthan",)),
        ("lunch", "chana dal, rice, roti", [("OSR142", 1), ("ASC113", 0.5), ("ASC096", 2)], 1, None),
        ("dinner", "roti, dal makhani, palak paneer", [("ASC096", 4), ("OSR139", 1), ("ASC215", 0.5)], 3, None),
        ("dinner", "roti, matar paneer, lassi", [("ASC096", 4), ("ASC191", 0.5), ("ASC022", 1)], 2, None),
        ("dinner", "roti, dal, rice", [("ASC096", 3), ("ASC155", 1), ("ASC113", 0.5)], 2, None),
        ("dinner", "makki roti, palak (saag)", [("ASC150", 2), ("ASC215", 1)], 2, ("Punjab", "Haryana", "Himachal Pradesh")),
        ("dinner", "roti, chicken curry", [("ASC096", 3), ("ASC240", 0.75)], 0.6, None),
        ("snack", "chai, biscuits", [("ASC001", 1), ("ASC441", 2), ("SUGAR", 1)], 3, None),
        ("snack", "chai, samosa", [("ASC001", 1), ("ASC361", 1), ("SUGAR", 1)], 1, None),
        ("snack", "sweet lassi", [("ASC021", 1)], 1, None),
        ("snack", "rice kheer", [("ASC282", 1)], 1, None),
    ],
    "south": [
        ("breakfast", "idli, sambar, coffee", [("ASC144", 4), ("ASC167", 0.75), ("ASC002", 1)], 3, None),
        ("breakfast", "dosa, sambar, coffee", [("BFP148", 2), ("ASC167", 0.75), ("ASC002", 1)], 3, None),
        ("breakfast", "masala dosa", [("ASC146", 1)], 1, None),
        ("breakfast", "rava upma", [("BFP039", 2)], 3, None),
        ("breakfast", "pongal (khichdi, ghee), sambar", [("BFP144", 1), ("GHEE", 1), ("ASC167", 0.5)], 1, ("Tamil Nadu", "Puducherry")),
        ("breakfast", "puttu, kadala (chana)", [("OSR105", 1), ("OSR142", 0.5)], 2, ("Kerala",)),
        ("breakfast", "pesarattu, upma", [("OSR103", 3), ("BFP039", 1)], 2, ("Andhra Pradesh",)),
        ("breakfast", "adai, coffee", [("ADAI", 2), ("ASC002", 1)], 1, ("Tamil Nadu",)),
        ("lunch", "rice, sambar, rasam, poriyal, curd", [("ASC113", 1), ("ASC167", 0.75), ("BFP176", 0.5), ("BFP269", 0.5), ("ASC273", 0.5)], 4, None),
        ("lunch", "curd rice", [("ASC126", 1)], 1, None),
        ("lunch", "lemon rice, curd", [("ASC124", 0.75), ("ASC273", 0.5)], 0.5, None),
        ("lunch", "ragi mudde, horsegram saaru", [("RAGI_MUDDE", 1), ("OSR143", 1)], 4, ("Karnataka",)),
        ("lunch", "vangi bhat, curd", [("BFP132", 0.75), ("ASC273", 0.5)], 1, ("Karnataka",)),
        ("lunch", "rice, fish curry, avial", [("ASC113", 1), ("BFP229", 0.75), ("ASC219", 0.5)], 4, ("Kerala",)),
        ("lunch", "rice, khatti dal, egg curry", [("ASC113", 1), ("BFP170", 1), ("BFP240", 0.5)], 3, ("Andhra Pradesh",)),
        ("lunch", "rice, fish curry", [("ASC113", 1), ("ASC246", 0.75)], 0.6, None),
        ("dinner", "chapati, aloo matar kurma", [("ASC096", 4), ("ASC190", 0.75)], 4, None),
        ("dinner", "rice, rasam, curd", [("ASC113", 0.75), ("BFP176", 1), ("ASC273", 1)], 2, None),
        ("dinner", "uttapam, sambar", [("BFP152", 2), ("ASC167", 0.5)], 1, None),
        ("dinner", "idli, sambar", [("ASC144", 4), ("ASC167", 0.75)], 2, None),
        ("dinner", "chicken biryani-style (mutton biryani), raita", [("ASC122", 1), ("ASC273", 0.5)], 0.4, None),
        ("snack", "coffee, biscuits", [("ASC002", 1), ("ASC441", 2)], 1.5, None),
        ("snack", "medu vada", [("BFP436", 2)], 0.5, None),
        ("snack", "chickpea sundal", [("SUNDAL", 1)], 1, None),
        ("snack", "banana", [("BANANA", 1)], 1, None),
    ],
    "east": [
        ("breakfast", "chiwda with milk (chura)", [("ASC052", 1)], 2, ("Bihar", "Jharkhand")),
        ("breakfast", "puffed rice with milk (muri)", [("ASC054", 0.75)], 2, ("West Bengal", "Odisha")),
        ("breakfast", "luchi-style paratha, aloo", [("ASC097", 3), ("BFP239", 0.5), ("ASC001", 1), ("SUGAR", 1)], 2, ("West Bengal",)),
        ("breakfast", "roti, aloo sabzi, chai", [("ASC096", 3), ("BFP239", 1), ("ASC001", 1), ("SUGAR", 1)], 2, None),
        ("breakfast", "upma, chai", [("BFP039", 2), ("ASC001", 1), ("SUGAR", 1)], 1, ("Odisha",)),
        ("lunch", "rice, dal, Bengali fish curry", [("ASC113", 1.25), ("ASC155", 0.75), ("BFP223", 0.5)], 2, ("West Bengal",)),
        ("lunch", "rice, dal, posto-style aloo", [("ASC113", 1.25), ("ASC155", 0.75), ("BFP239", 0.5)], 2, ("West Bengal",)),
        ("lunch", "rice, dalma", [("ASC113", 1.25), ("OSR141", 1)], 3, ("Odisha",)),
        ("lunch", "pakhala (water rice), fish curry", [("ASC113", 1.25), ("ASC246", 0.4)], 1, ("Odisha",)),
        ("lunch", "dal, bhaat, chokha", [("ASC113", 1), ("ASC155", 1), ("ASC178", 0.5)], 3, ("Bihar", "Jharkhand")),
        ("lunch", "rice, dal, aloo sabzi", [("ASC113", 1.25), ("ASC155", 0.75), ("BFP239", 0.5)], 2, None),
        ("dinner", "rice, dal, sabzi", [("ASC113", 1), ("ASC155", 0.5), ("BFP257", 0.75)], 3, None),
        ("dinner", "roti, aloo gobhi", [("ASC096", 4), ("ASC171", 1)], 4, ("Bihar", "Jharkhand")),
        ("dinner", "roti, dal, sabzi", [("ASC096", 4), ("ASC155", 0.75), ("BFP257", 0.5)], 1, ("West Bengal", "Odisha")),
        ("dinner", "rice, egg curry", [("ASC113", 1), ("BFP240", 0.75)], 0.6, None),
        ("dinner", "rice, fish curry", [("ASC113", 1), ("ASC246", 0.5)], 0.6, ("West Bengal", "Odisha")),
        ("snack", "chai, biscuits", [("ASC001", 1), ("ASC441", 2)], 3, None),
        ("snack", "payesh (rice kheer)", [("ASC282", 1)], 1, None),
        ("snack", "chai, samosa (singara)", [("ASC001", 1), ("ASC361", 1), ("SUGAR", 1)], 1, None),
        ("snack", "banana", [("BANANA", 1)], 1, None),
    ],
    "west": [
        ("breakfast", "kanda poha, chai", [("BFP045", 2), ("ASC001", 1), ("SUGAR", 1)], 3, ("Maharashtra", "Goa")),
        ("breakfast", "methi thepla, chai", [("OSR104", 2), ("ASC001", 1), ("SUGAR", 1)], 3, ("Gujarat",)),
        ("breakfast", "khaman dhokla, chai", [("BFP439", 4), ("ASC001", 1), ("SUGAR", 1)], 2, ("Gujarat",)),
        ("breakfast", "khakhra, chai", [("OSR102", 2), ("ASC001", 1), ("SUGAR", 1)], 1, ("Gujarat",)),
        ("breakfast", "upma, chai", [("BFP039", 2), ("ASC001", 1), ("SUGAR", 1)], 1, None),
        ("lunch", "rotli, dal, bhat, shaak", [("ASC096", 2), ("ASC155", 0.75), ("ASC113", 0.75), ("BFP239", 0.5), ("SUGAR", 1)], 4, ("Gujarat",)),
        ("lunch", "bajra rotla, shaak, chaas", [("BAJRA_ROTLA", 2), ("BFP239", 1), ("ASC022", 1)], 2, ("Gujarat",)),
        ("lunch", "jowar bhakri, pithla, rice", [("JOWAR_BHAKRI", 2), ("OSR142", 0.5), ("ASC113", 0.5)], 3, ("Maharashtra",)),
        ("lunch", "chapati, dal, rice, sabzi", [("ASC096", 2), ("ASC155", 0.75), ("ASC113", 0.75), ("BFP269", 0.5)], 3, ("Maharashtra",)),
        ("lunch", "rice, fish or chicken curry", [("ASC113", 1), ("ASC246", 0.6)], 1, ("Maharashtra",)),
        ("lunch", "Goan fish curry rice", [("ASC113", 1), ("ASC246", 0.75)], 4, ("Goa",)),
        ("dinner", "khichdi, chaas", [("BFP144", 1.25), ("ASC022", 1)], 3, ("Gujarat",)),
        ("dinner", "dal dhokli", [("OSR145", 1.5)], 1, ("Gujarat",)),
        ("dinner", "chapati, palak aloo, dal", [("ASC096", 2), ("BFP257", 1), ("ASC155", 0.5)], 2, None),
        ("dinner", "pav bhaji", [("OSR112", 1)], 1, ("Maharashtra",)),
        ("dinner", "rice, chicken curry", [("ASC113", 1), ("ASC240", 0.6)], 1, ("Maharashtra", "Goa")),
        ("dinner", "varan bhaat (dal, rice)", [("ASC113", 1), ("ASC155", 1)], 2, ("Maharashtra",)),
        ("snack", "chai, biscuits", [("ASC001", 1), ("ASC441", 2), ("SUGAR", 1)], 3, None),
        ("snack", "khaman dhokla", [("BFP439", 3)], 1, ("Gujarat",)),
        ("snack", "puran poli", [("ASC467", 1)], 1, ("Maharashtra",)),
        ("snack", "chai, samosa", [("ASC001", 1), ("ASC361", 1), ("SUGAR", 1)], 1, None),
    ],
    "central": [
        ("breakfast", "poha, chai", [("BFP045", 2), ("ASC001", 1), ("SUGAR", 1)], 3, ("Madhya Pradesh", "Chhattisgarh")),
        ("breakfast", "aloo paratha, chai", [("ASC098", 2), ("ASC001", 1), ("SUGAR", 1)], 1, None),
        ("breakfast", "roti, aloo sabzi, chai", [("ASC096", 3), ("BFP239", 0.5), ("ASC001", 1), ("SUGAR", 1)], 3, None),
        ("breakfast", "puri-style paratha, aloo sabzi", [("ASC097", 3), ("BFP239", 1), ("ASC001", 1)], 1, ("Uttar Pradesh",)),
        ("breakfast", "moong dal cheela (chila), chai", [("BFP046", 1), ("ASC001", 1), ("SUGAR", 1)], 1, ("Chhattisgarh",)),
        ("breakfast", "meetha daliya", [("ASC047", 1)], 1, None),
        ("lunch", "dal, chawal, roti, sabzi", [("ASC096", 3), ("ASC113", 0.75), ("ASC155", 0.75), ("ASC171", 0.5)], 4, None),
        ("lunch", "rice, dal, bhaji", [("ASC113", 1.25), ("ASC155", 0.75), ("BFP257", 0.5)], 4, ("Chhattisgarh",)),
        ("lunch", "dal bafla-style (paratha, panchmel dal)", [("ASC097", 3), ("OSR144", 1)], 1, ("Madhya Pradesh",)),
        ("lunch", "rajma chawal", [("ASC165", 1.5), ("ASC113", 0.75)], 1, ("Uttar Pradesh", "Uttarakhand")),
        ("dinner", "roti, aloo matar", [("ASC096", 5), ("ASC190", 0.5)], 3, None),
        ("dinner", "khichdi, curd", [("BFP144", 1.25), ("ASC273", 0.5)], 2, None),
        ("dinner", "roti, dal, sabzi", [("ASC096", 4), ("ASC155", 1), ("BFP257", 0.5)], 3, None),
        ("dinner", "roti, chicken curry", [("ASC096", 3), ("ASC240", 0.6)], 0.4, None),
        ("snack", "chai, biscuits", [("ASC001", 1), ("ASC441", 2), ("SUGAR", 1)], 4, None),
        ("snack", "chai, samosa", [("ASC001", 1), ("ASC361", 1), ("SUGAR", 1)], 1, None),
        ("snack", "chai, matar kachori", [("ASC001", 1), ("BFP118", 1), ("SUGAR", 1)], 0.5, None),
        ("snack", "suji halwa", [("ASC293", 0.75)], 1, None),
    ],
    "northeast": [
        ("breakfast", "rice, boiled egg, tea", [("ASC113", 0.6), ("ASC056", 1), ("ASC001", 1)], 3, None),
        ("breakfast", "pitha-style rice cake (puttu), tea", [("OSR105", 0.75), ("ASC001", 1)], 2, ("Assam", "Tripura")),
        ("breakfast", "rice, dal", [("ASC113", 0.75), ("ASC155", 0.75)], 2, None),
        ("breakfast", "roti, sabzi, tea", [("ASC096", 3), ("BFP257", 0.5), ("ASC001", 1)], 1, None),
        ("lunch", "rice, dal, fish curry (tenga)", [("ASC113", 1.25), ("ASC155", 0.5), ("ASC246", 0.4)], 3, None),
        ("lunch", "rice, pork-style meat stew", [("ASC113", 1), ("ASC232", 0.75)], 2, ("Nagaland", "Mizoram", "Meghalaya", "Arunachal Pradesh")),
        ("lunch", "rice, chicken curry", [("ASC113", 1.25), ("ASC240", 0.4)], 1, None),
        ("lunch", "rice, dal, sabzi", [("ASC113", 1), ("ASC155", 0.75), ("BFP257", 0.5)], 2, None),
        ("dinner", "rice, fish curry", [("ASC113", 1.25), ("ASC246", 0.4)], 2, None),
        ("dinner", "rice, egg curry, dal", [("ASC113", 1), ("BFP240", 0.5), ("ASC155", 0.5)], 1, None),
        ("dinner", "rice, meat stew", [("ASC113", 1.25), ("ASC232", 0.5)], 1, None),
        ("dinner", "roti, sabzi", [("ASC096", 3), ("BFP257", 1)], 1.5, None),
        ("dinner", "rice, dal, sabzi", [("ASC113", 1), ("ASC155", 0.75), ("BFP269", 0.5)], 2, None),
        ("snack", "tea, biscuits", [("ASC001", 1), ("ASC441", 1)], 2, None),
        ("snack", "chak-hao kheer", [("OSR011", 0.75)], 1, ("Manipur",)),
        ("snack", "banana", [("BANANA", 1)], 2, None),
        ("snack", "tea", [("ASC001", 1)], 1, None),
    ],
}
# ICMR-INDIAB-21 Table 2: median (IQR) age and BMI; % male; newly diagnosed prediabetes / T2D (rest normoglycaemic,
# known diabetes excluded); % physically inactive; family history of T2D; tobacco; alcohol; hypertension;
# median TG, HDL, LDL (mg/dL). Extended Data Table 2: medians of %E. States: Census 2011 population, millions.
# sev: severity scale from calibrate() (18 Oct 2026), so each region's prevalence arises before the quota trims it.
REGIONS = {
    "north": dict(sev=0.889, states={"Punjab": 27.7, "Haryana": 25.4, "Delhi": 16.8, "Himachal Pradesh": 6.9, "Rajasthan": 68.5, "Chandigarh": 1.1},
                  age=(40, 31, 50), bmi=(23, 20, 26), male=0.49, prediabetes=0.43, t2d=0.11, inactive=0.67, family=0.10,
                  tobacco=0.13, alcohol=0.09, hypertension=0.28, tg=114, hdl=41, ldl=95,
                  target=dict(carb=60.3, fat=27.7, protein=12.1, sugar=7.9, rice=8.1, wheat=26.3, millet=0.2, animal=0.3)),
    "south": dict(sev=0.823, states={"Tamil Nadu": 72.1, "Karnataka": 61.1, "Andhra Pradesh": 84.6, "Kerala": 33.4, "Puducherry": 1.2},
                  age=(41, 31, 53), bmi=(23, 20, 26), male=0.45, prediabetes=0.46, t2d=0.11, inactive=0.64, family=0.16,
                  tobacco=0.13, alcohol=0.16, hypertension=0.26, tg=114, hdl=39, ldl=102,
                  target=dict(carb=63.7, fat=24.7, protein=11.5, sugar=7.1, rice=33.8, wheat=10.9, millet=0.4, animal=1.0)),
    "east": dict(sev=0.67, states={"Bihar": 104.1, "Jharkhand": 33.0, "Odisha": 42.0, "West Bengal": 91.3},
                 age=(40, 30, 53), bmi=(21, 18, 24), male=0.50, prediabetes=0.39, t2d=0.06, inactive=0.55, family=0.07,
                 tobacco=0.13, alcohol=0.16, hypertension=0.29, tg=101, hdl=38, ldl=90,
                 target=dict(carb=64.8, fat=24.0, protein=11.3, sugar=6.3, rice=31.1, wheat=13.4, millet=0.1, animal=0.6)),
    "west": dict(sev=0.758, states={"Maharashtra": 112.4, "Gujarat": 60.4, "Goa": 1.5},
                 age=(42, 32, 53), bmi=(22, 19, 25), male=0.48, prediabetes=0.42, t2d=0.12, inactive=0.71, family=0.09,
                 tobacco=0.08, alcohol=0.07, hypertension=0.27, tg=101, hdl=40, ldl=107,
                 target=dict(carb=59.6, fat=27.9, protein=12.2, sugar=7.1, rice=23.3, wheat=10.0, millet=5.1, animal=1.4)),
    "central": dict(sev=0.802, states={"Uttar Pradesh": 199.8, "Madhya Pradesh": 72.6, "Chhattisgarh": 25.5, "Uttarakhand": 10.1},
                    age=(40, 30, 53), bmi=(22, 19, 25), male=0.51, prediabetes=0.49, t2d=0.09, inactive=0.61, family=0.05,
                    tobacco=0.10, alcohol=0.10, hypertension=0.26, tg=104, hdl=39, ldl=83,
                    target=dict(carb=62.6, fat=25.6, protein=11.5, sugar=7.0, rice=17.1, wheat=30.0, millet=0.3, animal=0.3)),
    "northeast": dict(sev=0.561, states={"Assam": 31.2, "Tripura": 3.7, "Meghalaya": 3.0, "Manipur": 2.9, "Nagaland": 2.0, "Arunachal Pradesh": 1.4,
                              "Mizoram": 1.1, "Sikkim": 0.6},
                      age=(39, 30, 51), bmi=(22, 19, 24), male=0.50, prediabetes=0.34, t2d=0.06, inactive=0.54, family=0.06,
                      tobacco=0.24, alcohol=0.23, hypertension=0.28, tg=118, hdl=39, ldl=87,
                      target=dict(carb=63.8, fat=21.6, protein=13.6, sugar=2.1, rice=48.1, wheat=7.6, millet=0.1, animal=2.9)),
}
STAPLE = {"rice": {"ASC113", "BFP144", "ASC126", "ASC124", "ASC127", "BFP132", "ASC123", "ASC122", "OSR105", "ASC144", "BFP148", "ASC146",
                   "BFP152", "BFP045", "ASC052", "ASC054", "ASC282", "OSR011"},
          "wheat": {"ASC096", "ASC097", "ASC098", "BFP110", "OSR104", "OSR102", "BFP039", "ASC047", "ASC441", "ASC293", "ASC467", "OSR112", "ASC361", "BFP118"},
          "millet": {"RAGI_MUDDE", "JOWAR_BHAKRI", "BAJRA_ROTLA"}}


def plate(items, scale=1.0):
    """Total carbohydrate (available + fibre, as on a label), protein, fat, fibre, free sugar and the carbohydrate-
    weighted GI of a list of (food, units)."""
    c = p = f = fb = s = gl = 0.0
    kcal = dict.fromkeys(("rice", "wheat", "millet", "animal"), 0.0)  # energy from staples and animal protein, for checking
    for k, u in items:
        _, ca, pr, fa, fi, su, gi = FOODS[k]
        c, p, f, fb, s = c + ca * u, p + pr * u, f + fa * u, fb + fi * u, s + su * u
        gl += u * (su * 65 + (ca - su) * gi)
        for n, codes in STAPLE.items():
            kcal[n] += 4 * u * (ca - su) * (k in codes)
        kcal["animal"] += 4 * u * pr * (k in ANIMAL)
    return {"carbs": (c + fb) * scale, "protein": p * scale, "fat": f * scale, "fiber": fb * scale, "sugar": s * scale,
            **{f"kcal_{n}": v * scale for n, v in kcal.items()}, "gi": gl / max(c, 1e-9)}


def menu(region, state):
    """The plates open to someone from `state`, by meal: [(name, items, weight)]."""
    out = {}
    for kind, name, items, w, states in PLATES[region]:
        if states is None or state in states:
            out.setdefault(kind, []).append((name, items, w))
    return out


def calibrate(region, n=150, seed=11, steps=6):
    """The severity scale at which the region's share of normal glucose arises without the quota (bisection with
    common random numbers). Run once; the result is written into REGIONS[region]["sev"]. Without it the quota would
    keep the region's prevalence by discarding older and heavier people, and age and BMI would drift off target."""
    import numpy as np
    from . import synth
    R, lo, hi = REGIONS[region], 0.2, 1.6
    want = 1 - R["prediabetes"] - R["t2d"]
    for _ in range(steps):
        R["sev"] = mid = (lo + hi) / 2
        rng, healthy = np.random.default_rng(seed), 0
        for i in range(n):
            sp = synth._spec(rng, i + 1, region)
            plan = synth._plan(rng, sp, 14, 5, 0.10, 0.30, 0.08)
            healthy += synth._record(sp, plan, synth.simulate(sp, plan)[1], rng, 5, 0.03)["group"] == "healthy"
        lo, hi = (mid, hi) if healthy / n > want else (lo, mid)
    return round((lo + hi) / 2, 3)


def describe(P, region):
    """The generated cohort next to its ICMR-INDIAB-21 targets: diet as eaten (every meal, logged or not), body, glycaemia."""
    import numpy as np
    import pandas as pd
    m = pd.DataFrame([x for p in P for x in p["plan"]["meals"]])
    avail = (m["carbs"] - m["fiber"]).sum()
    E = 4 * avail + 4 * m["protein"].sum() + 9 * m["fat"].sum()
    s = pd.DataFrame([p["static"] for p in P])
    diet = {"kcal_day": E / sum(p["plan"]["T"] / 1440 for p in P), "carb": 400 * avail / E, "fat": 900 * m["fat"].sum() / E,
            "protein": 400 * m["protein"].sum() / E, "sugar": 400 * m["sugar"].sum() / E,
            **{n: 100 * m[f"kcal_{n}"].sum() / E for n in ("rice", "wheat", "millet", "animal")}, "meal_gi": float(np.average(m["gi"], weights=m["carbs"] - m["fiber"]))}
    grp = pd.Series([p["group"] for p in P]).value_counts(normalize=True)
    return {"n": len(P), "diet": {k: round(float(v), 1) for k, v in diet.items()},
            "body": {"age": float(s["age"].median()), "bmi": float(s["bmi"].median()), "male": round(float((s["sex"] == "M").mean()), 2),
                     "inactive": round(float(1 - s["physically_active"].mean()), 2), "family": round(float(s["family_history"].mean()), 2),
                     "hba1c": float(s["hba1c"].median()), "fpg": float(s["fpg"].median()), "tg": float(s["tg"].median()), "hdl": float(s["hdl"].median())},
            "groups": {g: round(float(grp.get(g, 0)), 2) for g in ("healthy", "prediabetes", "T2D")},
            "states": s["state"].value_counts().to_dict()}


def check(pool, P, cohort):
    """The twin inside one region: population and learned layer fitted on half the people, forecasts and what-ifs
    scored on the other half. In-simulator numbers, never accuracy claims about real Indians."""
    from . import evaluate as ev, hybrid
    from .hybrid import HORIZONS
    train, test = P[::2], P[1::2]
    pop, M = ev.fit_all(pool, train)
    te = ev.twins(pool, test, pop)
    r, m = hybrid.predict(M, ev.cat(te, "roll")), hybrid.predict(M, ev.cat(te, "meal"))
    r.to_pickle(ev.PROC / f"{cohort}_roll.pkl")  # every forecast, so other models can be scored at the same moments
    acc ={h: {k: ev.boot(r.dropna(subset=[f"y{h}"]), lambda x, k=k: ev.rmse(x, k, h)) for k in ("pers", "lgbm", "twin", "hybrid")} for h in HORIZONS}
    for h in HORIZONS:
        acc[h]["hybrid_minus_lgbm"] = ev.boot(r.dropna(subset=[f"y{h}"]), lambda x: ev.rmse(x, "hybrid", h) - ev.rmse(x, "lgbm", h))
    ver = ev.verification(pool, cohort)[0]
    mm = m.dropna(subset=["evt3h"])
    return {"accuracy": acc, "verification": ver, "meals": len(mm), "spike_share": round(float(mm["evt3h"].mean()), 3),
            "peak_rise": round(float((mm["peak"] - mm["g0"]).mean()), 1)}


def main():
    """Generate, export and check all six regional cohorts; writes results/india.json and results/INDIA.md."""
    import json
    from concurrent.futures import ProcessPoolExecutor
    from . import synth
    from .data import ROOT, load
    out = {}
    with ProcessPoolExecutor(4) as pool:
        for r in REGIONS:
            P = load(f"india_{r}")
            synth.export(P, ROOT / "data" / "synthetic" / f"india_{r}")
            out[r] = {**describe(P, r), "twin": check(pool, P, f"india_{r}")}
            print(r, out[r]["diet"], out[r]["groups"], {h: out[r]["twin"]["accuracy"][h]["hybrid"][0] for h in (30, 60, 120)}, flush=True)
    (ROOT / "results" / "india.json").write_text(json.dumps(out, indent=1, default=float))
    report(out, ROOT / "results" / "INDIA.md")



def report(out, path):
    R = list(out)
    names = {"north": "North", "south": "South", "east": "East", "west": "West", "central": "Central", "northeast": "Northeast"}
    head = lambda first: f"| {first} | " + " | ".join(names[r] for r in R) + " |\n|---|" + "---|" * len(R) + "\n"
    row = lambda label, f: f"| {label} | " + " | ".join(f(r) for r in R) + " |\n"
    vs = lambda got, want, d=1: f"{got:.{d}f} ({want:.{d}f})"
    ci = lambda v: f"{v[0]:.2f} ({v[1]:.2f} to {v[2]:.2f})"
    t = ["# Regional Indian synthetic cohorts\n\n",
         "Six simulated cohorts, one per ICMR-INDIAB region, from `python -m twin.india`. **No real person; not an accuracy claim about "
         "Indians.** They test the twin on Indian regional diets and lifestyles where the true physiology is known. Plates come from the "
         "Indian Nutrient Databank and measured Indian glycaemic indices; populations from ICMR-INDIAB-21 (n = 18,090). "
         "Sources and assumptions: `research/DATASETS.md` section 4.\n\n",
         "## 1. Generated cohort against its target (ICMR-INDIAB-21 regional median, in brackets)\n\n", head("Diet, % of energy")]
    for k, label in (("carb", "Carbohydrate"), ("fat", "Fat"), ("protein", "Protein"), ("sugar", "Free / added sugar"), ("rice", "White rice"),
                     ("wheat", "Wheat"), ("millet", "Millets"), ("animal", "Animal protein")):
        t.append(row(label, lambda r, k=k: vs(out[r]["diet"][k], REGIONS[r]["target"][k])))
    t.append(row("Energy, kcal/day (no target)", lambda r: f"{out[r]['diet']['kcal_day']:.0f}"))
    t.append(row("Carbohydrate-weighted meal GI", lambda r: f"{out[r]['diet']['meal_gi']:.0f}"))
    t += ["\n", head("People")]
    t.append(row("Median age", lambda r: vs(out[r]["body"]["age"], REGIONS[r]["age"][0], 0)))
    t.append(row("Median BMI", lambda r: vs(out[r]["body"]["bmi"], REGIONS[r]["bmi"][0])))
    t.append(row("Male share", lambda r: vs(out[r]["body"]["male"], REGIONS[r]["male"], 2)))
    t.append(row("Physically inactive", lambda r: vs(out[r]["body"]["inactive"], REGIONS[r]["inactive"], 2)))
    t.append(row("Family history of T2D", lambda r: vs(out[r]["body"]["family"], REGIONS[r]["family"], 2)))
    t.append(row("Prediabetes share", lambda r: vs(out[r]["groups"]["prediabetes"], REGIONS[r]["prediabetes"], 2)))
    t.append(row("Newly diagnosed T2D share", lambda r: vs(out[r]["groups"]["T2D"], REGIONS[r]["t2d"], 2)))
    t.append(row("Median HbA1c, %", lambda r: f"{out[r]['body']['hba1c']:.1f}"))
    t.append(row("Median fasting glucose, mg/dL", lambda r: f"{out[r]['body']['fpg']:.0f}"))
    t.append(row("Median triglycerides", lambda r: vs(out[r]["body"]["tg"], REGIONS[r]["tg"], 0)))
    t.append(row("Median HDL", lambda r: vs(out[r]["body"]["hdl"], REGIONS[r]["hdl"], 0)))
    t.append("\nINDIAB-21 reports median HbA1c 5.2 to 5.5% and fasting capillary glucose 92 to 98 mg/dL by region; our fasting value is "
             "plasma-like. Prevalence is matched exactly by construction (people are drawn until each region's shares are filled, by "
             "INDIAB's HbA1c-or-fasting-glucose rule); BMI and activity are then outcomes, and drift where the diet pushes glucose up.\n\n")
    t += ["## 2. After meals (test half, every eligible meal)\n\n", head("")]
    t.append(row("Meals", lambda r: str(out[r]["twin"]["meals"])))
    t.append(row("Meals followed by glucose > 180 mg/dL for 15+ min", lambda r: f"{100 * out[r]['twin']['spike_share']:.1f}%"))
    t.append(row("Mean 3-h peak rise, mg/dL", lambda r: f"{out[r]['twin']['peak_rise']:.1f}"))
    t += ["\n## 3. The twin inside each region (in-simulator; fitted on half the people, scored on the other half)\n\n", head("RMSE, mg/dL")]
    for h in (30, 60, 120):
        for k, label in (("pers", "Persistence"), ("lgbm", "LightGBM"), ("twin", "Physics twin"), ("hybrid", "Hybrid twin")):
            t.append(row(f"{label}, {h} min", lambda r, k=k, h=h: f"{out[r]['twin']['accuracy'][h][k][0]:.1f}"))
    t.append(row("Hybrid minus LightGBM, 60 min", lambda r: ci(out[r]["twin"]["accuracy"][60]["hybrid_minus_lgbm"])))
    t += ["\n## 4. Does the twin recover the truth? (simulator ground truth)\n\n", head("")]
    v = lambda r: out[r]["twin"]["verification"]
    t.append(row("Carb tolerance vs truth, Spearman", lambda r: f"{v(r)['rise50_spearman']:.2f}"))
    t.append(row("Basal glucose error, mg/dL", lambda r: f"{v(r)['gb_mae_mgdl']:.1f}"))
    for k, label in (("carbs_minus_40pct", "What-if 40% less food"), ("walk_30min", "What-if 30-min walk")):
        t.append(row(f"{label}: correlation with true effect", lambda r, k=k: f"{v(r)[k]['r']:.2f}" if k in v(r) else "-"))
        t.append(row(f"{label}: direction right", lambda r, k=k: f"{100 * v(r)[k]['sign_agreement']:.0f}%" if k in v(r) else "-"))
    t.append("\n**Limits.** Physiology is the same in every region; regions differ by plates, glycaemic index, body size, prevalence and "
             "activity. Stomach emptying scaled by GI is our assumption. Meal clock times are national (dinner 21:00, the only data "
             "found being a wellness-app report), not regional. Several dishes are INDB proxies (named so in `twin/india.py`).\n")
    path.write_text("".join(t), encoding="utf-8")


if __name__ == "__main__":
    main()
