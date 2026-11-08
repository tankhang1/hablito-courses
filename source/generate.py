import json, os, sys
OUT = sys.argv[1]

def T(en, vi): return {"en": en, "vi": vi}
def lesson(id, title, desc, icon, phrases, focus=None):
    return {"id": id, "title": title, "description": desc, **({"focus": focus} if focus else {}), "icon": icon,
            "phrases": [dict(es=p[0], en=p[1], vi=p[2], **({"note": T(p[3], p[4])} if len(p) > 3 else {})) for p in phrases]}
def ok(id, es, en, vi, r, ren, rvi, nxt=None):
    c = {"id": id, "es": es, "translation": T(en, vi), "correct": True, "response": r, "responseTranslation": T(ren, rvi)}
    if nxt: c["next"] = nxt
    return c
def bad(id, es, en, vi, fix, r, ren, rvi, nxt=None):
    c = {"id": id, "es": es, "translation": T(en, vi), "correct": False, "correction": fix, "response": r, "responseTranslation": T(ren, rvi)}
    if nxt: c["next"] = nxt
    return c
def node(id, prompt, en, vi, hen, hvi, *choices):
    return {"id": id, "prompt": prompt, "translation": T(en, vi), "hint": T(hen, hvi), "choices": list(choices)}
def convo(id, title, desc, icon, nodes, duration="3 min"):
    return {"id": id, "title": title, "description": desc, "icon": icon, "duration": duration, "start": nodes[0]["id"], "nodes": nodes}

packs = []
def pack(n, cefr, title, desc, lessons, conversations):
    packs.append({"schemaVersion": 1, "id": f"level-{n:02d}", "version": 1, "level": n, "cefr": cefr,
                  "title": title, "description": desc, "lessons": lessons, "conversations": conversations})

# 1 ─────────────────────────────────────────
pack(1, "A1", T("Starter 1: First words", "Khởi đầu 1: Những từ đầu tiên"),
     T("Tiny everyday words and how you feel.", "Những từ nhỏ hằng ngày và cảm xúc của bạn."),
 [lesson("everyday-words", T("Everyday words", "Từ dùng hằng ngày"), T("Yes, no, and the polite basics.", "Có, không và những từ lịch sự cơ bản."), "message-circle", [
    ("Sí", "Yes", "Có / Vâng"), ("No", "No", "Không"), ("Por favor", "Please", "Làm ơn"),
    ("Muchas gracias", "Thank you very much", "Cảm ơn rất nhiều"), ("Con permiso", "Excuse me (to pass)", "Xin phép cho tôi qua"),
    ("Lo siento", "I'm sorry", "Tôi xin lỗi")]),
  lesson("feelings", T("How I feel", "Cảm xúc của tôi"), T("Say if you are tired, hungry, or happy.", "Nói bạn mệt, đói hay vui."), "smile", [
    ("Estoy bien", "I'm fine", "Tôi ổn"), ("Estoy cansado", "I'm tired", "Tôi mệt", "Women say “cansada”.", "Nữ nói “cansada”."),
    ("Tengo hambre", "I'm hungry", "Tôi đói"), ("Tengo sed", "I'm thirsty", "Tôi khát"),
    ("Estoy feliz", "I'm happy", "Tôi vui"), ("Tengo frío", "I'm cold", "Tôi lạnh")])],
 [convo("classmate", T("Meet a classmate", "Gặp bạn cùng lớp"), T("Say hi and share how you feel today.", "Chào hỏi và chia sẻ hôm nay bạn thế nào."), "heart", [
    node("hi", "¡Hola! ¿Cómo estás?", "Hi! How are you?", "Chào bạn! Bạn khỏe không?", "Answer with “Estoy…”.", "Trả lời bằng “Estoy…”.",
      ok("fine", "Estoy bien, gracias.", "I'm fine, thanks.", "Mình ổn, cảm ơn.", "¡Qué bueno! ¿Tienes hambre?", "Great! Are you hungry?", "Tốt quá! Bạn có đói không?", "hungry"),
      ok("tired", "Estoy cansado.", "I'm tired.", "Mình mệt.", "Ay, lo siento. ¿Tienes hambre?", "Oh, sorry. Are you hungry?", "Ôi, tiếc quá. Bạn có đói không?", "hungry"),
      bad("thanks", "De nada.", "You're welcome.", "Không có gì.", "Estoy bien, gracias.", "Mmm… ¿pero cómo estás?", "Hmm… but how are you?", "Ừm… nhưng bạn khỏe không?", "hungry")),
    node("hungry", "¿Tienes hambre?", "Are you hungry?", "Bạn có đói không?", "“Sí” or “No”, then a short reason.", "“Sí” hoặc “No”, kèm một lý do ngắn.",
      ok("yes", "Sí, tengo hambre.", "Yes, I'm hungry.", "Có, mình đói.", "Yo también. ¿Vamos a comer?", "Me too. Shall we eat?", "Mình cũng vậy. Đi ăn nhé?", "eat"),
      ok("no", "No, gracias. Tengo sed.", "No, thanks. I'm thirsty.", "Không, cảm ơn. Mình khát.", "Hay agua aquí. ¿Vamos?", "There's water here. Shall we go?", "Ở đây có nước. Đi nhé?", "eat"),
      bad("cold", "Tengo frío.", "I'm cold.", "Mình lạnh.", "Sí, tengo hambre.", "Toma mi chaqueta. ¿Y hambre?", "Take my jacket. And hungry?", "Cầm áo khoác của mình đi. Còn đói không?", "eat")),
    node("eat", "¡Vamos! Hasta luego, ¿sí?", "Let's go! See you later, OK?", "Đi thôi! Lát gặp nhé?", "Say thank you and goodbye.", "Cảm ơn và tạm biệt.",
      ok("bye", "Sí, muchas gracias. ¡Hasta luego!", "Yes, thanks a lot. See you later!", "Ừ, cảm ơn nhiều. Lát gặp!", "¡Hasta luego!", "See you later!", "Lát gặp nhé!"),
      ok("please", "Sí, por favor.", "Yes, please.", "Ừ, làm ơn.", "¡Perfecto!", "Perfect!", "Tuyệt!"),
      bad("sorry", "Lo siento.", "I'm sorry.", "Mình xin lỗi.", "Sí, muchas gracias. ¡Hasta luego!", "¿Por qué? ¡Todo bien!", "Why? All good!", "Sao vậy? Mọi thứ ổn mà!"))])])

