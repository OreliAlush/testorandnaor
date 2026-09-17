(() => {
  const form = document.querySelector("#assistant-form");
  if (!form) return;

  const messages = document.querySelector("#assistant-messages");
  const input = document.querySelector("#assistant-input");
  const send = document.querySelector("#assistant-send");
  const upload = document.querySelector(".assistant-upload");
  const photos = document.querySelector("#assistant-photos");
  const skipPhoto = document.querySelector("#assistant-skip-photo");
  const data = {};
  const questions = [
    ["project", "היי, אני OrPro Assist 👋 ספרו לי במילים שלכם: מה תרצו לעשות בבית?", "למשל: אני רוצה פרגולה בחצר, יש נזילה במטבח..."],
    ["location", "מעולה. באיזו עיר או אזור נמצא הפרויקט?", "עיר או אזור"],
    ["measurements", "יש לכם מידות משוערות? אפשר לכתוב למשל: 4 על 3, גובה 2.5. אם אין — כתבו 'אין לי'.", "כתבו מידות משוערות או 'אין לי'"],
    ["photos", "מצוין. עכשיו אפשר לצרף תמונות של השטח. הן יעזרו לבעל העסק להבין את העבודה.", ""],
    ["name", "איך קוראים לכם?", "שם מלא"],
    ["phone", "מה מספר הטלפון לחזרה?", "050-1234567"],
    ["email", "ולסיום, אימייל לקבלת ההצעות? אפשר לכתוב 'דלג'.", "name@example.com"],
  ];
  let step = 0;

  const addMessage = (text, type) => {
    const bubble = document.createElement("div");
    bubble.className = `assistant-bubble ${type}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
  };
  const ask = () => {
    const [, question, placeholder] = questions[step];
    addMessage(question, "bot");
    input.placeholder = placeholder;
    const photoStep = questions[step][0] === "photos";
    upload.hidden = !photoStep;
    input.hidden = photoStep;
    send.hidden = photoStep;
    if (photoStep) {
      photos.focus();
    } else {
      input.focus();
    }
  };
  const parseMeasurements = (value) => {
    const values = value.replace(/,/g, ".").match(/\d+(?:\.\d+)?/g) || [];
    data.width = values[0] || "";
    data.length = values[1] || "";
    data.height = values[2] || "";
  };
  const categorySlug = (value) => {
    const text = value.toLowerCase();
    if (/פרגול|דק|הצלל/.test(text)) return "pergolas";
    if (/מטבח|ארון|נגר/.test(text)) return "kitchens";
    if (/נזיל|צנר|ברז|סתימ|ביוב|אינסטל/.test(text)) return "plumbing";
    if (/חשמל|שקע|תאור|לוח/.test(text)) return "electricity";
    return "renovations";
  };
  const finish = () => {
    form.service_type.value = data.project;
    form.description.value = data.project;
    form.city.value = data.location;
    form.address.value = data.location;
    form.estimated_width.value = data.width;
    form.estimated_length.value = data.length;
    form.estimated_height.value = data.height;
    form.name.value = data.name;
    form.phone.value = data.phone;
    form.email.value = data.email === "דלג" ? "" : data.email;
    form.action = `/שירותים/${categorySlug(data.project)}/`;
    addMessage("תודה! אני שולח עכשיו את הפרטים לבעלי העסק המתאימים.", "bot");
    setTimeout(() => form.submit(), 700);
  };
  const answer = () => {
    const value = input.value.trim();
    if (!value) return;
    if (questions[step][0] === "phone" && value.replace(/\D/g, "").length < 8) {
      addMessage("נראה שחסר חלק מהמספר. אפשר לכתוב שוב טלפון מלא?", "bot");
      return;
    }
    data[questions[step][0]] = value;
    if (questions[step][0] === "measurements") parseMeasurements(value);
    addMessage(value, "customer");
    input.value = "";
    step += 1;
    if (step < questions.length) ask(); else finish();
  };
  send.addEventListener("click", answer);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") { event.preventDefault(); answer(); }
  });
  photos.addEventListener("change", () => {
    const count = photos.files.length;
    data.photos = count;
    addMessage(count ? `צירפתי ${count} תמונות` : "אין לי תמונות כרגע", "customer");
    step += 1;
    ask();
  });
  skipPhoto.addEventListener("click", () => {
    addMessage("אין לי תמונות כרגע", "customer");
    step += 1;
    ask();
  });
  ask();
})();