# 2 ─────────────────────────────────────────
pack(2, "A1", T("Starter 2: Time & days", "Khởi đầu 2: Thời gian & ngày"),
     T("Days of the week and telling the time.", "Các ngày trong tuần và cách nói giờ."),
 [lesson("days", T("Days of the week", "Các ngày trong tuần"), T("Plan your week in Spanish.", "Lên kế hoạch tuần bằng tiếng Tây Ban Nha."), "calendar", [
    ("el lunes", "Monday", "Thứ Hai"), ("el martes", "Tuesday", "Thứ Ba"), ("el miércoles", "Wednesday", "Thứ Tư"),
    ("el viernes", "Friday", "Thứ Sáu"), ("el fin de semana", "the weekend", "cuối tuần"), ("hoy y mañana", "today and tomorrow", "hôm nay và ngày mai")]),
  lesson("time", T("Telling the time", "Nói giờ"), T("Ask and say what time it is.", "Hỏi và nói bây giờ là mấy giờ."), "clock", [
    ("¿Qué hora es?", "What time is it?", "Mấy giờ rồi?"), ("Es la una.", "It's one o'clock.", "Một giờ.", "Only one o'clock uses “es la”.", "Chỉ một giờ mới dùng “es la”."),
    ("Son las tres.", "It's three o'clock.", "Ba giờ."), ("Son las cinco y media.", "It's half past five.", "Năm giờ rưỡi."),
    ("por la mañana", "in the morning", "vào buổi sáng"), ("por la noche", "at night", "vào buổi tối")])],
 [convo("friday-plan", T("Make a plan for Friday", "Hẹn nhau thứ Sáu"), T("Agree on a day and a time.", "Thống nhất ngày và giờ."), "map-pin", [
    node("day", "¿Quieres ir al cine?", "Do you want to go to the movies?", "Bạn muốn đi xem phim không?", "Suggest a day with “el…”.", "Đề xuất một ngày với “el…”.",
      ok("friday", "Sí, ¿el viernes?", "Yes, on Friday?", "Có, thứ Sáu nhé?", "¡Perfecto! ¿A qué hora?", "Perfect! What time?", "Tuyệt! Mấy giờ?", "time"),
      ok("weekend", "Sí, el fin de semana.", "Yes, on the weekend.", "Có, cuối tuần nhé.", "Bien, el sábado. ¿A qué hora?", "Good, Saturday. What time?", "Được, thứ Bảy. Mấy giờ?", "time"),
      bad("tired", "Estoy cansado.", "I'm tired.", "Mình mệt.", "Sí, ¿el viernes?", "Entonces otro día. ¿El viernes? ¿A qué hora?", "Another day then. Friday? What time?", "Vậy hôm khác. Thứ Sáu nhé? Mấy giờ?", "time")),
    node("time", "¿A qué hora nos vemos?", "What time shall we meet?", "Mấy giờ mình gặp nhau?", "Use “a las…” to give a time.", "Dùng “a las…” để nói giờ.",
      ok("seven", "A las siete de la noche.", "At seven in the evening.", "Lúc bảy giờ tối.", "Muy bien, a las siete.", "Great, at seven.", "Được, bảy giờ nhé.", "confirm"),
      ok("five", "A las cinco y media.", "At half past five.", "Lúc năm giờ rưỡi.", "Perfecto, a las cinco y media.", "Perfect, at half past five.", "Tuyệt, năm giờ rưỡi.", "confirm"),
      bad("monday", "El lunes.", "Monday.", "Thứ Hai.", "A las siete de la noche.", "No, la hora… ¿a las siete?", "No, the time… at seven?", "Không, giờ cơ… bảy giờ nhé?", "confirm")),
    node("confirm", "Entonces, nos vemos el viernes.", "So, see you on Friday.", "Vậy hẹn gặp thứ Sáu nhé.", "Close with “Nos vemos” or “Hasta…”.", "Kết thúc bằng “Nos vemos” hoặc “Hasta…”.",
      ok("see", "¡Sí, nos vemos!", "Yes, see you!", "Ừ, hẹn gặp!", "¡Chao!", "Bye!", "Chào nhé!"),
      ok("until", "¡Hasta el viernes!", "See you Friday!", "Hẹn thứ Sáu!", "¡Hasta el viernes!", "See you Friday!", "Hẹn thứ Sáu!"),
      bad("what", "¿Qué hora es?", "What time is it?", "Mấy giờ rồi?", "¡Sí, nos vemos!", "Son las tres. ¡Nos vemos el viernes!", "It's three. See you Friday!", "Ba giờ rồi. Hẹn thứ Sáu nhé!"))])])

# 3 ─────────────────────────────────────────
pack(3, "A1", T("Beginner 1: Food & drinks", "Sơ cấp 1: Đồ ăn & đồ uống"),
     T("Common foods and how to order them.", "Món ăn phổ biến và cách gọi món."),
 [lesson("food", T("At the table", "Trên bàn ăn"), T("Everyday foods and drinks.", "Món ăn, đồ uống hằng ngày."), "coffee", [
    ("el agua", "water", "nước"), ("el pan", "bread", "bánh mì"), ("el pollo", "chicken", "thịt gà"),
    ("el arroz", "rice", "cơm / gạo"), ("la fruta", "fruit", "trái cây"), ("el jugo de naranja", "orange juice", "nước cam")]),
  lesson("ordering", T("Ordering food", "Gọi món"), T("Ask, order, and pay at a restaurant.", "Hỏi, gọi món và thanh toán ở nhà hàng."), "list", [
    ("Quiero el pollo, por favor.", "I'd like the chicken, please.", "Cho tôi món gà."), ("¿Qué me recomienda?", "What do you recommend?", "Bạn gợi ý món gì?"),
    ("Sin picante, por favor.", "Not spicy, please.", "Đừng cho cay nhé."), ("Para llevar.", "To go.", "Mang đi."),
    ("Está delicioso.", "It's delicious.", "Ngon quá."), ("La cuenta, por favor.", "The check, please.", "Cho tôi tính tiền.")])],
 [convo("lunch", T("Order lunch", "Gọi bữa trưa"), T("Choose a dish, a drink, and pay.", "Chọn món, đồ uống và thanh toán."), "coffee", [
    node("order", "Buenas tardes. ¿Qué va a comer?", "Good afternoon. What will you have?", "Chào buổi chiều. Bạn dùng món gì?", "Start with “Quiero…”.", "Bắt đầu bằng “Quiero…”.",
      ok("chicken", "Quiero el pollo con arroz.", "I'd like chicken with rice.", "Cho tôi gà với cơm.", "Muy bien. ¿Y para tomar?", "Very good. And to drink?", "Được ạ. Còn đồ uống?", "drink"),
      ok("recommend", "¿Qué me recomienda?", "What do you recommend?", "Bạn gợi ý món gì?", "El pollo está delicioso. ¿Y para tomar?", "The chicken is delicious. And to drink?", "Món gà rất ngon. Còn đồ uống?", "drink"),
      bad("bill", "La cuenta, por favor.", "The check, please.", "Cho tôi tính tiền.", "Quiero el pollo con arroz.", "¡Pero todavía no come! ¿Qué quiere?", "But you haven't eaten yet! What would you like?", "Nhưng bạn chưa ăn mà! Bạn muốn gì?", "drink")),
    node("drink", "¿Algo para tomar?", "Anything to drink?", "Bạn uống gì không?", "Name a drink and add “por favor”.", "Nói tên đồ uống và thêm “por favor”.",
      ok("juice", "Un jugo de naranja, por favor.", "An orange juice, please.", "Cho tôi một ly nước cam.", "Claro, ahora se lo traigo.", "Sure, I'll bring it now.", "Vâng, tôi mang ra ngay.", "pay"),
      ok("water", "Agua, por favor.", "Water, please.", "Cho tôi nước lọc.", "Muy bien.", "Very good.", "Được ạ.", "pay"),
      bad("bread", "El pan.", "The bread.", "Bánh mì.", "Agua, por favor.", "El pan viene con la comida. ¿Para tomar?", "Bread comes with the meal. To drink?", "Bánh mì có kèm món rồi. Còn đồ uống?", "pay")),
    node("pay", "¿Le gustó la comida?", "Did you like the food?", "Bạn thấy món ăn thế nào?", "Compliment the food, then ask for the check.", "Khen món ăn, rồi xin tính tiền.",
      ok("delicious", "Sí, está delicioso. La cuenta, por favor.", "Yes, it's delicious. The check, please.", "Có, ngon lắm. Cho tôi tính tiền.", "Gracias. Aquí tiene.", "Thank you. Here you go.", "Cảm ơn. Của bạn đây."),
      ok("togo", "Sí. ¿Me lo pone para llevar?", "Yes. Could you pack it to go?", "Có. Gói mang đi giúp tôi nhé?", "Claro que sí.", "Of course.", "Tất nhiên rồi."),
      bad("spicy", "Sin picante.", "Not spicy.", "Đừng cho cay.", "Sí, está delicioso. La cuenta, por favor.", "Ya comió… ¿Le traigo la cuenta?", "You already ate… Shall I bring the check?", "Bạn ăn xong rồi mà… Tôi mang hóa đơn nhé?"))])])

# 4 ─────────────────────────────────────────
pack(4, "A1", T("Beginner 2: Shopping & money", "Sơ cấp 2: Mua sắm & tiền bạc"),
     T("Colors, clothes, prices, and paying.", "Màu sắc, quần áo, giá cả và thanh toán."),
 [lesson("clothes", T("Colors & clothes", "Màu sắc & quần áo"), T("Describe what you want to buy.", "Mô tả món đồ bạn muốn mua."), "shopping-bag", [
    ("la camisa roja", "the red shirt", "chiếc áo sơ mi đỏ"), ("los zapatos negros", "the black shoes", "đôi giày đen"),
    ("el vestido azul", "the blue dress", "chiếc váy xanh dương"), ("una chaqueta verde", "a green jacket", "một chiếc áo khoác xanh lá"),
    ("¿Lo tiene en blanco?", "Do you have it in white?", "Có màu trắng không?"), ("Es muy grande.", "It's too big.", "Rộng quá.")]),
  lesson("paying", T("Prices & paying", "Giá cả & thanh toán"), T("Ask the price and pay.", "Hỏi giá và trả tiền."), "credit-card", [
    ("¿Cuánto es?", "How much is it?", "Bao nhiêu tiền?"), ("¿Hay descuento?", "Is there a discount?", "Có giảm giá không?"),
    ("Pago en efectivo.", "I'll pay in cash.", "Tôi trả tiền mặt."), ("Pago con tarjeta.", "I'll pay by card.", "Tôi trả bằng thẻ."),
    ("Es barato.", "It's cheap.", "Rẻ."), ("¿Me da el recibo?", "Can I have the receipt?", "Cho tôi xin hóa đơn.")])],
 [convo("shoes", T("Buy shoes", "Mua giày"), T("Find a color, check the price, and pay.", "Chọn màu, hỏi giá và thanh toán."), "briefcase", [
    node("look", "Hola, ¿qué busca?", "Hi, what are you looking for?", "Chào bạn, bạn tìm gì?", "Say the item and its color.", "Nói món đồ và màu sắc.",
      ok("black", "Busco zapatos negros.", "I'm looking for black shoes.", "Tôi tìm giày đen.", "Tenemos estos. ¿Le gustan?", "We have these. Do you like them?", "Có đôi này. Bạn thích không?", "price"),
      ok("white", "¿Tiene estos zapatos en blanco?", "Do you have these shoes in white?", "Đôi này có màu trắng không?", "Sí, aquí están. ¿Le gustan?", "Yes, here they are. Do you like them?", "Có, đây ạ. Bạn thích không?", "price"),
      bad("hungry", "Tengo hambre.", "I'm hungry.", "Tôi đói.", "Busco zapatos negros.", "Aquí vendemos zapatos. ¿Qué color busca?", "We sell shoes here. What color?", "Ở đây bán giày. Bạn tìm màu gì?", "price")),
    node("price", "Son muy bonitos, ¿verdad?", "They're very nice, right?", "Đẹp lắm phải không?", "Ask “¿Cuánto…?”.", "Hỏi “¿Cuánto…?”.",
      ok("howmuch", "Sí. ¿Cuánto es?", "Yes. How much is it?", "Ừ. Bao nhiêu tiền?", "Son seiscientos pesos.", "They're 600 pesos.", "Sáu trăm peso.", "pay"),
      ok("discount", "Sí. ¿Hay descuento?", "Yes. Is there a discount?", "Ừ. Có giảm giá không?", "Hoy hay diez por ciento. Son quinientos cuarenta.", "Today there's 10% off. It's 540.", "Hôm nay giảm 10%. Còn 540.", "pay"),
      bad("big", "Es muy grande.", "It's too big.", "Rộng quá.", "Sí. ¿Cuánto es?", "Le traigo otra talla. Cuestan seiscientos.", "I'll bring another size. They're 600.", "Tôi lấy cỡ khác. Giá 600.", "pay")),
    node("pay", "¿Cómo va a pagar?", "How will you pay?", "Bạn thanh toán thế nào?", "“Pago con…” or “Pago en…”.", "“Pago con…” hoặc “Pago en…”.",
      ok("card", "Pago con tarjeta.", "I'll pay by card.", "Tôi trả bằng thẻ.", "Perfecto. Aquí tiene su recibo.", "Perfect. Here's your receipt.", "Tuyệt. Hóa đơn của bạn đây."),
      ok("cash", "Pago en efectivo.", "I'll pay in cash.", "Tôi trả tiền mặt.", "Muy bien. Gracias por su compra.", "Very good. Thanks for shopping.", "Được ạ. Cảm ơn bạn đã mua hàng."),
      bad("cheap", "Es barato.", "It's cheap.", "Rẻ.", "Pago con tarjeta.", "¡Sí! ¿Pero con tarjeta o en efectivo?", "Yes! But card or cash?", "Đúng! Nhưng thẻ hay tiền mặt?"))])])

# 5 ─────────────────────────────────────────
pack(5, "A2", T("Elementary 1: Getting around", "Sơ trung 1: Đi lại trong thành phố"),
     T("Places in town and simple directions.", "Địa điểm trong thành phố và chỉ đường đơn giản."),
 [lesson("places", T("Places in town", "Địa điểm trong thành phố"), T("Name the places you need.", "Gọi tên những nơi bạn cần đến."), "map", [
    ("el banco", "the bank", "ngân hàng"), ("la farmacia", "the pharmacy", "hiệu thuốc"), ("la parada de autobús", "the bus stop", "trạm xe buýt"),
    ("el supermercado", "the supermarket", "siêu thị"), ("el hospital", "the hospital", "bệnh viện"), ("la estación de tren", "the train station", "ga tàu")]),
  lesson("directions", T("Directions", "Chỉ đường"), T("Understand left, right, and straight ahead.", "Hiểu trái, phải và đi thẳng."), "navigation", [
    ("a la derecha", "to the right", "bên phải"), ("a la izquierda", "to the left", "bên trái"), ("todo recto", "straight ahead", "đi thẳng"),
    ("en la esquina", "on the corner", "ở góc đường"), ("cerca de aquí", "near here", "gần đây"), ("lejos de aquí", "far from here", "xa đây")])],
 [convo("pharmacy", T("Find the pharmacy", "Tìm hiệu thuốc"), T("Ask the way and confirm the directions.", "Hỏi đường và xác nhận lại."), "compass", [
    node("ask", "¿Le puedo ayudar?", "Can I help you?", "Tôi giúp gì được cho bạn?", "Ask “¿Dónde está…?”.", "Hỏi “¿Dónde está…?”.",
      ok("where", "Sí. ¿Dónde está la farmacia?", "Yes. Where is the pharmacy?", "Vâng. Hiệu thuốc ở đâu?", "Siga todo recto y a la derecha.", "Go straight and then right.", "Đi thẳng rồi rẽ phải.", "repeat"),
      ok("near", "¿Hay una farmacia cerca de aquí?", "Is there a pharmacy near here?", "Gần đây có hiệu thuốc không?", "Sí, siga todo recto y a la derecha.", "Yes, go straight and then right.", "Có, đi thẳng rồi rẽ phải.", "repeat"),
      bad("cash", "Pago en efectivo.", "I'll pay in cash.", "Tôi trả tiền mặt.", "Sí. ¿Dónde está la farmacia?", "¿Busca algo? ¿La farmacia? Está a la derecha.", "Looking for something? The pharmacy? It's on the right.", "Bạn tìm gì à? Hiệu thuốc? Ở bên phải.", "repeat")),
    node("repeat", "Todo recto y luego a la derecha.", "Straight ahead and then right.", "Đi thẳng rồi rẽ phải.", "Repeat back to confirm.", "Nhắc lại để xác nhận.",
      ok("confirm", "Todo recto y a la derecha, ¿verdad?", "Straight and to the right, right?", "Đi thẳng rồi rẽ phải, đúng không?", "Exacto. Está en la esquina.", "Exactly. It's on the corner.", "Đúng vậy. Ở góc đường.", "far"),
      ok("slow", "Más despacio, por favor.", "More slowly, please.", "Làm ơn nói chậm hơn.", "To-do rec-to… y a la derecha. En la esquina.", "Straight… and right. On the corner.", "Đi thẳng… rồi rẽ phải. Ở góc đường.", "far"),
      bad("left", "¿A la izquierda?", "To the left?", "Rẽ trái à?", "Todo recto y a la derecha, ¿verdad?", "No, a la derecha. En la esquina.", "No, to the right. On the corner.", "Không, rẽ phải. Ở góc đường.", "far")),
    node("far", "Está muy cerca, cinco minutos.", "It's very close, five minutes.", "Rất gần, năm phút thôi.", "Thank them.", "Cảm ơn họ.",
      ok("thanks", "¡Muchas gracias por su ayuda!", "Thanks a lot for your help!", "Cảm ơn bạn đã giúp!", "De nada. ¡Que le vaya bien!", "You're welcome. Take care!", "Không có gì. Chúc bạn may mắn!"),
      ok("great", "Perfecto, gracias.", "Perfect, thanks.", "Tuyệt, cảm ơn.", "De nada.", "You're welcome.", "Không có gì."),
      bad("hospital", "¿Dónde está el hospital?", "Where is the hospital?", "Bệnh viện ở đâu?", "¡Muchas gracias por su ayuda!", "¿El hospital? Está lejos de aquí. Tome un taxi.", "The hospital? It's far. Take a taxi.", "Bệnh viện à? Xa lắm. Bạn đi taxi nhé."))])])

# 6 ─────────────────────────────────────────
pack(6, "A2", T("Elementary 2: Home & family", "Sơ trung 2: Nhà cửa & gia đình"),
     T("Talk about your family and your home.", "Nói về gia đình và nhà của bạn."),
 [lesson("family", T("My family", "Gia đình tôi"), T("Introduce the people at home.", "Giới thiệu những người trong nhà."), "users", [
    ("mi madre", "my mother", "mẹ tôi"), ("mi padre", "my father", "bố tôi"), ("mi hermano mayor", "my older brother", "anh trai tôi"),
    ("mi hermana menor", "my younger sister", "em gái tôi"), ("mis hijos", "my children", "các con tôi"), ("mis abuelos", "my grandparents", "ông bà tôi")]),
  lesson("home", T("At home", "Ở nhà"), T("Rooms, pets, and where you live.", "Phòng ốc, thú cưng và nơi bạn sống."), "home", [
    ("la cocina", "the kitchen", "nhà bếp"), ("el dormitorio", "the bedroom", "phòng ngủ"), ("Vivo en un apartamento.", "I live in an apartment.", "Tôi sống ở căn hộ."),
    ("Tengo un perro.", "I have a dog.", "Tôi có một con chó."), ("Mi casa es pequeña.", "My house is small.", "Nhà tôi nhỏ."),
    ("Vivo con mi familia.", "I live with my family.", "Tôi sống cùng gia đình.")])],
 [convo("family-talk", T("Talk about your family", "Kể về gia đình"), T("Answer questions about who you live with.", "Trả lời câu hỏi về người bạn sống cùng."), "heart", [
    node("live", "¿Con quién vives?", "Who do you live with?", "Bạn sống với ai?", "Start with “Vivo con…”.", "Bắt đầu bằng “Vivo con…”.",
      ok("family", "Vivo con mi familia.", "I live with my family.", "Mình sống với gia đình.", "¡Qué bien! ¿Tienes hermanos?", "Nice! Do you have siblings?", "Hay quá! Bạn có anh chị em không?", "siblings"),
      ok("alone", "Vivo solo en un apartamento.", "I live alone in an apartment.", "Mình sống một mình ở căn hộ.", "Ah, ¿y tienes hermanos?", "Ah, and do you have siblings?", "À, thế bạn có anh chị em không?", "siblings"),
      bad("kitchen", "La cocina.", "The kitchen.", "Nhà bếp.", "Vivo con mi familia.", "Jaja, ¿con quién vives?", "Haha, who do you live with?", "Haha, bạn sống với ai?", "siblings")),
    node("siblings", "¿Tienes hermanos?", "Do you have brothers or sisters?", "Bạn có anh chị em không?", "Use “Tengo…”.", "Dùng “Tengo…”.",
      ok("brother", "Sí, tengo un hermano mayor.", "Yes, I have an older brother.", "Có, mình có một anh trai.", "Yo tengo dos hermanas. ¿Y mascotas?", "I have two sisters. And pets?", "Mình có hai chị gái. Còn thú cưng?", "pets"),
      ok("none", "No, soy hijo único.", "No, I'm an only child.", "Không, mình là con một.", "Ah, entiendo. ¿Y mascotas?", "Ah, I see. And pets?", "À, mình hiểu. Còn thú cưng?", "pets"),
      bad("grand", "Mis abuelos.", "My grandparents.", "Ông bà mình.", "Sí, tengo un hermano mayor.", "¡Qué bonito! Pero, ¿tienes hermanos?", "Lovely! But do you have siblings?", "Dễ thương quá! Nhưng bạn có anh chị em không?", "pets")),
    node("pets", "¿Tienes mascotas en casa?", "Do you have pets at home?", "Ở nhà bạn có thú cưng không?", "Say what pet you have.", "Nói bạn nuôi con gì.",
      ok("dog", "Sí, tengo un perro.", "Yes, I have a dog.", "Có, mình nuôi một con chó.", "¡Me encantan los perros!", "I love dogs!", "Mình rất thích chó!"),
      ok("no", "No, mi casa es pequeña.", "No, my house is small.", "Không, nhà mình nhỏ.", "Claro, tiene sentido.", "Sure, that makes sense.", "Ừ, hợp lý."),
      bad("bed", "El dormitorio.", "The bedroom.", "Phòng ngủ.", "Sí, tengo un perro.", "¿Tu mascota duerme en el dormitorio?", "Does your pet sleep in the bedroom?", "Thú cưng của bạn ngủ trong phòng ngủ à?"))])])

# 7 ─────────────────────────────────────────
pack(7, "A2", T("Pre-intermediate 1: Health & emergencies", "Tiền trung cấp 1: Sức khỏe & khẩn cấp"),
     T("Describe pain and get help fast.", "Mô tả cơn đau và nhờ giúp đỡ nhanh."),
 [lesson("pain", T("Body & pain", "Cơ thể & cơn đau"), T("Tell a doctor what hurts.", "Nói với bác sĩ chỗ nào đau."), "activity", [
    ("Me duele la cabeza.", "My head hurts.", "Tôi đau đầu."), ("Me duele el estómago.", "My stomach hurts.", "Tôi đau bụng."),
    ("Me duele la garganta.", "My throat hurts.", "Tôi đau họng."), ("Tengo fiebre.", "I have a fever.", "Tôi bị sốt."),
    ("Tengo tos.", "I have a cough.", "Tôi bị ho."), ("Estoy mareado.", "I feel dizzy.", "Tôi chóng mặt.", "Women say “mareada”.", "Nữ nói “mareada”.")]),
  lesson("help", T("Getting help", "Nhờ giúp đỡ"), T("Phrases for urgent moments.", "Những câu cho lúc khẩn cấp."), "alert-triangle", [
    ("¡Ayuda!", "Help!", "Cứu với!"), ("Llame a una ambulancia.", "Call an ambulance.", "Gọi xe cứu thương giúp tôi."),
    ("Necesito un médico.", "I need a doctor.", "Tôi cần bác sĩ."), ("¿Dónde está el hospital?", "Where is the hospital?", "Bệnh viện ở đâu?"),
    ("Soy alérgico a la penicilina.", "I'm allergic to penicillin.", "Tôi dị ứng với penicillin."), ("Es urgente.", "It's urgent.", "Việc này khẩn cấp.")])],
 [convo("doctor", T("At the doctor", "Đi khám bác sĩ"), T("Explain your symptoms and allergies.", "Trình bày triệu chứng và dị ứng."), "heart", [
    node("what", "¿Qué le pasa?", "What's wrong?", "Bạn bị sao vậy?", "Use “Me duele…” or “Tengo…”.", "Dùng “Me duele…” hoặc “Tengo…”.",
      ok("throat", "Me duele la garganta y tengo tos.", "My throat hurts and I have a cough.", "Tôi đau họng và bị ho.", "¿Desde cuándo?", "Since when?", "Từ khi nào?", "since"),
      ok("fever", "Tengo fiebre y estoy mareado.", "I have a fever and feel dizzy.", "Tôi bị sốt và chóng mặt.", "Entiendo. ¿Desde cuándo?", "I see. Since when?", "Tôi hiểu. Từ khi nào?", "since"),
      bad("bank", "¿Dónde está el banco?", "Where is the bank?", "Ngân hàng ở đâu?", "Me duele la garganta y tengo tos.", "Esto es una clínica. ¿Qué le duele?", "This is a clinic. What hurts?", "Đây là phòng khám. Bạn đau ở đâu?", "since")),
    node("since", "¿Desde cuándo se siente así?", "How long have you felt like this?", "Bạn bị thế này bao lâu rồi?", "“Desde ayer” means “since yesterday”.", "“Desde ayer” nghĩa là “từ hôm qua”.",
      ok("yesterday", "Desde ayer por la noche.", "Since last night.", "Từ tối hôm qua.", "Bien. ¿Es alérgico a algún medicamento?", "OK. Are you allergic to any medicine?", "Được. Bạn có dị ứng thuốc nào không?", "allergy"),
      ok("days", "Desde hace dos días.", "For two days.", "Hai ngày nay rồi.", "Bien. ¿Es alérgico a algún medicamento?", "OK. Are you allergic to any medicine?", "Được. Bạn có dị ứng thuốc nào không?", "allergy"),
      bad("help", "¡Ayuda!", "Help!", "Cứu với!", "Desde ayer por la noche.", "Tranquilo, está en buenas manos. ¿Desde cuándo?", "Relax, you're in good hands. Since when?", "Bình tĩnh, bạn đang được chăm sóc. Từ khi nào?", "allergy")),
    node("allergy", "¿Es alérgico a algún medicamento?", "Are you allergic to any medicine?", "Bạn có dị ứng thuốc nào không?", "Say “Soy alérgico a…” or “No”.", "Nói “Soy alérgico a…” hoặc “No”.",
      ok("pen", "Sí, soy alérgico a la penicilina.", "Yes, I'm allergic to penicillin.", "Có, tôi dị ứng penicillin.", "Gracias. Le doy otro medicamento.", "Thanks. I'll give you a different medicine.", "Cảm ơn. Tôi sẽ cho bạn thuốc khác."),
      ok("none", "No, a ninguno.", "No, none.", "Không, không có.", "Muy bien. Tome esto cada ocho horas.", "Very good. Take this every eight hours.", "Được. Uống thuốc này mỗi tám tiếng."),
      bad("urgent", "Es urgente.", "It's urgent.", "Khẩn cấp lắm.", "No, a ninguno.", "Ya lo estoy atendiendo. ¿Alergias?", "I'm already treating you. Allergies?", "Tôi đang khám cho bạn rồi. Có dị ứng không?"))])])

# 8 ─────────────────────────────────────────
pack(8, "A2", T("Pre-intermediate 2: Work & study", "Tiền trung cấp 2: Công việc & học tập"),
     T("Jobs, schedules, and small talk at work.", "Nghề nghiệp, lịch làm việc và trò chuyện nơi công sở."),
 [lesson("jobs", T("Jobs", "Nghề nghiệp"), T("Say what you do.", "Nói bạn làm nghề gì."), "briefcase", [
    ("¿A qué te dedicas?", "What do you do?", "Bạn làm nghề gì?"), ("Soy profesor.", "I'm a teacher.", "Tôi là giáo viên.", "Women say “profesora”.", "Nữ nói “profesora”."),
    ("Trabajo en una oficina.", "I work in an office.", "Tôi làm việc ở văn phòng."), ("Estudio en la universidad.", "I study at the university.", "Tôi học đại học."),
    ("Trabajo desde casa.", "I work from home.", "Tôi làm việc tại nhà."), ("Busco trabajo.", "I'm looking for a job.", "Tôi đang tìm việc.")]),
  lesson("schedule", T("My schedule", "Lịch của tôi"), T("Talk about your day at work.", "Nói về một ngày làm việc."), "clock", [
    ("Empiezo a las nueve.", "I start at nine.", "Tôi bắt đầu lúc chín giờ."), ("Termino a las cinco.", "I finish at five.", "Tôi xong lúc năm giờ."),
    ("Tengo una reunión.", "I have a meeting.", "Tôi có cuộc họp."), ("Estoy ocupado ahora.", "I'm busy right now.", "Bây giờ tôi đang bận."),
    ("¿Tienes un minuto?", "Do you have a minute?", "Bạn có rảnh một phút không?"), ("Nos vemos mañana.", "See you tomorrow.", "Mai gặp nhé.")])],
 [convo("work-chat", T("Small talk at work", "Trò chuyện ở chỗ làm"), T("Chat with a new coworker.", "Nói chuyện với đồng nghiệp mới."), "briefcase", [
    node("job", "Hola, soy Carla. ¿Eres nuevo aquí?", "Hi, I'm Carla. Are you new here?", "Chào, mình là Carla. Bạn mới vào à?", "Say yes and what your role is.", "Nói “có” và vị trí của bạn.",
      ok("new", "Sí, soy el nuevo diseñador.", "Yes, I'm the new designer.", "Ừ, mình là nhà thiết kế mới.", "¡Bienvenido! ¿A qué hora empiezas?", "Welcome! What time do you start?", "Chào mừng! Bạn bắt đầu lúc mấy giờ?", "time"),
      ok("study", "Sí, y también estudio en la universidad.", "Yes, and I also study at the university.", "Ừ, và mình cũng đang học đại học.", "¡Qué bien! ¿A qué hora empiezas?", "Nice! What time do you start?", "Hay quá! Bạn bắt đầu lúc mấy giờ?", "time"),
      bad("dog", "Tengo un perro.", "I have a dog.", "Mình có một con chó.", "Sí, soy el nuevo diseñador.", "¡Qué lindo! Pero, ¿trabajas aquí?", "Cute! But do you work here?", "Dễ thương ghê! Nhưng bạn làm ở đây à?", "time")),
    node("time", "¿A qué hora empiezas y terminas?", "What time do you start and finish?", "Bạn bắt đầu và kết thúc lúc mấy giờ?", "“Empiezo a las…, termino a las…”.", "“Empiezo a las…, termino a las…”.",
      ok("nine", "Empiezo a las nueve y termino a las cinco.", "I start at nine and finish at five.", "Mình bắt đầu lúc chín giờ, xong lúc năm giờ.", "Igual que yo. ¿Tienes un minuto ahora?", "Same as me. Do you have a minute now?", "Giống mình. Giờ bạn rảnh một phút không?", "minute"),
      ok("home", "Los viernes trabajo desde casa.", "On Fridays I work from home.", "Thứ Sáu mình làm ở nhà.", "¡Qué suerte! ¿Tienes un minuto ahora?", "Lucky! Do you have a minute now?", "Sướng thế! Giờ bạn rảnh một phút không?", "minute"),
      bad("meeting", "Nos vemos mañana.", "See you tomorrow.", "Mai gặp nhé.", "Empiezo a las nueve y termino a las cinco.", "¡Pero si acabamos de conocernos! ¿A qué hora empiezas?", "But we just met! What time do you start?", "Mình vừa mới gặp mà! Bạn bắt đầu lúc mấy giờ?", "minute")),
    node("minute", "¿Tienes un minuto para un café?", "Do you have a minute for a coffee?", "Bạn có rảnh uống cà phê không?", "Accept, or say you're busy.", "Đồng ý, hoặc nói bạn đang bận.",
      ok("yes", "¡Claro! Vamos.", "Sure! Let's go.", "Được chứ! Đi thôi.", "Genial. Te enseño la cafetería.", "Great. I'll show you the café.", "Tuyệt. Mình dẫn bạn đi quán cà phê."),
      ok("busy", "Ahora estoy ocupado, tengo una reunión.", "I'm busy now, I have a meeting.", "Giờ mình bận, mình có họp.", "No pasa nada. ¡Nos vemos luego!", "No problem. See you later!", "Không sao. Gặp sau nhé!"),
      bad("job", "Busco trabajo.", "I'm looking for a job.", "Mình đang tìm việc.", "¡Claro! Vamos.", "¡Pero ya trabajas aquí! ¿Vamos por café?", "But you already work here! Coffee?", "Nhưng bạn làm ở đây rồi mà! Đi cà phê không?"))])])

# 9 ─────────────────────────────────────────
pack(9, "B1", T("Intermediate 1: Travel problems", "Trung cấp 1: Sự cố khi du lịch"),
     T("Solve problems at the hotel and on the road.", "Xử lý sự cố ở khách sạn và trên đường."),
 [lesson("hotel", T("At the hotel", "Ở khách sạn"), T("Ask for what you need at reception.", "Yêu cầu những gì bạn cần ở quầy lễ tân."), "key", [
    ("Tengo una reserva a nombre de Lee.", "I have a reservation under Lee.", "Tôi đã đặt phòng tên Lee."),
    ("El aire acondicionado no funciona.", "The air conditioning doesn't work.", "Máy lạnh không hoạt động."),
    ("¿A qué hora es el desayuno?", "What time is breakfast?", "Bữa sáng lúc mấy giờ?"), ("Necesito otra toalla.", "I need another towel.", "Tôi cần thêm một cái khăn."),
    ("¿Puedo dejar mi equipaje aquí?", "Can I leave my luggage here?", "Tôi gửi hành lý ở đây được không?"), ("Quiero cambiar de habitación.", "I'd like to change rooms.", "Tôi muốn đổi phòng.")]),
  lesson("problems", T("When things go wrong", "Khi gặp sự cố"), T("Explain a problem calmly and clearly.", "Trình bày sự cố bình tĩnh và rõ ràng."), "alert-circle", [
    ("Perdí mi pasaporte.", "I lost my passport.", "Tôi bị mất hộ chiếu."), ("Mi vuelo está retrasado.", "My flight is delayed.", "Chuyến bay của tôi bị hoãn."),
    ("Me robaron la cartera.", "My wallet was stolen.", "Tôi bị trộm ví."), ("Tomé el autobús equivocado.", "I took the wrong bus.", "Tôi đi nhầm xe buýt."),
    ("¿Me puede ayudar, por favor?", "Can you help me, please?", "Bạn giúp tôi được không?"), ("Necesito hablar con el gerente.", "I need to speak to the manager.", "Tôi cần nói chuyện với quản lý.")])],
 [convo("hotel-fix", T("Fix a hotel problem", "Xử lý sự cố khách sạn"), T("Report a broken air conditioner and get a new room.", "Báo máy lạnh hỏng và được đổi phòng."), "map-pin", [
    node("problem", "Recepción, buenas noches. ¿En qué le ayudo?", "Reception, good evening. How can I help?", "Lễ tân xin nghe, chào buổi tối. Tôi giúp gì được ạ?", "Describe the problem with “no funciona”.", "Mô tả sự cố bằng “no funciona”.",
      ok("ac", "El aire acondicionado no funciona.", "The air conditioning doesn't work.", "Máy lạnh không hoạt động.", "Lo siento mucho. ¿Cuál es su habitación?", "I'm very sorry. What's your room?", "Thành thật xin lỗi. Bạn ở phòng nào?", "room"),
      ok("help", "¿Me puede ayudar? Hace mucho calor en mi habitación.", "Can you help me? It's very hot in my room.", "Giúp tôi được không? Phòng tôi nóng quá.", "Claro. ¿Cuál es su habitación?", "Of course. What's your room?", "Tất nhiên. Bạn ở phòng nào?", "room"),
      bad("breakfast", "¿A qué hora es el desayuno?", "What time is breakfast?", "Bữa sáng lúc mấy giờ?", "El aire acondicionado no funciona.", "A las siete. ¿Hay algún otro problema?", "At seven. Is there any other problem?", "Lúc bảy giờ. Còn vấn đề gì khác không?", "room")),
    node("room", "¿Cuál es su número de habitación?", "What's your room number?", "Số phòng của bạn là bao nhiêu?", "Say “Es la…” plus the number.", "Nói “Es la…” kèm số phòng.",
      ok("num", "Es la doscientos cinco.", "It's 205.", "Phòng 205.", "Gracias. Mando a alguien ahora.", "Thanks. I'll send someone now.", "Cảm ơn. Tôi cho người lên ngay.", "change"),
      ok("change", "La doscientos cinco. ¿Puedo cambiar de habitación?", "205. Can I change rooms?", "Phòng 205. Tôi đổi phòng được không?", "Déjeme revisar…", "Let me check…", "Để tôi kiểm tra…", "change"),
      bad("passport", "Perdí mi pasaporte.", "I lost my passport.", "Tôi mất hộ chiếu.", "Es la doscientos cinco.", "¡Ay! Lo buscamos luego. ¿Su habitación?", "Oh! We'll look later. Your room?", "Ôi! Lát mình tìm sau. Phòng của bạn?", "change")),
    node("change", "Tenemos otra habitación libre en el tercer piso.", "We have another free room on the third floor.", "Chúng tôi còn một phòng trống ở tầng ba.", "Accept politely.", "Đồng ý một cách lịch sự.",
      ok("perfect", "Perfecto, muchas gracias por su ayuda.", "Perfect, thank you for your help.", "Tuyệt, cảm ơn bạn đã giúp.", "Con gusto. Aquí tiene la nueva llave.", "My pleasure. Here's the new key.", "Rất sẵn lòng. Chìa khóa mới đây ạ."),
      ok("luggage", "Genial. ¿Me ayudan con el equipaje?", "Great. Can you help with my luggage?", "Tuyệt. Có ai giúp tôi mang hành lý không?", "Claro, el botones sube ahora.", "Sure, the bellhop is coming up.", "Vâng, nhân viên hành lý lên ngay."),
      bad("manager", "Necesito hablar con el gerente.", "I need to speak to the manager.", "Tôi cần gặp quản lý.", "Perfecto, muchas gracias por su ayuda.", "Ya está resuelto, pero si quiere, lo llamo.", "It's solved already, but I can call him if you want.", "Đã giải quyết rồi, nhưng nếu muốn tôi sẽ gọi quản lý."))])])

# 10 ────────────────────────────────────────
pack(10, "B1", T("Intermediate 2: Past & opinions", "Trung cấp 2: Quá khứ & ý kiến"),
     T("Tell what you did and share what you think.", "Kể bạn đã làm gì và chia sẻ suy nghĩ."),
 [lesson("past", T("Talking about the past", "Nói về quá khứ"), T("Simple past for weekend stories.", "Thì quá khứ đơn để kể chuyện cuối tuần."), "rewind", [
    ("Ayer fui al mercado.", "Yesterday I went to the market.", "Hôm qua tôi đi chợ."), ("Comí tacos con mis amigos.", "I ate tacos with my friends.", "Tôi ăn tacos với bạn bè."),
    ("Fue muy divertido.", "It was a lot of fun.", "Rất vui."), ("Vi una película.", "I watched a movie.", "Tôi đã xem một bộ phim."),
    ("Viví en México dos años.", "I lived in Mexico for two years.", "Tôi đã sống ở Mexico hai năm."), ("No hice nada.", "I didn't do anything.", "Tôi không làm gì cả.")]),
  lesson("opinions", T("Giving opinions", "Nêu ý kiến"), T("Agree, disagree, and say what you like.", "Đồng ý, phản đối và nói điều bạn thích."), "message-square", [
    ("Creo que sí.", "I think so.", "Tôi nghĩ là có."), ("No estoy de acuerdo.", "I don't agree.", "Tôi không đồng ý."),
    ("Me encanta.", "I love it.", "Tôi rất thích."), ("No me gusta mucho.", "I don't like it much.", "Tôi không thích lắm."),
    ("En mi opinión, es caro.", "In my opinion, it's expensive.", "Theo tôi thì nó đắt."), ("Tienes razón.", "You're right.", "Bạn nói đúng.")])],
 [convo("weekend", T("Weekend recap", "Kể chuyện cuối tuần"), T("Share what you did and what you thought.", "Kể bạn đã làm gì và cảm nhận thế nào."), "compass", [
    node("did", "¿Qué hiciste el fin de semana?", "What did you do on the weekend?", "Cuối tuần bạn làm gì?", "Use the past: “fui”, “comí”, “vi”.", "Dùng thì quá khứ: “fui”, “comí”, “vi”.",
      ok("market", "Fui al mercado y comí tacos.", "I went to the market and ate tacos.", "Mình đi chợ và ăn tacos.", "¡Qué rico! ¿Te gustaron?", "Yum! Did you like them?", "Ngon thế! Bạn có thích không?", "opinion"),
      ok("movie", "Vi una película nueva.", "I watched a new movie.", "Mình xem một bộ phim mới.", "¿Ah, sí? ¿Te gustó?", "Oh yeah? Did you like it?", "Thế à? Bạn có thích không?", "opinion"),
      bad("present", "Voy al mercado.", "I'm going to the market.", "Mình đang đi chợ.", "Fui al mercado y comí tacos.", "¿Ahora? Te pregunto por el fin de semana pasado.", "Now? I'm asking about last weekend.", "Bây giờ á? Mình hỏi cuối tuần trước mà.", "opinion")),
    node("opinion", "¿Y qué te pareció?", "And what did you think?", "Bạn thấy thế nào?", "Give an opinion: “Me encantó…”, “No me gustó…”.", "Nêu ý kiến: “Me encantó…”, “No me gustó…”.",
      ok("loved", "Me encantó. Fue muy divertido.", "I loved it. It was a lot of fun.", "Mình rất thích. Vui lắm.", "¡Qué bueno! Yo quiero ir también.", "Great! I want to go too.", "Hay quá! Mình cũng muốn đi.", "plan"),
      ok("notmuch", "No me gustó mucho, en mi opinión fue caro.", "I didn't like it much; I think it was expensive.", "Mình không thích lắm, theo mình thì đắt.", "Entiendo. A veces es caro.", "I get it. Sometimes it's expensive.", "Mình hiểu. Đôi khi nó đắt thật.", "plan"),
      bad("agree", "Tienes razón.", "You're right.", "Bạn nói đúng.", "Me encantó. Fue muy divertido.", "¿Razón de qué? Cuéntame, ¿te gustó?", "Right about what? Tell me, did you like it?", "Đúng về chuyện gì? Kể đi, bạn có thích không?", "plan")),
    node("plan", "¿Vamos juntos el próximo sábado?", "Shall we go together next Saturday?", "Thứ Bảy tới mình đi cùng nhé?", "Agree or suggest something else.", "Đồng ý hoặc đề xuất việc khác.",
      ok("yes", "¡Claro! Creo que va a ser genial.", "Sure! I think it'll be great.", "Được chứ! Mình nghĩ sẽ rất vui.", "¡Perfecto! Nos vemos el sábado.", "Perfect! See you Saturday.", "Tuyệt! Hẹn thứ Bảy nhé."),
      ok("other", "No estoy seguro. ¿Y si vamos al cine?", "I'm not sure. What if we go to the movies?", "Mình chưa chắc. Hay mình đi xem phim?", "¡Buena idea! El cine entonces.", "Good idea! The movies then.", "Ý hay! Vậy đi xem phim.", None),
      bad("nothing", "No hice nada.", "I didn't do anything.", "Mình chẳng làm gì cả.", "¡Claro! Creo que va a ser genial.", "Jaja, eso fue el pasado. ¿Vamos el sábado?", "Haha, that was the past. Shall we go Saturday?", "Haha, đó là chuyện cũ rồi. Thứ Bảy đi nhé?"))])])

# Grammar/usage focus for the first ten levels' lessons.
FOCUS = {
 ("level-01","everyday-words"): T("“Por favor” and “gracias” go at the end of a request: “Agua, por favor.”", "“Por favor” và “gracias” thường đặt cuối câu: “Agua, por favor.”"),
 ("level-01","feelings"): T("Use “estar” for how you feel now (estoy bien) and “tener” for hunger, thirst, and cold (tengo hambre).", "Dùng “estar” cho cảm giác lúc này (estoy bien) và “tener” cho đói, khát, lạnh (tengo hambre)."),
 ("level-02","days"): T("Days are lowercase. “El lunes” means “on Monday”; “los lunes” means “every Monday”.", "Tên thứ viết thường. “El lunes” là “vào thứ Hai”; “los lunes” là “mỗi thứ Hai”."),
 ("level-02","time"): T("One o'clock is singular (es la una); every other hour is plural (son las dos, son las tres).", "Một giờ dùng số ít (es la una); các giờ khác dùng số nhiều (son las dos, son las tres)."),
 ("level-03","food"): T("Every noun has a gender: el pan, el pollo (masculine); la fruta, la sopa (feminine).", "Mỗi danh từ có giống: el pan, el pollo (giống đực); la fruta, la sopa (giống cái)."),
 ("level-03","ordering"): T("“Quiero…” is fine; “Quisiera…” or “Me da…” sounds more polite.", "“Quiero…” dùng được; “Quisiera…” hoặc “Me da…” nghe lịch sự hơn."),
 ("level-04","clothes"): T("Adjectives come after the noun and match it: la camisa roja, los zapatos negros.", "Tính từ đứng sau danh từ và hợp giống, số: la camisa roja, los zapatos negros."),
 ("level-04","paying"): T("“¿Cuánto es?” for a total, “¿Cuánto cuesta / cuestan?” for one item or several.", "“¿Cuánto es?” để hỏi tổng tiền, “¿Cuánto cuesta / cuestan?” cho một hay nhiều món."),
 ("level-05","places"): T("Use “estar” for location: “¿Dónde está el banco?” and “hay” for “there is”: “¿Hay un banco cerca?”", "Dùng “estar” cho vị trí: “¿Dónde está el banco?”, và “hay” nghĩa là “có”: “¿Hay un banco cerca?”"),
 ("level-05","directions"): T("Directions use polite commands: siga (keep going), gire (turn), cruce (cross).", "Chỉ đường dùng câu mệnh lệnh lịch sự: siga (cứ đi), gire (rẽ), cruce (băng qua)."),
 ("level-06","family"): T("Possessives agree in number: mi hermano, mis hermanos.", "Tính từ sở hữu hợp số: mi hermano, mis hermanos."),
 ("level-06","home"): T("“Vivo en…” for where you live; “tengo” for what you have.", "“Vivo en…” để nói nơi bạn sống; “tengo” cho thứ bạn có."),
 ("level-07","pain"): T("“Doler” works like “gustar”: me duele la cabeza, me duelen los pies.", "“Doler” dùng giống “gustar”: me duele la cabeza, me duelen los pies."),
 ("level-07","help"): T("In emergencies, short commands work best: ¡Ayuda! ¡Llame a…!", "Khi khẩn cấp, câu mệnh lệnh ngắn hiệu quả nhất: ¡Ayuda! ¡Llame a…!"),
 ("level-08","jobs"): T("Present tense endings: trabajo, estudio, vivo (I); trabajas, estudias, vives (you).", "Đuôi động từ thì hiện tại: trabajo, estudio, vivo (tôi); trabajas, estudias, vives (bạn)."),
 ("level-08","schedule"): T("Some verbs change their stem: empezar → empiezo, poder → puedo.", "Một số động từ đổi gốc: empezar → empiezo, poder → puedo."),
 ("level-09","hotel"): T("“No funciona” is the go-to phrase for anything broken.", "“No funciona” là câu dùng cho mọi thứ bị hỏng."),
 ("level-09","problems"): T("The preterite tells what happened once: perdí, tomé, me robaron.", "Thì quá khứ đơn (pretérito) kể việc đã xảy ra: perdí, tomé, me robaron."),
 ("level-10","past"): T("Common irregular pasts: fui (I went / I was), hice (I did), vi (I saw).", "Quá khứ bất quy tắc hay gặp: fui (tôi đã đi / đã là), hice (tôi đã làm), vi (tôi đã thấy)."),
 ("level-10","opinions"): T("Soften opinions with “creo que…”, “me parece que…”, “en mi opinión…”.", "Làm mềm ý kiến bằng “creo que…”, “me parece que…”, “en mi opinión…”."),
}
for _p in packs:
    for _l in _p["lessons"]:
        f = FOCUS.get((_p["id"], _l["id"]))
        if f and "focus" not in _l:
            _l["focus"] = f

# Later levels live in batch files passed after the output folder.
for batch in sys.argv[2:]:
    exec(open(batch, encoding="utf8").read())

# Levels 1–10 gained a lesson focus after release, so they ship as version 2.
for _p in packs:
    if _p["level"] <= 10:
        _p["version"] = 2

os.makedirs(OUT, exist_ok=True)
for p in packs:
    with open(os.path.join(OUT, f"{p['id']}.json"), "w", encoding="utf8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2); f.write("\n")
print(len(packs), "packs")
